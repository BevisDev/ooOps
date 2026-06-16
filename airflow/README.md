# Apache Airflow (Helm)

Hướng dẫn tạo **secret key** và **connection** trước khi deploy Airflow.

> Namespace mặc định: `airflow`  
> File cấu hình: `values-prod.yaml`

## 1. Secret key (bắt buộc)

Các secret sau phải tồn tại trong Kubernetes **trước** khi `helm install/upgrade`. Tên secret khớp với `values-prod.yaml`.

### 1.1. Fernet key

Dùng để mã hóa password trong Airflow (Connection, Variable).

```bash
# Tạo key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

kubectl create secret generic airflow-fernet-key \
  --from-literal=fernet-key="<FERNET_KEY>" \
  -n airflow
```

> **Lưu ý:** Fernet key phải giữ nguyên sau khi deploy. Đổi key sẽ không giải mã được dữ liệu cũ.

### 1.2. API secret key & JWT secret

Dùng cho Airflow 3+ (API server, session, JWT).

```bash
kubectl create secret generic airflow-api-secret-key \
  --from-literal=api-secret-key="$(openssl rand -base64 32)" \
  -n airflow

kubectl create secret generic airflow-jwt-secret \
  --from-literal=jwt-secret="$(openssl rand -base64 32)" \
  -n airflow
```

### 1.3. Database metadata

```bash
kubectl create secret generic airflow-metadata-secret \
  --from-literal=connection="postgresql+psycopg2://<user>:<password>@<host>:5432/<database>" \
  -n airflow
```

### 1.4. Azure OIDC (đăng nhập UI)

```bash
kubectl create secret generic airflow-azure-oidc \
  --from-literal=tenant-id="<AZURE_TENANT_ID>" \
  --from-literal=client-id="<AZURE_CLIENT_ID>" \
  --from-literal=client-secret="<AZURE_CLIENT_SECRET>" \
  -n airflow
```

### 1.5. SSH key (git-sync DAGs)

```bash
kubectl create secret generic airflow-ssh-secret \
  --from-file=gitSshKey=<path-to-private-key> \
  -n airflow
```

---

## 2. Connection qua Kubernetes Secret

Trong `values-prod.yaml`, connection được inject vào pod qua biến môi trường `AIRFLOW_CONN_<CONN_ID>`.

| Conn Id (trong DAG/UI) | K8s Secret | Key | Biến môi trường |
|------------------------|------------|-----|-----------------|
| `minio_conn` | `airflow-minio-conn` | `conn` | `AIRFLOW_CONN_MINIO_CONN` |
| `git_team1` | `airflow-git-conn-team1` | `conn` | `AIRFLOW_CONN_GIT_TEAM1` |
| `git_team2` | `airflow-git-conn-team2` | `conn` | `AIRFLOW_CONN_GIT_TEAM2` |
| `smtp_default` | `airflow-smtp-conn` | `conn` | `AIRFLOW_CONN_SMTP_DEFAULT` |

### 2.1. Tạo secret connection

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

### 2.2. SMTP user/password (cấu hình SMTP core)

```bash
kubectl create secret generic airflow-smtp \
  --from-literal=email_user="<smtp-user>" \
  --from-literal=email_password="<smtp-password>" \
  -n airflow
```

### 2.3. Thêm connection mới

1. Tạo K8s secret chứa key `conn`.
2. Thêm vào `values-prod.yaml` mục `secret`:

```yaml
secret:
  - envName: AIRFLOW_CONN_MY_CONN
    secretName: airflow-my-conn
    secretKey: conn
```

3. Chạy `helm upgrade` để pod nhận biến môi trường mới.

**Quy tắc đặt tên:** Conn Id `my_conn` → biến môi trường `AIRFLOW_CONN_MY_CONN` (viết hoa, dấu `-` thành `_`).

---

## 3. Connection / Variable trên UI

Truy cập: `https://airflowdp.company.com.vn`

### 3.1. Tạo Connection

1. Vào **Admin → Connections** (hoặc **Browse → Connections**).
2. Bấm **+** (Add Connection).
3. Điền:
   - **Connection Id**: tên dùng trong DAG, ví dụ `postgres_default`
   - **Connection Type**: `postgres`, `http`, `aws`, `smtp`, ...
   - **Host**, **Login**, **Password**, **Port**, **Schema**, **Extra** (nếu cần)
4. Bấm **Save**.

Trong DAG dùng:

```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

hook = PostgresHook(postgres_conn_id="postgres_default")
```

### 3.2. Tạo Variable

1. Vào **Admin → Variables**.
2. Bấm **+**, nhập **Key** và **Val**.
3. Bấm **Save**.

Trong DAG:

```python
from airflow.models import Variable

value = Variable.get("my_key")
```

---

## 4. Khi nào dùng Secret K8s vs UI?

| Cách | Phù hợp khi |
|------|-------------|
| **K8s Secret** (`AIRFLOW_CONN_*`) | Connection dùng chung toàn cluster, quản lý qua GitOps/Helm, không muốn lưu trên UI |
| **UI** | Thêm/sửa nhanh khi dev, connection chỉ dùng thử hoặc do team vận hành quản lý trực tiếp |

> Connection tạo trên UI cũng được mã hóa bằng Fernet key. Đảm bảo `airflow-fernet-key` đã tạo đúng trước khi deploy.

---

## 5. Kiểm tra nhanh

```bash
# Xem secret đã tạo
kubectl get secret -n airflow | grep airflow-

# Xem connection trong pod (ví dụ scheduler)
kubectl exec -n airflow deploy/airflow-scheduler -- env | grep AIRFLOW_CONN
```
