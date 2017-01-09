#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ = '懒懒的天空'

import requests
import sys
import json
from conf.INIFILES import read_config, write_config
import os
import datetime
from conf.BLog import Log
reload(sys)
sys.setdefaultencoding('utf-8')


class WeiXin(object):
    def __init__(self, corpid, corpsecret): # 初始化的时候需要获取corpid和corpsecret，需要从管理后台获取
        self.__params = {
            'corpid': corpid,
            'corpsecret': corpsecret
        }

        self.url_get_token = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        self.url_send = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?'

        self.__token = self.__get_token()
        self.__token_params = {
            'access_token': self.__token
        }

    def __raise_error(self, res):
        raise Exception('error code: %s,error message: %s' % (res.json()['errcode'], res.json()['errmsg']))
        global senderr
        sendstatus = False
        senderr = 'error code: %s,error message: %s' % (res.json()['errcode'], res.json()['errmsg'])

    def __get_token(self):
        # print self.url_get_token
        headers = {'content-type': 'application/json'}
        res = requests.get(self.url_get_token, headers=headers,  params=self.__params)

        try:
            return res.json()['access_token']
        except:
            self.__raise_error(res.content)


    def send_message(self,  agentid, messages, userid='', toparty=''):
        payload = {
            'touser': userid,
            'toparty': toparty,
            'agentid': agentid,
            "msgtype": "news",
            "news": messages
        }
        headers = {'content-type': 'application/json'}
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        params = self.__token_params
        res = requests.post(self.url_send, headers=headers, params=params, data=data)
        try:
            return res.json()
        except:
            self.__raise_error(res)


def main(send_to, subject, content):
    try:
        global sendstatus
        global senderr
        data = ''
        messages = {}
        body = {}
        config_file_path = get_path()
        CorpID = read_config(config_file_path, 'wei', "CorpID")
        CorpSecret = read_config(config_file_path, 'wei', "CorpSecret")
        agentid = read_config(config_file_path, 'wei', "agentid")
        web = read_config(config_file_path, 'wei', "web")
        content = json.loads(content)
        messages["message_url"] = web
        body["url"] = web + "history.php?action=showgraph&itemids[]=" + content[u'监控ID']
        warn_message = ''
        if content[u'当前状态'] == 'PROBLEM':
            body["title"] = "服务器故障"
            warn_message += subject + '\n'
            warn_message += '详情：\n'
            warn_message += '告警等级：'+ content[u'告警等级'] + '\n'
            warn_message += '告警时间：'+ content[u'告警时间'] + '\n'
            warn_message += '告警地址：'+ content[u'告警地址'] + '\n'
            warn_message += '持续时间：'+ content[u'持续时间'] + '\n'
            warn_message += '监控项目：'+ content[u'监控项目'] + '\n'
            warn_message += content[u'告警主机'] + '故障(' + content[u'事件ID']+ ')'
        else:
            body["title"] = "服务器恢复"
            warn_message += subject + '\n'
            warn_message += '详情：\n'
            warn_message += '告警等级：'+ content[u'告警等级'] + '\n'
            warn_message += '恢复时间：'+ content[u'恢复时间'] + '\n'
            warn_message += '告警地址：'+ content[u'告警地址'] + '\n'
            warn_message += '持续时间：'+ content[u'持续时间'] + '\n'
            warn_message += '监控项目：'+ content[u'监控项目'] + '\n'
            warn_message += content[u'告警主机'] + '恢复(' + content[u'事件ID']+ ')'
        body['description'] = warn_message
        data = []
        data.append(body)
        messages['articles'] = data
        wx = WeiXin(CorpID, CorpSecret)
        data = wx.send_message(toparty=send_to, agentid=agentid, messages=messages)
        sendstatus = True
    except Exception, e:
        senderr = str(e)
        sendstatus = False
    logwrite(sendstatus, data)


def get_path():
    path = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = path + '/config.ini'
    return config_path


def logwrite(sendstatus, content):
    logpath = '/var/log/zabbix/weixin'
    if not sendstatus:
        content = senderr
    t = datetime.datetime.now()
    daytime = t.strftime('%Y-%m-%d')
    daylogfile = logpath+'/'+str(daytime)+'.log'
    logger = Log(daylogfile, level="info", is_console=False, mbs=5, count=5)
    os.system('chown zabbix.zabbix {0}'.format(daylogfile))
    logger.info(content)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        send_to = sys.argv[1]
        subject = sys.argv[2]
        content = sys.argv[3]
        logwrite(True, content)
        main(send_to, subject, content)

