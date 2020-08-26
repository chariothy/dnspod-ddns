# For Tencent DDNS
# @version 1.0

FROM python:3.8-alpine
LABEL maintainer="chariothy@gmail.com"

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

ARG TARGETPLATFORM
ARG BUILDPLATFORM

LABEL maintainer="chariothy" \
  org.opencontainers.image.created=$BUILD_DATE \
  org.opencontainers.image.url="https://github.com/chariothy/dnspod-ddns.git" \
  org.opencontainers.image.source="https://github.com/chariothy/dnspod-ddns.git" \
  org.opencontainers.image.version=$VERSION \
  org.opencontainers.image.revision=$VCS_REF \
  org.opencontainers.image.vendor="chariothy" \
  org.opencontainers.image.title="dnspod-ddns" \
  org.opencontainers.image.description="DDNS for dnspod" \
  org.opencontainers.image.licenses="MIT"

WORKDIR /usr/src/app
COPY ./requirements.txt ./

# Install libs
RUN pip install --no-cache-dir -r ./requirements.txt
# 本地编译时需要加国内代理
#RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r ./requirements.txt

COPY . .

CMD [ "python", "main.py" ]