# CKA Practice Exam

**Certified Kubernetes Administrator** · 17 Tasks · 2 Hours · Pass: 66% · Kubernetes v1.34

---

## Exam Overview

| | |
|---|---|
| **Duration** | 2 hours |
| **Format** | 17 hands-on CLI tasks |
| **Passing Score** | 66% |
| **Open Book** | kubernetes.io/docs, kubernetes.io/blog |
| **Retakes** | 1 free retake included |

### Domain Weights

| Domain | Weight | Tasks |
|---|---|---|
| Troubleshooting | 30% | 1–5 |
| Cluster Architecture, Installation & Configuration | 25% | 6–9 |
| Services & Networking | 20% | 10–12 |
| Workloads & Scheduling | 15% | 13–15 |
| Storage | 10% | 16–17 |

---

# Troubleshooting — 30%

---

### Task 1 · Fix a NotReady Worker Node

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 7% | Hard | cluster1 | `kubectl config use-context k8s-c1` |

Node `node01` is in a **NotReady** state. SSH into the node, investigate, and bring it back to **Ready**. Ensure the fix persists across reboots.

**Solution:**

```bash
ssh node01
sudo systemctl status kubelet
sudo journalctl -u kubelet -n 50 --no-pager
sudo systemctl start kubelet
sudo systemctl enable kubelet
exit
kubectl get nodes
```

**Verify:** `kubectl get nodes | grep node01` → should show `Ready`

---

### Task 2 · Identify the Highest CPU Pod

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 6% | Hard | cluster2 | `kubectl config use-context k8s-c2` |

Find the pod consuming the most CPU across **all namespaces**. Write the result to `/opt/KUTR00101/pod.txt` in the format `<namespace>/<pod-name>`.

**Solution:**

```bash
kubectl top pods -A --sort-by=cpu
# Take the first result
echo "kube-system/metrics-heavy-pod" > /opt/KUTR00101/pod.txt
```

**Verify:** `cat /opt/KUTR00101/pod.txt`

---

### Task 3 · Fix a Broken Deployment

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 6% | Hard | cluster1 | `kubectl config use-context k8s-c1` |

Deployment `web-app` in namespace `production` shows 0/3 pods running. Fix it **in place** — do not delete and recreate.

**Solution:**

```bash
kubectl describe deployment web-app -n production
# Look for image pull errors — common typo: "ngnix" instead of "nginx"

kubectl set image deployment/web-app nginx=nginx:latest -n production
kubectl get pods -n production -l app=web-app
```

**Verify:** `kubectl get deployment web-app -n production` → `3/3 READY`

---

### Task 4 · Troubleshoot Service Endpoints

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 6% | Medium | cluster3 | `kubectl config use-context k8s-c3` |

Service `api-svc` in namespace `backend` has **no endpoints**, but pods with label `app=api-server` are running. Fix the service. Do not delete the pods.

**Solution:**

```bash
kubectl get svc api-svc -n backend -o yaml | grep -A5 selector
kubectl get pods -n backend --show-labels
# Selector mismatch: service has "api-service", pods have "api-server"

kubectl patch svc api-svc -n backend \
  --type='json' \
  -p='[{"op":"replace","path":"/spec/selector/app","value":"api-server"}]'
```

**Verify:** `kubectl get endpoints api-svc -n backend` → should show pod IPs

---

### Task 5 · Fix a Broken kube-apiserver

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Hard | cluster2 | `ssh cluster2-controlplane` |

The kube-apiserver on `cluster2` is down. SSH into the control plane and fix the static pod manifest.

**Solution:**

```bash
ssh cluster2-controlplane
cat /etc/kubernetes/manifests/kube-apiserver.yaml
sudo crictl ps -a | grep apiserver
sudo crictl logs <container-id>

# Fix the error in the manifest (wrong port, cert path, or flag typo)
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Wait 30–60s for kubelet to restart the pod
exit
kubectl get nodes
```

**Verify:** `kubectl get nodes` → all nodes should respond

---

# Cluster Architecture, Installation & Configuration — 25%

---

