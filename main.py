import time, sys

from util import show_diff, CONFIG, APP 
from dnspod import requestDnsApi, refreshRecord
from ip import Ip, getIp, getOldIP, saveIP
from notify import notify


DAEMON = '-d' in sys.argv

def run(version):
    assert(version == 4 or version == 6)
    dnsType = 'AAAA' if version == 6 else 'A'
    domains = CONFIG[f'ipv{version}']
    if not domains:
        APP.debug(f'未配置IPv{version}，不需要更新。')
        return
    try:
        APP.debug('*'*40 + f'IPv{version}' + '*'*40)
        newIP = getIp(version)
        APP.debug(f'解析IPv{version}结果为：{newIP}')
        changedDomains = []
        for subDomain in domains:
            oldIp = getOldIP(version, subDomain)
            if newIP != oldIp or CONFIG['force']:
                APP.info(f'域名{subDomain}的IPv{version}已发生改变，上次地址为{oldIp}')
                
                result = refreshRecord(subDomain, newIP, version)
                status = result['status']
                if status['code'] != '1':
                    raise RuntimeError('{}-{}'.format(status['code'], status['message']))

                APP.info(f'域名{subDomain}的{dnsType}纪录已经更新为{newIP}')
                changedDomains.append(subDomain)
            else:
                APP.debug(f'域名{subDomain}的{dnsType}纪录未发生改变')
        if not CONFIG['dry']:
            saveIP(version, newIP, domains)
        if changedDomains:
            notify({'version': version, 'dnsType': dnsType, 'ip': newIP, 'domains': ','.join(changedDomains)})
    except Exception as ex:
        APP.error(f'!!!运行失败，原因：{ex}')
        notify({'version': version, 'dnsType': dnsType, 'domains': ','.join(domains), 'error': ex})
    
    if CONFIG['dry']:
        print('\n\n' + '!'*20 + f'-这是在dry模式下运行，实际IPv{version}域名未作更新-' + '!'*20)


def start():
    while True:
        run(6)
        run(4)
        if DAEMON:
            time.sleep(CONFIG['interval'])
        else:
            break

if __name__ == "__main__":
    start()