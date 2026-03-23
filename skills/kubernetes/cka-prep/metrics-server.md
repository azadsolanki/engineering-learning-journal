# Metrics Server

## What & Why
Metrics Server replaced **Heapster** (deprecated) as the standard cluster monitoring tool. It collects CPU/memory metrics from nodes and pods, and exposes them via `/apis/metrics.k8s.io/` — enabling **HPA (Horizontal Pod Autoscaler)** to scale workloads automatically.

---

## Installation

### 1. Download
```bash
wget https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 2. Edit — add the insecure TLS flag
```bash
vi components.yaml
```
```yaml
containers:
  - args:
    - --cert-dir=/tmp
    - --secure-port=4443
    - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
    - --kubelet-use-node-status-port
    - --metric-resolution=15s
    - --kubelet-insecure-tls    # <--- REQUIRED
```

### 3. Apply
```bash
kubectl apply -f components.yaml
```

### 4. Verify
```bash
kubectl -n kube-system get pods    # confirm metrics-server pod is Running
kubectl top nodes                  # node CPU/memory usage
kubectl top pods                   # pod CPU/memory usage
```

---

## CKA Tips
- Metrics Server is **not** installed by default — you must add it
- Without `--kubelet-insecure-tls` the pod will crash in most lab environments
- `kubectl top` only works **after** Metrics Server is running
- HPA **depends** on Metrics Server — if top doesn't work, HPA won't either
