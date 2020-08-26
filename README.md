# DDSN 更新DNSPod的域名

## 一直在找一个好用的DDNS脚本，特别是Docker版本的，但试了好几个，就是更新不成功。

## 所以还是想自己做一个吧，就专门做一个DNSPod版本的，好用就行。

# 说明：
### 首次运行时，程序会检测当前目录下是否有**config_local.py**这个文件，这个文件中的值会覆盖默认的**config.py**中的值。
### 如果没有此文件，则会创建一个**config_local.py**示例文件，只要在这个新建的文件中修改相应的值就可以了。
### config_local.py中有各个配置的详细说明，不用担心不会设置。

## 1. Docker用法：
docker run -it --rm --name ddns -v $PWD:/usr/src/app/config --network=host chariothy/dnspod-ddns

## 2. Python用法：(Python版本>=3.6)
git clone git@github.com:chariothy/dnspod-ddns.git

cd dnspod

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r ./requirements.txt

python main.py

