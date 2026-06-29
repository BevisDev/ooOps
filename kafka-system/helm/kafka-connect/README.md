# Kafka Connect Cluster

- Kafka Connect is an integration toolkit
- Provides a framework for integrating Kafka with an external data source or target
- Connectors are plugins that provide the connection configuration needed.
- Kafka Connect clusters deployed using the `KafkaConnect` resource
- Connectors created using the `KafkaConnector` resource.

## 2. Connector

### 2.1 S3/Minio

docs: https://www.confluent.io/hub/confluentinc/kafka-connect-s3

---
Partitioning
- DefaultPartitioner: Creates a structure based on topic and partition
- FieldPartitioner: Partitions data based on field values from records
- TimeBasedPartitioner: Creates partitions based on record timestamps

To use time-based partitioning:
```sh
partitioner.class: io.confluent.connect.storage.partitioner.TimeBasedPartitioner
path.format: 'year=YYYY/month=MM/day=dd/hour=HH'
timestamp.extractor: RecordField
timestamp.field: timestamp
```

DataFormat and Compression
- JSON: **io.confluent.connect.s3.format.json.JsonFormat**
- Avro: **io.confluent.connect.s3.format.avro.AvroFormat**
- Parquet: **io.confluent.connect.s3.format.parquet.ParquetFormat**

Best practices:
1. Sizing: Set appropriate `flush.size` based on your record size and frequency
2. Partitioning: Choose a partitioning strategy that aligns with your query patterns
3. Use Parquet or Avro for analytical workloads to improve query performance


### 2.2 Debizum

docs: https://debezium.io/documentation/reference/3.5/connectors/index.html

---
Procedure:
1. Download the Debezium
2. Extract the files into your Kafka Connect environment.
3. Add the directory with the JAR files to Kafka Connect's plugin.path.
4. Restart your Kafka Connect process to pick up the new JAR files.

Deployments:
- [Oracle](https://debezium.io/documentation/reference/3.5/connectors/oracle.html#oracle-deploying-a-connector)
- [MySQL](https://debezium.io/documentation/reference/3.5/connectors/mysql.html#mysql-deploying-a-connector)
- [Postgres](https://debezium.io/documentation/reference/3.5/connectors/postgresql.html#postgresql-deployment)
- [MSSQL](https://debezium.io/documentation/reference/3.5/connectors/sqlserver.html#sqlserver-deploying-a-connector)

connector.class:
- s3/minio: **io.confluent.connect.s3.S3SinkConnector**
- postgres: **io.debezium.connector.postgresql.PostgresConnector**
- oracle: **io.debezium.connector.oracle.OracleConnector**
- mssql: **io.debezium.connector.sqlserver.SqlServerConnector**
- mysql: **io.debezium.connector.mysql.MySqlConnector**

## Document

- [Deploying Kafka Connect](https://strimzi.io/docs/operators/latest/deploying#kafka-connect-str)
- [Exposing API](https://strimzi.io/docs/operators/latest/deploying#con-exposing-kafka-connect-api-str)
- [Debezium Connector](https://debezium.io/documentation/reference/3.5/connectors/index.html)