### Task 6 · RBAC — ClusterRole and ClusterRoleBinding

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 7% | Hard | cluster1 | `kubectl config use-context k8s-c1` |

Create ClusterRole `pod-reader` allowing **get, watch, list** on pods. Bind it to ServiceAccount `dashboard-sa` in `kube-system` via ClusterRoleBinding `pod-reader-binding`.

**Solution:**

```bash
kubectl create clusterrole pod-reader \
  --verb=get,watch,list --resource=pods

kubectl create clusterrolebinding pod-reader-binding \
  --clusterrole=pod-reader \
  --serviceaccount=kube-system:dashboard-sa
```

**Verify:** `kubectl auth can-i list pods --as=system:serviceaccount:kube-system:dashboard-sa` → `yes`

---

### Task 7 · Backup and Restore etcd

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 8% | Hard | cluster3 | `ssh cluster3-controlplane` |

**Backup** etcd to `/opt/etcd-backup.db`. Then **restore** from `/opt/etcd-backup-previous.db` to `/var/lib/etcd-restored`.

Certs: CA `/etc/kubernetes/pki/etcd/ca.crt`, cert `server.crt`, key `server.key`

**Solution:**

```bash
ssh cluster3-controlplane

# Backup
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify backup
ETCDCTL_API=3 etcdctl snapshot status /opt/etcd-backup.db --write-table

# Restore
ETCDCTL_API=3 etcdctl snapshot restore \
  /opt/etcd-backup-previous.db \
  --data-dir=/var/lib/etcd-restored

# Update etcd manifest to point to restored data
sudo vi /etc/kubernetes/manifests/etcd.yaml
# Change hostPath: /var/lib/etcd → /var/lib/etcd-restored
```

**Verify:** `ls -la /var/lib/etcd-restored/` → directory should exist with data

---

### Task 8 · Upgrade Control Plane to v1.32.0

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 7% | Hard | cluster1 | `ssh cluster1-controlplane` |

Upgrade **only** the control plane from v1.31.0 to v1.32.0. Do not upgrade worker nodes.

**Solution:**

```bash
kubectl drain cluster1-controlplane \
  --ignore-daemonsets --delete-emptydir-data

ssh cluster1-controlplane
sudo apt-get update
sudo apt-get install -y kubeadm=1.32.0-1.1
sudo kubeadm upgrade apply v1.32.0 --yes
sudo apt-get install -y kubelet=1.32.0-1.1 kubectl=1.32.0-1.1
sudo systemctl daemon-reload
sudo systemctl restart kubelet

exit
kubectl uncordon cluster1-controlplane
```

**Verify:** `kubectl get nodes` → control plane shows `v1.32.0`

---

### Task 9 · ServiceAccount with Role and RoleBinding

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Medium | cluster1 | `kubectl config use-context k8s-c1` |

In namespace `app-team1`:
1. Create ServiceAccount `cicd-token`
2. Create Role `cicd-role` — **create, delete** on Deployments, StatefulSets, DaemonSets
3. Create RoleBinding `cicd-role-binding` binding the role to the SA

**Solution:**

```bash
kubectl create serviceaccount cicd-token -n app-team1

kubectl create role cicd-role -n app-team1 \
  --verb=create,delete \
  --resource=deployments,statefulsets,daemonsets

kubectl create rolebinding cicd-role-binding -n app-team1 \
  --role=cicd-role \
  --serviceaccount=app-team1:cicd-token
```

**Verify:** `kubectl auth can-i create deployments --as=system:serviceaccount:app-team1:cicd-token -n app-team1` → `yes`

---

# Services & Networking — 20%

---

### Task 10 · Create a NetworkPolicy

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 7% | Hard | cluster1 | `kubectl config use-context k8s-c1` |

Create NetworkPolicy `allow-port-from-namespace` in namespace `internal`:
- Applies to **all pods** (empty podSelector)
- Allow ingress only from namespaces labeled `project=trusted` on TCP **8080**
- Deny all other ingress
- Allow all egress

