FROM alpine:3.23

ENV TZ=Asia/Ho_Chi_Minh

RUN apk add --no-cache \
        tzdata \
        curl \
        ca-certificates \
    && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && update-ca-certificates
