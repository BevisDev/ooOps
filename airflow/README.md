# Apache Airflow

- version: airflow 3.2.2
- image: 

## 1. Docker Images

  - apache/airflow:3.2.2 (Dockerfile for install plugins)
  - registry.k8s.io/git-sync/git-sync:v4.4.2 (optional) 

## 2. Secret key (bắt buộc)

### 2.1 Fernet key

Dùng để mã hóa password trong Airflow (Connection, Variable).

```bash
# Tạo key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

kubectl create secret generic airflow-fernet-key \
  --from-literal=fernet-key="<FERNET_KEY>" \
  -n airflow
```

> **Lưu ý:** Fernet key phải giữ nguyên sau khi deploy. Đổi key sẽ không giải mã được dữ liệu cũ.

### 2.2 API secret key & JWT secret

Dùng cho Airflow 3+ (API server, session, JWT).

```bash
kubectl create secret generic airflow-api-secret-key \
  --from-literal=api-secret-key="$(openssl rand -base64 32)" \
  -n airflow

kubectl create secret generic airflow-jwt-secret \
  --from-literal=jwt-secret="$(openssl rand -base64 32)" \
  -n airflow
```

### 2.3 Database metadata

```bash
kubectl create secret generic airflow-metadata-secret \
  --from-literal=connection="postgresql+psycopg2://<user>:<password>@<host>:5432/<database>" \
  -n airflow
```

### 2.4 Dockerhub private registry (optional)

```bash
kubectl create secret docker-registry dockerhub-regcred \
  --docker-server='dockerhub.company.com.vn' \
  --docker-username='<username>' \
  --docker-password='<password>' \
  --docker-email=author@gmail.com \
  -n airflow
```

### 2.5 Azure OIDC (đăng nhập UI) (optional)

```bash
kubectl create secret generic airflow-azure-oidc \
  --from-literal=tenant-id="<AZURE_TENANT_ID>" \
  --from-literal=client-id="<AZURE_CLIENT_ID>" \
  --from-literal=client-secret="<AZURE_CLIENT_SECRET>" \
  -n airflow
```

### 2.6 SSH key (git-sync DAGs or gitBundles)

```bash
kubectl create secret generic airflow-ssh-secret \
  --from-file=gitSshKey=<path-to-private-key> \
  --from-file=known_hosts=<path-to-private-git>
  -n airflow
```

---

## 3 Connection qua Kubernetes Secret

Trong `values-prod.yaml`, connection được inject vào pod qua biến môi trường `AIRFLOW_CONN_<CONN_ID>`.

| Conn Id (trong DAG/UI) | K8s Secret | Key | Biến môi trường |
|------------------------|------------|-----|-----------------|
| `minio_conn` | `airflow-minio-conn` | `conn` | `AIRFLOW_CONN_MINIO_CONN` |
| `git_team1` | `airflow-git-conn-team1` | `conn` | `AIRFLOW_CONN_GIT_TEAM1` |
| `git_team2` | `airflow-git-conn-team2` | `conn` | `AIRFLOW_CONN_GIT_TEAM2` |
| `smtp_default` | `airflow-smtp-conn` | `conn` | `AIRFLOW_CONN_SMTP_DEFAULT` |

### 3.1 Tạo secret connection

Giá trị `conn` là **Airflow URI connection string**.

```bash
# Ví dụ: MinIO (S3)
kubectl create secret generic airflow-minio-conn \
  --from-literal=conn='aws://<access_key>:<secret_key>@/?region_name=us-east-1&endpoint_url=http%3A%2F%2F<minio-host>%3A9000' \
  -n airflow

# Ví dụ: Git
kubectl create secret generic airflow-git-conn-team1 \
  --from-literal=conn='git://<user>:<token>@<gitlab-host>/<group>/<repo>.git' \
  -n airflow

# Ví dụ: SMTP
kubectl create secret generic airflow-smtp-conn \
  --from-literal=conn='smtp://<user>%40domain.com:<password>@smtp.office365.com:587/?starttls=true&ssl=false' \
  -n airflow
```

### 3.2. SMTP user/password (cấu hình SMTP core)

```bash
kubectl create secret generic airflow-smtp \
  --from-literal=email_user="<smtp-user>" \
  --from-literal=email_password="<smtp-password>" \
  -n airflow
```

## 4 Custom

### 4.1 webserver_config.py

Simple Authorization đơn giản <br>
current: đăng nhập check AppRoles config trên Azure -> Tạo Roles Airflow <br>
vd (AppRoles) `airflow_team1` -> `airflow_team1` (role airflow) <br>

default mapping special roles Azure Roles -> Airflow Roles
```sh
  `airflow_admin` -> `Admin`
  `airflow_op` -> `Op`
  `airflow_developer` -> `User`
```
### 4.2 airflow_local.settings.py
ràng buộc DAG và task policy
custom 2 hàm

```python
from airflow.sdk import DAG
from airflow.sdk.bases.operator import BaseOperator

def dag_policy(dag : DAG):

def task_policy(task: BaseOperator) -> None:
```

### 4.3 azure.auth.py (multi-team: enable)

Custom Authen team login Azure (files/auth)

### 4.4 email_templates (smtp default)
