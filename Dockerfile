# For Tencent DDNS
# @version 1.0

FROM python:3.8-alpine
LABEL maintainer="chariothy@gmail.com"

WORKDIR /usr/src/app
COPY . .

# Install libs
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r ./requirements.txt