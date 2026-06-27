# Vault Secret

Helm chart khai báo **VaultAuth** và **VaultStaticSecret** (VSO) — đồng bộ secret tĩnh từ Vault KV sang Kubernetes Secret.

## Kiến trúc

```text
Vault (dp-vault)
  └── KV v2 mount "secret"
        ├── dockerhub
        ├── git-ssh
        └── gitlab-runner/runner-*

VSO (vault-secrets-operator, namespace vault)
  └── VaultConnection + VaultAuthGlobal

dp-secrets (chart này)
  └── ServiceAccount vault-sa + VaultAuth (per namespace)
  └── VaultStaticSecret (per secret)
        └── Kubernetes Secret
```


## Quy ước đặt tên (quan trọng)

| Thành phần | Tên mặc định | Ghi chú |
|------------|--------------|---------|
| ServiceAccount | `vault-sa` | JWT dùng để login Vault — **phải khớp** `bound_service_account_names` trên Vault role |
| VaultAuth CR | `vault-auth` | `vaultAuthRef` trong `VaultStaticSecret` trỏ **tên CR này**, không phải tên SA |
| Vault K8s auth role | `readonly` | Cấu hình trên Vault |
| KV mount | `secret` | `defaults.mount` |

## Values

### `vaultAuthNamespaces`

Tạo `ServiceAccount` + `VaultAuth` cho từng namespace cần sync secret.

```yaml
vaultAuthNamespaces:
  - namespace: gitlab-runner
    enabled: true
    kubernetes:
      role: readonly
  - namespace: airflow3
    enabled: false
    kubernetes:
      role: readonly
```

Namespace phải có entry ở đây **trước** khi thêm `staticSecrets` trong namespace đó.

### `defaults`

Áp dụng cho mọi `staticSecrets` trừ khi entry override.

```yaml
defaults:
  vaultAuthRef: vault-auth  
  type: kv-v2              
  mount: secret
  refreshAfter: 24h
```

### `staticSecrets`

```yaml
staticSecrets:
  - name: dockerhub-regcred          # tên VaultStaticSecret CR
    namespace: gitlab-runner
    enabled: true
    path: dockerhub                  # path trên Vault: secret/data/dockerhub
    transformation: dockerconfigjson
    destination:
      name: dockerhub-regcred        # tên K8s Secret (mặc định = name nếu bỏ qua)
      type: kubernetes.io/dockerconfigjson

  - name: git-ssh
    namespace: gitlab-runner
    enabled: true
    path: git-ssh
    # không transformation → sync raw key 1:1 (Opaque)

  - name: runner-governance-secret
    namespace: gitlab-runner
    enabled: true
    path: gitlab-runner/runner-governance
```

| Field | Bắt buộc | Mô tả |
|-------|----------|-------|
| `name` | Có | Tên `VaultStaticSecret` CR |
| `namespace` | Có | Namespace deploy CR và Secret đích |
| `path` | Có | Path KV (không gồm mount) |
| `enabled` | Không | `false` = không render entry (mặc định `true`) |
| `destination.name` | Không | Tên K8s Secret (mặc định = `name`) |
| `destination.type` | Không | Loại K8s Secret (`kubernetes.io/dockerconfigjson` cho pull secret) |
| `transformation` | Không | Preset: `dockerconfigjson` |

### Hai field `type` — không nhầm

| Field trong manifest | Ý nghĩa | Giá trị |
|----------------------|---------|---------|
| `spec.type` | Secret engine Vault | `kv-v2` (từ `defaults.type`) |
| `spec.destination.type` | Loại K8s Secret | `kubernetes.io/dockerconfigjson`, … |

**Không** đặt `kubernetes.io/dockerconfigjson` ở root entry — sẽ lỗi sync.

## Transformation

### Docker Hub (`dockerconfigjson`)

Vault KV keys: `registry`, `username`, `password`, `email`.

Preset ghép thành key `.dockerconfigjson`, loại bỏ field gốc:

```yaml
transformation: dockerconfigjson
destination:
  name: dockerhub-regcred
  type: kubernetes.io/dockerconfigjson
```

### Secret thường (token, SSH key, …)

Không cần transformation — key Vault copy thẳng sang K8s Secret (`Opaque`).

| Vault KV keys | K8s Secret keys |
|---------------|-----------------|
| `ssh-privatekey`, `known_hosts` | cùng tên |
| `token` | `token` |

### Lọc key (tuỳ chọn)

```yaml
destination:
  name: my-secret
  transformation:
    excludeRaw: true
    includes:
      - "^token$"
```
