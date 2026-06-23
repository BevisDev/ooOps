# Kafka (Strimzi)

Helm chart deploy **Kafka cluster** (KRaft, 3 controllers + 3 brokers).

# Note

045-Crd-kafkanodepool.yaml
 - 2 role (controller | broker)
 - storage: type (ephemeral | persistent-claim | jbod)

## Kiến trúc

```text
Strimzi Operator (chart cdc/strimzi)
        ↓
Kafka CR + KafkaNodePool CR (chart này)
        ↓
Kafka brokers / controllers (pods)
```

## Cài đặt

```bash
helm upgrade --install dp-kafka . -n kafka
```

Argo CD: app `kafka` trong `dp-ops` → namespace `kafka`, `values.yaml`.

## Prerequisites

1. **Strimzi operator** đã chạy (`cdc/strimzi`)
2. Namespace `kafka` có `VaultAuth` + `dockerhub-regcred` (`dp-secrets`)
3. **StorageClass** `longhorn` (hoặc sửa `nodePools[].storage.class`)

## Bootstrap servers

| Listener | Địa chỉ |
|----------|---------|
| Plain | `dp-kafka-kafka-bootstrap.kafka.svc:9092` |
| TLS | `dp-kafka-kafka-bootstrap.kafka.svc:9093` |

## Values chính

| Key | Mô tả |
|-----|-------|
| `clusterName` | Tên Kafka CR / label `strimzi.io/cluster` |
| `kafka.version` | Kafka version|
| `kafka.config` | `server.properties` overrides (RF=3, minISR=2) |
| `controllers` | KafkaNodePool controllers (KRaft metadata) |
| `brokers` | KafkaNodePool brokers (data plane) |
| `entityOperator` | Topic/User Operator (`KafkaTopic` CR) |
| `kafkaExporter` | Prometheus metrics |

## Liên kết

- [Strimzi Kafka CR](https://strimzi.io/docs/operators/latest/configuring.html#type-Kafka-reference)
- [KafkaNodePool](https://strimzi.io/docs/operators/latest/configuring.html#type-KafkaNodePool-reference)
- [Apache Kafka](https://kafka.apache.org/43/configuration/broker-configs/)
