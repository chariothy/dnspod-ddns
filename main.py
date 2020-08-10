import json,urllib.request
from urllib.parse import urlencode
import base64, hmac
import requests
import time, socket
import os, json
import subprocess, re

from chariothy_common import AppTool

APP_NAME = 'dnspod'
APP = AppTool(APP_NAME, os.getcwd())
CONFIG = APP.config

IP_ADDR = {
    6: ':::',
    4: '...'
}
IP_FILE = '/tmp/ipv{}'
UID = CONFIG['dnspod']['id']
UTOKEN = CONFIG['dnspod']['token']
DTOKEN = CONFIG['dingtalk']['token']
URL = 'https://dnsapi.cn/'
DOMAIN_RECORD = {}


def requestDnsApi(method, data={}):
    """调用dnspod的API

    Args:
        method ([type]): [description]
        data (dict, optional): [description]. Defaults to {}.
    """
    auth = {
        'login_token': f'{UID},{UTOKEN}', 
        'format': 'json'
    }
    res = requests.post(url=URL + method, data=dict(auth, **data))
    p(res.json())
    return res.json()


def p(*values):
    """非debug时打印结果
    """
    if CONFIG['debug']:
        print('\n===>', values)


def requestDingTalk(msg):
    """发消息给钉钉机器人
    """
    data = {
        "msgtype": "text",
        "text": {
            "content": "DDNS" + msg
        },
        "at": CONFIG['dingtalk']['at']
    }
    res = requests.post(url="https://oapi.dingtalk.com/robot/send?access_token={}".format(DTOKEN), \
        headers = {'Content-Type': 'application/json'}, data=json.dumps(data))
    p(res.json())


def parseIp(ipPair, version):
    """解析本地网卡中的IP信息

    Args:
        ipPair (str): IP信息文本
        version (int): 4,6

    Returns:
        tuple: (ip, preferred_lft)
    """
    ip = ipPair[0]
    tlft = ipPair[1]
    if version == 4:
        ipMatch = re.findall(r'inet ([0-9\.]+)/', ip)
    elif version == 6:
        ipMatch = re.findall(r'inet6 ([0-9a-f:]+)/', ip)
    print(ipMatch)
    tlftMatch = re.findall(r'valid_lft (\d+)sec preferred_lft (\d+)sec', tlft)
    print(tlftMatch)
    return (ipMatch[0], tlftMatch[0][1])


def saveIP(ip, version):
    """保存新IP

    Args:
        ip (str): 新IP
        version (int): 4,6
    """
    ipFilePath = IP_FILE.format(version)
    with open(ipFilePath, mode='w') as fd:
        fd.write(ip)


def getOldIP(version):
    """获取上次IP

    Args:
        version (int): 4,6

    Returns:
        str: 上次IP
    """
    ipFilePath = IP_FILE.format(version)
    if os.path.exists(ipFilePath):
        with open(ipFilePath, mode='r') as fd:
            ip = fd.readline(1)
            return ip
    else:
        return ''


def getIP(version):
    """获取本机IP地址
    """
    if version == 4:
        command = 'ip -4 addr show scope global {} up | ' \
        'grep -v " deprecated" | ' \
        'grep -v " 0sec" | ' \
        'grep -A1 "inet [1-9]"'.format(CONFIG['interface'])
    elif version == 6:
        command = 'ip -6 addr show scope global {} up | ' \
            'grep -v " deprecated" | ' \
            'grep -v " 0sec" | ' \
            'grep -A1 "inet6 [^f:]"'.format(CONFIG['interface'])
    p(command)
    ipStr = subprocess.check_output(command, shell=True).decode('utf-8')
    p(ipStr)

    ipParts = [x.strip() for x in ipStr.split('\n')]
    p(ipParts)
    ipPairList = list(zip(ipParts[::2], ipParts[1::2]))
    #p(dict(ipPairDict))

    if len(ipPairList) == 1:
        ips = parseIp(ipPairList[0], version)
        return ips[0]
    elif len(ipParts) > 1:
        ipList = []
        for ipPair in ipPairList:
            ips = parseIp(ipPair, version)
            ipList.append(ips)
        ipList.sort(key=lambda ip: ip[-1], reverse=True)
        p(ipList)
        return ipList[0][0]
    else:
        raise RuntimeError(f'没法找到IPv{version}地址')


def getDomains():
    """从dnspod获取domain信息
    """
    if not DOMAIN_RECORD:
        domains = requestDnsApi('Domain.List')
        for domain in domains['domains']:
            name = domain['name']
            if name not in DOMAIN_RECORD:
                DOMAIN_RECORD[domain['id']] = {
                    'name': domain['name'],
                    'records': {}
                }


def getRecords(domainId):
    """从dnspod获取record信息

    Args:
        domainId (str): Domain ID
    """
    getDomains()
    domain = DOMAIN_RECORD[domainId]
    if not domain['records']:
        records = requestDnsApi('Record.List', {'domain_id': domainId})
        for record in records['records']:
            key = '{}.{}:{}'.format(record['name'], domain['name'], record['type'])
            domain['records'][key] = {
                'id': record['id'],
                'name': record['name'],
                'value': record['value'],
                'type': record['type'],
            }
    
    
def refreshRecord(subDomainName, newIP, version):
    """更新记录IP，或添加新记录

    Args:
        subDomainName (str): 记录名（包含域名）
        newIP (str): IP
        version (int): 4,6

    Raises:
        RuntimeError: 错误
    """
    getDomains()
    recordType = 'AAAA' if version == 6 else 'A'
    for domainId in DOMAIN_RECORD.keys():
        domain = DOMAIN_RECORD[domainId]
        if domain['name'] in subDomainName:
            getRecords(domainId)
            key = f'{subDomainName}:{recordType}'
            if key in domain['records']:
                record = domain['records'][key]
                if record['value'] == newIP:
                    p(f'IPv{version}地址与线上一致：{newIP}')
                    continue
                data = {
                    'domain_id': domainId,
                    'record_id': record['id'],
                    'sub_domain': record['name'],
                    'value': newIP,
                    'record_type': record['type'],
                    'record_line': '默认'
                }
                action = 'Record.Modify'
                actionReport = '更新'
            else:
                data = {
                    'domain_id': domainId,
                    'sub_domain': '@' if subDomainName == domain['name'] else subDomainName.replace('.'+domain['name'], ''),
                    'value': newIP,
                    'record_type': recordType,
                    'record_line': '默认'
                }
                action = 'Record.Create'
                actionReport = '创建'
            p(data)
            result = requestDnsApi(action, data)
            p(result)
            status = result['status']
            if status['code'] != '1':
                raise RuntimeError('{}-{}'.format(status['code'], status['message']))
            else:
                requestDingTalk('成功{}{}，IP为{}'.format(actionReport, subDomainName, newIP))


def run(version):
    assert(version == 4 or version == 6)
    try:
        global IP_ADDR
        IP_ADDR[version] = getIP(version)
        oldIp = getOldIP(version)
        p('本地IPv{}：{}'.format(version, IP_ADDR[version]))
        if IP_ADDR[version] != oldIp:
            p('已更新，上次IPv{}为{}'.format(version, oldIp))
            saveIP(IP_ADDR[version], version)
            for subDomain in CONFIG[f'ipv{version}']:
                refreshRecord(subDomain, IP_ADDR[version], version)
        else:
            p('未更新')
    except RuntimeError as ex:
        p(ex)
        requestDingTalk('更新失败：' + ex)


if __name__ == "__main__":
    run(6)
    run(4)