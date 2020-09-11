import requests
from util import CONFIG, APP, now


URL = 'https://dnsapi.cn/'
UID = CONFIG['dnspod']['id']
UTOKEN = CONFIG['dnspod']['token']
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
    result = res.json()
    #p(result)
    if result['status']['code'] != '1':
        raise RuntimeError(f'Dnspod API调用失败：{result}')
    return res.json()


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
    example = {
        "NOTICE": '目前在dry模式下运行',
        "status": {
            "code":"1",
            "message":"Action completed successful",
            "created_at":now()
        },
    }
    for domainId in DOMAIN_RECORD.keys():
        domain = DOMAIN_RECORD[domainId]
        if domain['name'] in subDomainName:
            getRecords(domainId)
            key = f'{subDomainName}:{recordType}'
            if key in domain['records']:
                record = domain['records'][key]
                if record['value'] == newIP:
                    APP.D(f'{subDomainName}的IPv{version}地址与线上一致：{newIP}')
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
                example["record"] = {
                    "id":16894439,
                    "name":domain['name'],
                    "value":newIP,
                    "status":"enable"
                }
            else:
                data = {
                    'domain_id': domainId,
                    'sub_domain': '@' if subDomainName == domain['name'] else subDomainName.replace('.'+domain['name'], ''),
                    'value': newIP,
                    'record_type': recordType,
                    'record_line': '默认'
                }
                action = 'Record.Create'
                example["record"] = {
                    "id":"16894439",
                    "name":domain['name'],
                    "status":"enable"
                }
            APP.D(data)
            if not CONFIG['dry']:
                result = requestDnsApi(action, data)
                APP.D(result)
                return result
            APP.D(example)
    return example
                    
    # Clear cache
    DOMAIN_RECORD.clear()