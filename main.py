import json,urllib.request
from urllib.parse import urlencode
import base64, hmac
import requests
import time, socket
import os, json
import subprocess, re, sys
import shutil, stat, traceback

from ip import Ip
from chariothy_common import AppTool


def show_diff(src_path, dst_path):
    import difflib
    with open(src_path, mode='r') as fd:
        src_text = fd.readlines()
    
    with open(dst_path, mode='r') as fd:
        dst_text = fd.readlines()

    diff_list = list(difflib.Differ().compare(src_text, dst_text))
    for diff in diff_list:
        if diff == "\n":
            print ("\n")
        print(diff, end='', sep='')
    print()


def checkConfig():
    localConfig = './config/config_local.py'
    sampleConfig = localConfig.replace('_local', '_sample')        
    from config import CONFIG

    sys.path.append(os.path.join(os.getcwd(), 'config'))
    if not os.path.exists(sampleConfig):
        configVersion = ''
    else:
        from config_sample import CONFIG as CONFIG_SAMPLE
        configVersion = CONFIG_SAMPLE.get('version', 'NONE')
    
    if CONFIG['version'] != configVersion:
        if configVersion:
            print('#'* 20 + ' ↓ config_sample.py有版本更新，请注意其中的配置项差异 ({} <-> {}) ↓ '.format(configVersion, CONFIG['version']) + '#' * 20)
            show_diff(sampleConfig, './config.py')
            shutil.move(sampleConfig, sampleConfig.replace('_sample', f'_sample.v{configVersion}'))
            print('#'* 20 + ' ↑ config_sample.py有版本更新，请注意其中的配置项差异 ({} <-> {}) ↑ '.format(configVersion, CONFIG['version']) + '#' * 20)
        shutil.copyfile('./config.py', sampleConfig)
        os.chmod(sampleConfig, 0o777)

    if not os.path.exists(localConfig):
        print('\n未发现config_local.py文件，开始生成默认配置文件 ......')
        shutil.copyfile('./config.py', localConfig)
        os.chmod(localConfig, 0o777)
        print('\n默认config_local.py文件已经生成，请根据实际情况修改配置，并重新运行。')
        os.sys.exit()

checkConfig()


APP_NAME = 'dnspod'
APP = AppTool(APP_NAME, os.getcwd(), 'config')
CONFIG = APP.config
LOGGER = APP.logger
IP_ADDR = {
    6: ':::',
    4: '...'
}
IP_FILE = './config/ipv{}'
UID = CONFIG['dnspod']['id']
UTOKEN = CONFIG['dnspod']['token']
URL = 'https://dnsapi.cn/'
DOMAIN_RECORD = {}


def p(*values, force=False):
    """非debug时打印结果
    """
    if CONFIG['debug'] or force:
        print('\n【', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '】 ', sep='', end='')
        print(*values)


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
    result = res.json()
    #p(result)
    if result['status']['code'] != '1':
        raise RuntimeError('Dnspod API调用失败')
    return res.json()


def notifyByEmail(config, data):
    prefix = 'error_' if 'error' in data else ''
    subject = config[prefix + 'subject'].format(**data)
    body = config[prefix + 'body'].format(**data)
    p('邮件===>', subject, '; ', body)
    if not CONFIG['dry']:
        res = APP.send_email(subject, body)
        if res:
            p('邮件推送失败：', res, force=True)
        else:
            p('邮件发送成功。')


def notifyByDingTail(config, data):
    """发消息给钉钉机器人
    """
    token = config['token']
    if not token:
        p('ERROR: 没有钉钉token')
        return
    prefix = 'error_' if 'error' in data else ''
    data = {
        "msgtype": "text",
        "text": {
            "content": config['keyword'] + config[prefix + 'message'].format(**data)
        },
        "at": config['at']
    }
    p('钉钉机器人===>', data)
    if not CONFIG['dry']:
        res = requests.post(url="https://oapi.dingtalk.com/robot/send?access_token={}".format(token), \
            headers = {'Content-Type': 'application/json'}, data=json.dumps(data))
        p('钉钉推送结果：', res.json())


def notifyByServerChan(config, data):
    prefix = 'error_' if 'error' in data else ''
    url = 'https://sc.ftqq.com/{sckey}.send'.format(**config)
    title = config[prefix + 'title'].format(**data)
    message = config[prefix + 'message'].format(**data)
    p('Server酱===>', title, '; ', message)
    if not CONFIG['dry']:
        res = requests.get(url, params={'text': title, 'desp': message})
        p('Server酱推送结果：', res.json())


def notify(data):
    notifyConfig = CONFIG['notify']
    if 'mail' in notifyConfig:
        notifyByEmail(CONFIG['mail'], data)
    if 'dingtalk' in notifyConfig:
        notifyByDingTail(CONFIG['dingtalk'], data)
    if 'ServerChan' in notifyConfig:
        notifyByServerChan(CONFIG['ServerChan'], data)


