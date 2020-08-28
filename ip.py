from abc import ABC
import requests
import re

import socket
import requests.packages.urllib3.util.connection as urllib3_cn

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
