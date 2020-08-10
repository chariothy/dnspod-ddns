CONFIG = {
    "debug": True,
    'interface': 'eth0',
    'dnspod': {
        'id': 1234567,
        'token': 'your_dnspod_token'
    },
    'dingtalk': {
        'token': 'your_ding_talk_robot_token',
        "at": {
            "atMobiles": ["13888888888"],
            "isAtAll": "false"
        }
    },
    'ipv4': ['ipv4.domain'],
    'ipv6': ['ipv6.domain']
}