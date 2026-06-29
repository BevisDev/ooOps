ARG STRIMZI_VERSION=1.0.1
ARG KAFKA_VERSION=4.2.0

FROM quay.io/strimzi/kafka:${STRIMZI_VERSION}-kafka-${KAFKA_VERSION}

LABEL maintainer="dev.binhtt@gmail.com"

USER root

RUN mkdir -p /opt/kafka/plugins/{debezium-postgres,debezium-mysql,debezium-sqlserver,debezium-oracle,minio}

COPY plugins/debezium-connector-postgres/   /opt/kafka/plugins/debezium-postgres/
COPY plugins/debezium-connector-mysql/      /opt/kafka/plugins/debezium-mysql/
COPY plugins/debezium-connector-sqlserver/  /opt/kafka/plugins/debezium-sqlserver/
COPY plugins/debezium-connector-oracle/     /opt/kafka/plugins/debezium-oracle/
COPY plugins/minio/                         /opt/kafka/plugins/minio/

USER 1001