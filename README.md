# DDSN 更新DNSPod的域名

### 一直在找一个好用的DDNS脚本，特别是Docker版本的，但试了好几个，就是更新不成功。

### 所以还是想自己做一个吧，就专门做一个DNSPod版本的，好用就行。

### 用法：
docker run -it --rm \
-v $PWD:/usr/src/myapp \
-w /usr/src/myapp \
chariothy/dnspod