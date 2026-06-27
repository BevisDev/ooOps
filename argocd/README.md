# Argo CD (Helm)

- version: 3.4.2
- kubeVersion: '>=1.25.0-0'
- redirect_uri: https://domain/auth/callback

## Images:
    1. quay.io/argoproj/argocd:v3.4.2


## Secrets:

Create `argocd-secret`
```kubectl
kubectl create secret generic argocd-secret -n argocd \
  --from-literal=server.secretkey="$(openssl rand -base64 32)"
```

## Document

- [Helm Chart](https://artifacthub.io/packages/helm/argo/argo-cd)
- [Document](https://argo-cd.readthedocs.io/en/stable/)

