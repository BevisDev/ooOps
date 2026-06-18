# Longhorn (Helm)

version: 1.12.0

Thư mục này chứa file values cho [Longhorn](https://longhorn.io/) — CSI storage phân tán trên Kubernetes, cung cấp `StorageClass` (mặc định thường là `longhorn`) dùng bởi các workload khác trong repo (ví dụ Vault dùng `storageClass: longhorn`).

## Điều kiện cluster (tóm tắt)

- Cài **open-iscsi** (và dịch vụ `iscsid` chạy) trên **mọi node** sẽ chạy replica/engine.
- Mount helper: `nfs-common` / `nfs-utils` tùy distro (cần cho RWX qua share manager).
- Kiểm tra thêm theo [installation requirements](https://longhorn.io/docs/latest/deploy/install/#installation-requirements) của phiên bản bạn chọn.

## Tài liệu tham khảo

- [Chart](http://artifacthub.io/packages/helm/longhorn/longhorn)
- [Longhorn — Install với Helm](https://longhorn.io/docs/latest/deploy/install/install-with-helm/)
- [Chart longhorn (charts.longhorn.io)](https://github.com/longhorn/longhorn/tree/master/chart)
