import requests
import json
from util import CONFIG, APP


def notifyByEmail(config, data):
    prefix = 'error_' if 'error' in data else ''
    subject = config[prefix + 'subject'].format(**data)
    body = config[prefix + 'body'].format(**data)
    APP.D(f'邮件 数据===> {subject} ; {body}')
    #p('邮件===>', subject, '; ', body)
    if not CONFIG['dry']:
        res = APP.send_email(subject, body)
        if res:
            APP.E(f'邮件推送失败：{res}')
            #p('邮件推送失败：', res, force=True)
        else:
            APP.D('邮件发送成功。')
            #p('邮件发送成功。')


def notifyByDingTail(config, data):
    """发消息给钉钉机器人
    """
    token = config['token']
    if not token:
        APP.E('APP.E: 没有钉钉token')
        #p('APP.E: 没有钉钉token')
        return
    prefix = 'error_' if 'error' in data else ''
    data = {
        "msgtype": "text",
        "text": {
            "content": config['keyword'] + config[prefix + 'message'].format(**data)
        },
        "at": config['at']
    }
    APP.D(f'钉钉机器人 数据===> {data}')
    #p('钉钉机器人===>', data)
    if not CONFIG['dry']:
        res = requests.post(url="https://oapi.dingtalk.com/robot/send?access_token={}".format(token), \
            headers = {'Content-Type': 'application/json'}, data=json.dumps(data))
        #p('钉钉推送结果：', res.json())
        APP.D(f'钉钉推送结果：{res.json()}')


def notifyByServerChan(config, data):
    prefix = 'error_' if 'error' in data else ''
    url = 'https://sc.ftqq.com/{sckey}.send'.format(**config)
    title = config[prefix + 'title'].format(**data)
    message = config[prefix + 'message'].format(**data)
    APP.D(f'Server酱 数据===> {title} ; {message}')
    #p('Server酱===>', title, '; ', message)
    if not CONFIG['dry']:
        res = requests.get(url, params={'text': title, 'desp': message})
        #p('Server酱推送结果：', res.json())
        APP.D(f'Server酱推送结果：{res.json()}')


def notify(data):
    notifyConfig = CONFIG['notify']
    if 'mail' in notifyConfig:
        notifyByEmail(CONFIG['mail'], data)
    if 'dingtalk' in notifyConfig:
        notifyByDingTail(CONFIG['dingtalk'], data)
    if 'ServerChan' in notifyConfig:
        notifyByServerChan(CONFIG['ServerChan'], data)