**Solution:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-port-from-namespace
  namespace: internal
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          project: trusted
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - {}
```

```bash
kubectl apply -f netpol.yaml
```

**Verify:** `kubectl describe netpol allow-port-from-namespace -n internal`

---

### Task 11 · Expose via Service and Ingress

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 7% | Medium | cluster2 | `kubectl config use-context k8s-c2` |

Deployment `web-frontend` runs in `web-ns` on port 80.

1. Create ClusterIP Service `web-frontend-svc` (port 80 → 80)
2. Create Ingress `web-ingress`: class `nginx`, host `app.internal.com`, path `/webapp` (Prefix), rewrite-target `/`

**Solution:**

```bash
kubectl expose deployment web-frontend -n web-ns \
  --name=web-frontend-svc --port=80 --target-port=80
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  namespace: web-ns
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.internal.com
    http:
      paths:
      - path: /webapp
        pathType: Prefix
        backend:
          service:
            name: web-frontend-svc
            port:
              number: 80
```

**Verify:** `kubectl get ingress web-ingress -n web-ns`

---

### Task 12 · Service DNS Resolution

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 6% | Medium | cluster1 | `kubectl config use-context k8s-c1` |

1. Create deployment `nginx-dns` in `dns-test` (nginx:1.25, 2 replicas)
2. Expose as ClusterIP Service `nginx-dns-svc` on port 80
3. Verify DNS and save FQDN to `/opt/dns-output.txt`

**Solution:**

```bash
kubectl create deployment nginx-dns -n dns-test \
  --image=nginx:1.25 --replicas=2

kubectl expose deployment nginx-dns -n dns-test \
  --name=nginx-dns-svc --port=80 --target-port=80

kubectl run dns-test-pod --rm -it -n dns-test \
  --image=busybox:1.36 --restart=Never \
  -- nslookup nginx-dns-svc.dns-test.svc.cluster.local

echo "nginx-dns-svc.dns-test.svc.cluster.local" > /opt/dns-output.txt
```

**Verify:** `cat /opt/dns-output.txt` → `nginx-dns-svc.dns-test.svc.cluster.local`

---

# Workloads & Scheduling — 15%

---

### Task 13 · Pod Scheduling with nodeAffinity

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Medium | cluster1 | `kubectl config use-context k8s-c1` |

Create pod `node-affinity-pod` (nginx:1.25) that schedules **only** on nodes with `disktype=ssd` using `requiredDuringSchedulingIgnoredDuringExecution`.

**Solution:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: node-affinity-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
  containers:
  - name: nginx
    image: nginx:1.25
```

**Verify:** `kubectl get pod node-affinity-pod -o wide`

---

### Task 14 · Deployment with Resources and Rolling Update

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Medium | cluster2 | `kubectl config use-context k8s-c2` |

Create Deployment `rate-limiter` in `apps`:
- Image `nginx:1.25-alpine`, 4 replicas, port 80
- Requests: CPU 100m, Memory 64Mi · Limits: CPU 200m, Memory 128Mi
- Strategy: maxSurge=2, maxUnavailable=1

Then update to `nginx:1.26-alpine` with `--record`.

**Solution:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rate-limiter
  namespace: apps
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
  selector:
    matchLabels:
      app: rate-limiter
  template:
    metadata:
      labels:
        app: rate-limiter
    spec:
      containers:
      - name: nginx
        image: nginx:1.25-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
```

```bash
kubectl apply -f rate-limiter.yaml
kubectl set image deployment/rate-limiter nginx=nginx:1.26-alpine -n apps --record
```

**Verify:** `kubectl rollout history deployment/rate-limiter -n apps`

---

### Task 15 · Taints, Tolerations, and nodeName

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Medium | cluster1 | `kubectl config use-context k8s-c1` |

1. Taint `node02`: `environment=production:NoSchedule`
2. Create pod `prod-pod` (redis:7-alpine) that tolerates the taint and runs on `node02`

**Solution:**

```bash
kubectl taint nodes node02 environment=production:NoSchedule
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: prod-pod
spec:
  nodeName: node02
  tolerations:
  - key: "environment"
    operator: "Equal"
    value: "production"
    effect: "NoSchedule"
  containers:
  - name: redis
    image: redis:7-alpine
