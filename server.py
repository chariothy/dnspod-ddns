from flask import Flask, abort, request, jsonify
from dnspod import refreshRecord
from util import CONFIG, APP, now
from notify import notify
from ip import saveIP, getOldIP


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

TOKEN = CONFIG['server_token']

def get_real_ip():
    ip = request.environ.get('HTTP_X_FORWARDED_FOR')
    return ip if ip else request.environ.get('REMOTE_ADDR')


def ipv6to4(ipv6):
    """转换ipv6形式的ipv4地址

    Args:
        ipv6 (str): ipv6形式的ipv4地址, Ex. ::ffff:127.0.0.1
    """
    prefix = '::ffff:'
    lenPrefix = len(prefix)
    if ipv6[:lenPrefix] == prefix:
        return ipv6.split(':')[-1]
    return None


def request_get(key):
    """多种渠道获取请求数据，优先从json data中获取，否则从url中获取

    Args:
        key (str): 键
    """
    val = None
    if request.json:
        val = request.json.get(key)
    if not val:
        val = request.args.get(key)
    return val


@app.route('/ip', methods=['POST'])
def set_ip():
    domains = request_get('domain')
    token = request_get('token')
    #print(domains, token)

    if token != TOKEN:
        message = {
            'error': 'Unauthorized'
        }
        return jsonify(message), 404

    if not domains or type(domains) not in (str, list) :
        message = {
            'error': 'Invalid request data',
            'example1': {
                'domain': 'sub.domain.com'
            },
            'example2': {
                'domain': ['sub1.domain.com', 'sub2.domain.com']
            }    
        }
        return jsonify(message), 422
    
    ipv6 = get_real_ip()
    ipv4 = ipv6to4(ipv6)
    newIP = ipv4 if ipv4 else ipv6
    version = 4 if ipv4 else 6
    dnsType = 'AAAA' if version == 6 else 'A'

    if type(domains) == str:
        domains = [domains]

    results = []
    changedDomains = []
    for domain in domains:
        oldIp = getOldIP(version, domain)
        if newIP != oldIp or CONFIG['force']:
            APP.info(f'域名{domain}的IPv{version}已发生改变，上次地址为{oldIp}')
            result = refreshRecord(domain, newIP, version)
            results.append(result)
            changedDomains.append(domain)
        else:
            APP.debug(f'域名{domain}的{dnsType}纪录未发生改变')
            results.append({
                "status": {
                    "code":"1",
                    "message":"Action completed successful",
                    "created_at":now()
                },
                'record': {
                    "name":domain,
                    "value":newIP,
                    "status":"unchanged"
                }
            })
    if not CONFIG['dry']:
        saveIP(version, newIP, domains)
    if changedDomains:
        notify({
            'version': version, 
            'dnsType': 'AAAA' if version == 6 else 'A', 
            'ip': newIP, 
            'domains': ','.join(changedDomains)
        })
    return jsonify(results)


@app.route('/ip', methods=['GET'])
def get_ip():
    ipv6 = get_real_ip()
    ipv4 = ipv6to4(ipv6)

    ip = ipv4 if ipv4 else ipv6
    return jsonify(ip)


if __name__ == "__main__":
    # 将host设置为0.0.0.0，则外网用户也可以访问到这个服务
    app.run(host="::", port=CONFIG['server_port'], debug=CONFIG['debug'])