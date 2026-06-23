# Kafka Cluster

Helm chart deploy **Kafka cluster** (KRaft, 3 controllers + 3 brokers).

## Prerequisites

1. **Strimzi operator** has deployed
2. **StorageClass** `longhorn`

## Kafka Node Pool

045-Crd-kafkanodepool.yaml
 - only 2 role (controller | broker)
 - storage: type (ephemeral | persistent-claim | jbod)


## Document

- [Strimzi Kafka CR](https://strimzi.io/docs/operators/latest/configuring.html#type-Kafka-reference)
- [KafkaNodePool](https://strimzi.io/docs/operators/latest/configuring.html#type-KafkaNodePool-reference)
- [Apache Kafka](https://kafka.apache.org/43/configuration/broker-configs/)