```

**Verify:** `kubectl get pod prod-pod -o wide` → Running on `node02`

---

# Storage — 10%

---

### Task 16 · Create PV, PVC, and Mount in Pod

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Medium | cluster1 | `kubectl config use-context k8s-c1` |

1. PV `task-pv`: 500Mi, RWO, hostPath `/mnt/data/task`, class `manual`
2. PVC `task-pvc` in `storage`: 200Mi, RWO, class `manual`
3. Pod `task-storage-pod` in `storage`: busybox:1.36, `sleep 3600`, mount PVC at `/data`

**Solution:**

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: task-pv
spec:
  capacity:
    storage: 500Mi
  accessModes: [ReadWriteOnce]
  hostPath:
    path: /mnt/data/task
  storageClassName: manual
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: task-pvc
  namespace: storage
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 200Mi
  storageClassName: manual
---
apiVersion: v1
kind: Pod
metadata:
  name: task-storage-pod
  namespace: storage
spec:
  containers:
  - name: busybox
    image: busybox:1.36
    command: ["sleep", "3600"]
    volumeMounts:
    - name: task-volume
      mountPath: /data
  volumes:
  - name: task-volume
    persistentVolumeClaim:
      claimName: task-pvc
```

**Verify:** `kubectl get pv task-pv` → Bound · `kubectl get pod task-storage-pod -n storage` → Running

---

### Task 17 · Expand a PVC and Mount in Pod

| Weight | Difficulty | Cluster | Context |
|---|---|---|---|
| 5% | Medium | cluster2 | `kubectl config use-context k8s-c2` |

PVC `logs-pvc` in `logging` is 1Gi. Expand to **3Gi** (StorageClass supports expansion). Then create pod `log-writer` (busybox:1.36) that writes `date` to `/logs/app.log` every 5s using the PVC.

**Solution:**

```bash
kubectl patch pvc logs-pvc -n logging \
  -p '{"spec":{"resources":{"requests":{"storage":"3Gi"}}}}'
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: log-writer
  namespace: logging
spec:
  containers:
  - name: writer
    image: busybox:1.36
    command: ["sh", "-c", "while true; do date >> /logs/app.log; sleep 5; done"]
    volumeMounts:
    - name: log-vol
      mountPath: /logs
  volumes:
  - name: log-vol
    persistentVolumeClaim:
      claimName: logs-pvc
```

**Verify:** `kubectl get pvc logs-pvc -n logging` → 3Gi · `kubectl get pod log-writer -n logging` → Running

---

# Quick Reference

### Aliases — Set These First

```bash
alias k=kubectl
alias kn='kubectl config set-context --current --namespace'
export do='--dry-run=client -o yaml'
```

### Generate YAML Fast

```bash
kubectl run nginx --image=nginx $do > pod.yaml
kubectl create deployment nginx --image=nginx $do > deploy.yaml
kubectl create service clusterip my-svc --tcp=80:80 $do > svc.yaml
kubectl create ingress my-ingress --rule="host/path=svc:80" $do > ingress.yaml
```

### Troubleshooting Flow

```bash
kubectl get pods -A                        # Overview
kubectl describe pod <name> -n <ns>        # Details + events
kubectl logs <pod> -n <ns>                 # App logs
kubectl logs <pod> -n <ns> --previous      # Crashed container logs
kubectl exec -it <pod> -n <ns> -- sh       # Shell in
kubectl get events -n <ns> --sort-by='.lastTimestamp'
```

### etcd Backup

```bash
ETCDCTL_API=3 etcdctl snapshot save /path/backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

### Cluster Upgrade

```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
apt-get install -y kubeadm=X.Y.Z-1.1
kubeadm upgrade apply vX.Y.Z
apt-get install -y kubelet=X.Y.Z-1.1 kubectl=X.Y.Z-1.1
systemctl daemon-reload && systemctl restart kubelet
kubectl uncordon <node>
```

---

**Tip:** If stuck for more than 7 minutes, flag the task and move on. Good luck! 🎯
