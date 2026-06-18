# 🚀 Apache Kafka – Introduction

Apache Kafka is a **distributed streaming platform** designed for building real-time data pipelines and event-driven applications.  
It provides high throughput, reliability, and horizontal scalability, making it a core component in modern microservice and data-processing architectures.

You can explore visual concepts of Kafka here:  
👉 https://softwaremill.com/kafka-visualisation/

## 🔥 Key Features

### ✔ High Throughput

Kafka can handle millions of messages per second with minimal overhead.

### ✔ Distributed & Scalable

Topics are partitioned and replicated across multiple brokers to ensure horizontal scaling and fault tolerance.

### ✔ Durable Message Storage

Kafka stores messages on disk and replicates them across nodes for reliability.

### ✔ Publisher–Subscriber Messaging

Producers publish messages to topics, and consumers subscribe to read them in real time.

### ✔ Fault Tolerant

Nodes can fail without losing data thanks to replication and leader election.

---

## 🧩 Core Concepts

### **Topic**

A named stream of messages. Topics are split into **partitions**.

### **Partition**

A log file that stores messages in immutable, ordered sequence.

### **Producer**

An application that writes (publishes) messages to Kafka topics.

### **Consumer**

An application that reads messages from Kafka topics.

### **Broker**

A Kafka server that stores and distributes message data.

### **Cluster**

A group of brokers working together.

### **Consumer Group**

A set of consumers cooperating to consume data from partitions in parallel.

---
