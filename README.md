# DDSN 更新DNSPod的域名

## 一直在找一个好用的DDNS脚本，特别是Docker版本的，但试了好几个，就是更新不成功。

## 所以还是想自己做一个吧，就专门做一个DNSPod版本的，好用就行。

<br>

## 1. 获取IP的方式：
### 目前支持脚本方式和访问公用api的方式

<br>

## 2. IP更新后的通知方式：
### 目前支持邮件、[钉钉机器人](http://dwz.win/MqK)、[Server酱](http://sc.ftqq.com/)

<br>

## 3. 对于IPv6支持DDNS 服务器方式：
### 方便对多个设备DDNS，避免多处部署，多处更新

<br>

# 说明：
### 首次运行时，程序会检测当前目录下是否有**config_local.py**这个文件，这个文件中的值会覆盖默认的**config.py**中的值。
### 如果没有此文件，则会创建一个**config_sample.py**示例文件，只要在这个新建的文件中修改相应的值并另存为confg_local.py就可以了。
### **config_sample.py**会被新版本覆盖，因此请不要在其中保存数据，而是另存为**confg_local.py**。
### **config_sample.py**中有各个配置的详细说明，不用担心不会设置。详见：[config.py](https://github.com/chariothy/dnspod-ddns/blob/master/config.py)

<br>

## 1. 首次运行
### Docker 方式
```
docker pull chariothy/dnspod-ddns 

cd ~ && mkdir dnspod && cd ~/dnspod

docker run -it --rm --name ddns -v $PWD/config:/usr/src/app/config --network=host chariothy/dnspod-ddns
```
### Python方式：(Python版本>=3.8)
**在Windows下运行时，请将 get_ipv4 和 get_ipv6 均配置为 api 方式**
```
git clone git@github.com:chariothy/dnspod-ddns.git && cd dnspod-ddns

pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade -r ./requirements.txt （每次更新时需要运行）

python3 main.py
```

## 2. 后台运行（首次运行调试成功后，间隔时间可在配置中调整interval）
### Docker方式 
**daemon方式运行时，如果修改配置文件，需要运行 ```docker restart ddns``` 让新配置生效**
```
（每次更新时需要运行 docker pull chariothy/dnspod-ddns && docker stop ddns && docker rm ddns ）

cd ~/dnspod

docker run -itd \
--restart unless-stopped \
--name ddns \
-v $PWD/config:/usr/src/app/config \
--network=host \
chariothy/dnspod-ddns \
python main.py -d
```

### Python方式
**daemon方式运行时，如果修改配置文件，需要重启进程让新配置生效**
```
cd dnspod-ddns && python3 main.py -d
```

## 3. DDNS 服务器
### 此模式基本针对IPv6，因为IPv4一般为NAT方式，公网IP只需要在一台机器运行即可。
### 但IPv6会给每台设备分配一个公网地址，因此要给每台设备上运行一个DDNS 客户端。
### 而如果使用DDNS 服务器，则只需要在每台设备上curl调用DDNS 服务器的API即可。

<br>

#### 3.1 在一台设备上用后台方式建立起一个DDNS，假设对应域名为 **ddns.domain.com**
#### 3.2 在配置文件中设置 server_token，防止被盗用（```openssl rand -hex 10```）
#### 3.3 docker方式（建议使用host网络因为docker对IPv6支持不够好）
```
（每次更新时需要运行 docker pull chariothy/dnspod-ddns && docker stop ddns && docker rm ddns ）

cd ~/dnspod

docker run -itd \
--restart unless-stopped \
--name ddns-server \
-v $PWD/config:/usr/src/app/config \
--network=host \
chariothy/dnspod-ddns \
python server.py
```
#### 3.4 python方式
```cd dnspod-ddns && python3 server.py```

#### 3.5 每个设备客户端
````
# 如果此设备只对应一个域名（有些终端需要在 ? 和 & 前加上 \ 来转义）
curl -X POST "ddns.domain.com:7788/ip?domain=node.domain.com&token=token_to_request_ddns_server_api"

# 如果此设备只对应多个域名
curl -H "Content-Type:application/json" -d '{"domain":["node1.domain.com", "node2.domain.com"], "token":"token_to_request_ddns_server_api"}' "ddns.domain.com:7788/ip"
````
<br>

## 注意：
1. 配置文件中默认dry为True，需要将其修改为False才会实际生效。
1. docker方式运行时，每次更新请先运行 ```docker pull chariothy/dnspod-ddns```
1. python方式运行时，每次更新请先运行 ```pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade -r ./requirements.txt```

<br>

## TODO:
1. 加入域名权重配置
1. 加入docker-compose用法说明
1. port自定义
1. interval分别设置