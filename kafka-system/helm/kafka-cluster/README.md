# Kafka Cluster

Helm chart deploy **Kafka cluster** (KRaft, 3 controllers + 3 brokers).

## 1. Prerequisites

1. **Strimzi operator** has deployed
2. **StorageClass** `longhorn`

## 2. Kafka Node Pool

045-Crd-kafkanodepool.yaml
 - only 2 role (controller | broker)
 - storage: type (ephemeral | persistent-claim | jbod)


## 3. Kafka Topic

| Key | required | Default | description |
|-----|----------|---------|-------|
| `name` | x  | — | K8s resource name |
| `topicName` | x | — | topic name|
| `partitions` | | `3` | num partitions (just increse after created) |
| `replicas` | | `3` | Replication factor |
| `config` | | — | Kafka topic config |

some configs often use

| Key | example | description |
|-----|-------|-------|
| `retention.ms` | `604800000` | time keep message (ms) |
| `max.message.bytes` | `1048576` | max message size |

## Document

- [KafkaTopic Config](https://kafka.apache.org/43/configuration/topic-configs/)
- [Strimzi Kafka CR](https://strimzi.io/docs/operators/latest/configuring.html#type-Kafka-reference)
- [KafkaNodePool](https://strimzi.io/docs/operators/latest/configuring.html#type-KafkaNodePool-reference)
- [Apache Kafka](https://kafka.apache.org/43/configuration/broker-configs/)
