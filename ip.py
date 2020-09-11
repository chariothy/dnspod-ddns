from abc import ABC
import requests
import re, sys, os, subprocess

import socket
import requests.packages.urllib3.util.connection as urllib3_cn

from util import CONFIG, APP
from chariothy_common import dump_json, load_json

IP_FILE = './config/ipv{}'
DOMAIN_IP = {}

def allowed_gai_family(version):
    """
     https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    assert version in (4, 6)
    if version == 4:
        family = socket.AF_INET
    elif version == 6 and urllib3_cn.HAS_IPV6:
        family = socket.AF_INET6 # force ipv6 only if it is available
    return family


class Ip(ABC):
    """IP解析抽象基类

    """
    timeout = 5

    @staticmethod
    def create(url, version):
        """根据不同的url创建相应子类

        Args:
            url (str): API的URL
        """
        if 'ip.sb' == url:
            return IpIpSb('https://api.ip.sb/ip', version)
        elif 'myip.com' == url:
            return IpMyIpCom('https://api.myip.com', version)
        elif 'dyndns.com' == url:
            return IpDyndns('http://checkip{}.dyndns.com', version)
        else:
            pass


    def __init__(self, url, version):
        self.url = url
        self.version = version


    def parseIp(self, res):
        raise NotImplementedError


    def getIp(self):
        _allow_gai_family = urllib3_cn.allowed_gai_family
        urllib3_cn.allowed_gai_family = lambda : allowed_gai_family(self.version)
        try:
            res = requests.get(self.url, timeout=Ip.timeout)
            ip = self.parseIp(res)
            cost = int(res.elapsed.microseconds/1000)
            error = None
        except Exception as ex:
            ip = None
            cost = Ip.timeout * 1000
            error = ex
        finally:
            urllib3_cn.allowed_gai_family = _allow_gai_family

        return {
            'ip': ip,
            'cost': f'{cost}ms',
            'url': self.url,
            'error': error
        }


class IpIpSb(Ip):
    def parseIp(self, res):
        return res.text.strip()


class IpDyndns(Ip):
    def __init__(self, url, version):
        self.version = version
        self.url = url.format('v6' if version==6 else '')
        self.reg = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}') \
            if version == 4 \
            else re.compile(r'2[0-9a-fA-F]{3}:(?:[0-9a-fA-F]{0,4}:){1,6}[0-9a-fA-F]{1,4}')


    def parseIp(self, res):
        match = self.reg.findall(res.text)
        return match[0]


class IpMyIpCom(Ip):
    def parseIp(self, res):
        return res.json()['ip']


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
    APP.D(ipMatch)
    ip, prefix = ipMatch[0]
    prefix = int(prefix)
    tlftMatch = re.findall(r'valid_lft (\d+sec|forever) preferred_lft (\d+sec|forever)', tlft)
    APP.D(tlftMatch)
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


def saveIP(version, ip, domains):
    """保存新IP

    Args:
        ip (str): 新IP
        version (int): 4,6
    """
    ipFilePath = IP_FILE.format(version)
    for domain in domains:
        DOMAIN_IP[domain] = ip
    dump_json(ipFilePath, DOMAIN_IP)
    APP.D(f'新IP地址已经保存到{ipFilePath}')


def getOldIP(version, domain):
    """获取上次IP

    Args:
        version (int): 4,6
        domain (str): 域名

    Returns:
        str: 上次IP
    """
    global DOMAIN_IP
    if DOMAIN_IP:
        return DOMAIN_IP.get(domain)

    ipFilePath = IP_FILE.format(version)
    try:
        ipDict = load_json(ipFilePath, {})
    except Exception:
        ipDict = {}

    DOMAIN_IP = ipDict
    return ipDict.get(domain)


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
    APP.D(command)
    ipStr = subprocess.check_output(command, shell=True).decode('utf-8')
    APP.D(ipStr)

    ipParts = [x.strip() for x in ipStr.split('\n')]
    APP.D(ipParts)
    ipPairList = list(zip(ipParts[::2], ipParts[1::2]))
    APP.D(f'获取到本地IPv{version} >>> {ipPairList}')

    if len(ipPairList) == 1:
        ips = parseIp(ipPairList[0], version)
        return ips[0]
    elif len(ipParts) > 1:
        ipList = []
        for ipPair in ipPairList:
            ips = parseIp(ipPair, version)
            ipList.append(ips)
        ipList.sort(key=lambda ip: ip[-1], reverse=True)
        APP.D(ipList)
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
        APP.D(ip)
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
            APP.W(f'IPv{version}不一致', f'从网卡获取的IP为{ipRegex}，从{ipUrl}获取的IP为{ipApi}')        
    elif not ipRegex and not ipApi:
        raise RuntimeError(f'未获取到IPv{version}地址')
    elif ipApi:
        ip = ipApi
    elif ipRegex:
        ip = ipRegex
    return ip
