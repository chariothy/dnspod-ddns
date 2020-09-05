CONFIG = {
    'version': '1.2',                   # 配置文件版本
    "debug": True,                      # 是否输出更多信息
    'dry': False,                       # 是否dry run，只检测不更新，防止测试时频繁更新和推送，也不会保存旧IP
    'force': False,                     # 是否强制更新，不管与上次的检测结果是否相同都更新
    'interface': 'eth0',                # 要检测IP地址的网卡名称，可以用"ip addr"来查看
    'interval': '5',                    # 后台运行时的间隔时间，单位为秒，建议：使用api方式获取IP的间隔设置为300，使用regex获取IP的设置为5
    'dnspod': {
        'id': 1234567,                  # dnspod的ID
        'token': 'your_dnspod_token'    # dnspod的token
    },
    'notify': [                         # 通知方式，会对列表中列出的方式进去通知，列表为空则不做任何通知
        'mail',                         # 通过邮件方式通知，需要配置'mail'和'smtp'
        'ServerChan',                   # 通过微信公众号Server酱(http://sc.ftqq.com/)通知，需要配置'ServerChan'
        'dingtalk'                      # 通过钉钉机器人(http://dwz.win/MqK)通知，需要配置'dingtalk'
    ],
    'get_ipv4': ['api'],                # 获取ipv4的方式，支持：
                                        #   'regex':  正则解析ip addr从网卡获取的ip的方式，速度最快
                                        #   'api': 通过公共api获取ip，目前支持dyndns.com, myip.com, ip.sb, ipify.org。准确性最高
                                        # 同时配置regex和url的话会将两者结果进行对比，如果两者结果不同，则使用url的结果，并发送报告
                                        # !!! 建议：如果从网卡可以获取公网IP，建议使用regex方式，快且稳定。公共api慢而不稳定。后面我会考虑自建一个api。
    'get_ipv6': ['regex'],              # 获取ipv6的方式，详情同get_ipv4
    'ipv4': ['ipv4.domain.com'],        # IPv4地址对应的域名，为空则不更新ipv4地址
                                        #       如：a.domain.com
                                        #       可以使用泛域名如：*.sub.domain.com
                                        #       可以直接写根域名：domain.com (对应A名称为@)
    'ipv6': ['ipv6.domain.com'],        # IPv6地址对应的域名, 详情同IPv4
    'mail': {
        'from': ('Hongyu TIAN', 'chariothy@gmail.com'),     # 发件人信息，（名称，地址）
        'to': (('Hongyu TIAN', 'chariothy@gmail.com'),),    # 收件人信息列表，（（名称，地址），）
        'subject': 'IPv{version}地址发生改变',               # 邮件标题，可用变量：version(4,6)
        'body': '域名{domains}的{dnsType}纪录已经更新为{ip}', # 邮件正文，可用变量：
                                                            #       domains(所有相应域名，逗号分隔)
                                                            #       dnsType(A,AAAA)
                                                            #       ip(IP地址)
        'error_subject': '更新IPv{version}地址失败',         # 出错邮件标题，可用变量：version(4,6) 
        'error_body': '更新域名{domains}的{dnsType}纪录时出错：{error}'  # 出错邮件正文，可用变量：
                                                            #       domains(所有相应域名，逗号分隔)
                                                            #       dnsType(A,AAAA)
                                                            #       error(错误信息)                                                 
    },
    'smtp': {                           # 邮箱SMTP信息，可从邮箱服务商处获取
        'host': 'smtp.gmail.com',
        'port': 587,                    # 此处需要与type对应
        'user': 'chariothy@gmail.com',
        'pwd': '123456',                # 可能需要邮件应用专用密码，请参考邮箱服务商
        'type': 'tls'                   # 此处需要与port对应，支持 plain (默认) / ssl / tls
    },
    'ServerChan': {                                               # 请遵守Server酱的调用频率限制，否则可能被禁用
        'sckey': 'SCU38711T818290d9c930e171e83e02b96afbc3365c2ebe41b8cd9',  # Server酱的SCKEY
        'title': 'IPv{version}地址发生改变',                       # 消息标题，可用变量：version(4,6)
        'message': '域名{domains}的{dnsType}纪录已经更新为{ip}',    # 消息正文，可用变量：
                                                                  #       domains(所有相应域名，逗号分隔)
                                                                  #       dnsType(A,AAAA)
                                                                  #       ip(IP地址)
        
        'error_title': '更新IPv{version}地址失败',         # 出错邮件标题，可用变量：version(4,6) 
        'error_message': '更新域名{domains}的{dnsType}纪录时出错：{error}'  # 出错邮件正文，可用变量：
                                                            #       domains(所有相应域名，逗号分隔)
                                                            #       dnsType(A,AAAA)
                                                            #       error(错误信息)                    
                                                            # !!! 官网FAQ：“不要在text参数中传递引号、点、花括号等字符。因为微信的接口不支持一系列的特殊字符，
                                                            # 但没有详细列表，所以我只简单的过滤掉了一些。如果需要发送特殊字符，请放到 desp字段中。”
    },
    'dingtalk': {                       # 通过钉钉机器人发送通知，具体请见钉钉机器人文档
        'token': 'your_ding_talk_robot_token',
        "at": {
            "atMobiles": ["13888888888"],
            "isAtAll": "false"
        },
        'keyword': 'DDNS',              # 钉钉机器人的三种验证方式之一为关键字验证，
                                        # 在设置机器人时自定义一个关键字，然后在消息中必须包含这个关键字
                                        # 否则发送会失败。
        'message': '域名{domains}的{dnsType}纪录已经更新为{ip}',    # 消息正文（由），可用变量：
                                                                  #       domains(所有相应域名，逗号分隔)
                                                                  #       dnsType(A,AAAA)
                                                                  #       ip(IP地址)
        'error_message': '更新域名{domains}的{dnsType}纪录时出错：{error}'  # 出错邮件正文，可用变量：
                                                            #       domains(所有相应域名，逗号分隔)
                                                            #       dnsType(A,AAAA)
                                                            #       error(错误信息)                    
    },
}