def parseIp(ipPair, version):
    """解析本地网卡中的IP信息

    Args:
        ipPair (str): IP信息文本
        version (int): 4,6

    Returns:
        tuple: (ip, score)
    """
    ipLine, tlft = ipPair
    if version == 4:
        ipMatch = re.findall(r'inet ([0-9\.]+)/(\d+)\s', ipLine)
    elif version == 6:
        ipMatch = re.findall(r'inet6 ([0-9a-f:]+)/(\d+)\s', ipLine)
    p(ipMatch)
    ip, prefix = ipMatch[0]
    prefix = int(prefix)
    tlftMatch = re.findall(r'valid_lft (\d+sec|forever) preferred_lft (\d+sec|forever)', tlft)
    p(tlftMatch)
    valid, prefer = tlftMatch[0]

    if prefer == 'forever':
        score = sys.maxsize
    else:
        prefer = int(prefer[:-3])       # Remove 'sec'
        valid = int(valid[:-3])         # Remove 'sec'
        score = (prefer + valid) * prefix
        if 'mngtmpaddr' in ipLine:
            score = prefer * 0.8
    return (ip, score)


def saveIP(ip, version):
    """保存新IP

    Args:
        ip (str): 新IP
        version (int): 4,6
    """
    ipFilePath = IP_FILE.format(version)
    p(f'新IP地址已经保存到{ipFilePath}')
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
            ip = fd.readline()
            return ip
    else:
        return ''


def getIpByRegex(version):
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
    p(f'获取到本地IPv{version}', ipPairList)

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
        raise RuntimeError(f'无法找到IPv{version}地址')


def getIpByApi(version):
    apiUrls = [
        'ip.sb',
        'myip.com',
        'dyndns.com'
    ]
    for apiUrl in apiUrls:
        iper = Ip.create(apiUrl, version)
        ip = iper.getIp()
        p(ip)
        if ip['ip']:
            return ip
    return {'ip': None, 'url': None}
    

def getIp(version):
    methodConfig = CONFIG[f'get_ipv{version}']
    ipRegex = None
    ipApi = None
    
    if 'regex' in methodConfig:
        ipRegex = getIpByRegex(version)

    if 'api' in methodConfig:
        ipData = getIpByApi(version)
        ipApi = ipData['ip']
        ipUrl = ipData['url']

    ip = None
    if ipRegex and ipApi:
        ip = ipApi
        if ipRegex != ipApi:
            APP.send_email(f'IPv{version}不一致', f'从网卡获取的IP为{ipRegex}，从{ipUrl}获取的IP为{ipApi}')        
    elif not ipRegex and not ipApi:
        raise RuntimeError(f'未获取到IPv{version}地址')
    elif ipApi:
        ip = ipApi
    elif ipRegex:
        ip = ipRegex
    return ip


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
                    p(f'{subDomainName}的IPv{version}地址与线上一致：{newIP}')
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
            else:
                data = {
                    'domain_id': domainId,
                    'sub_domain': '@' if subDomainName == domain['name'] else subDomainName.replace('.'+domain['name'], ''),
                    'value': newIP,
                    'record_type': recordType,
                    'record_line': '默认'
                }
                action = 'Record.Create'
            p(data)
            if not CONFIG['dry']:
                result = requestDnsApi(action, data)
                p(result)
                status = result['status']
                if status['code'] != '1':
                    raise RuntimeError('{}-{}'.format(status['code'], status['message']))


def run(version):
    assert(version == 4 or version == 6)
    dnsType = 'AAAA' if version == 6 else 'A'
    domains = CONFIG[f'ipv{version}']
    if not domains:
        p(f'未配置IPv{version}，不需要更新。')
        return
    domainStr = ','.join(domains)
    try:
        p('*'*40 + f'IPv{version}' + '*'*40)
        global IP_ADDR
        newIP = getIp(version)
        p(f'解析IPv{version}结果为：{newIP}', force=True)
        oldIp = getOldIP(version)
        if newIP != oldIp or CONFIG['force']:
            IP_ADDR[version] = newIP
            p('IPv{}已发生改变，上次地址为{}'.format(version, oldIp), force=True)
            for subDomain in domains:
                refreshRecord(subDomain, newIP, version)
            p(f'域名{domains}的{dnsType}纪录已经更新为{newIP}', force=True)
            notify({'version': version, 'dnsType': dnsType, 'ip': newIP, 'domains': domainStr})
            if not CONFIG['dry']:
                saveIP(newIP, version)
        else:
            p(f'IPv{version}未发生改变，程序结束')
    except Exception as ex:
        p('!!!运行失败，原因：', ex, force=True)
        if CONFIG['debug']:
            traceback.print_exc()
        notify({'version': version, 'dnsType': dnsType, 'domains': domainStr, 'error': ex})
    
    if CONFIG['dry']:
        print('\n\n' + '!'*20 + f'-这是在dry模式下运行，实际IPv{version}域名未作更新-' + '!'*20)


def start():
    while True:
        run(6)
        run(4)
        if '-d' in sys.argv:
            time.sleep(CONFIG['interval'])
        else:
            break

if __name__ == "__main__":
    start()