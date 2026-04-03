# CKA Practice Questions — Miscellaneous

> Mixed topics. Reflects the real exam format — one task per question, hands-on only.

---

**Q1. Upgrade kubeadm, kubelet and kubectl**
The cluster is running Kubernetes `v1.29`. Upgrade the control plane node to `v1.30`.

```bash
# Upgrade kubeadm
apt-get update
apt-get install -y kubeadm=1.30.0-00

# Plan and apply
kubeadm upgrade plan
kubeadm upgrade apply v1.30.0

# Upgrade kubelet and kubectl
apt-get install -y kubelet=1.30.0-00 kubectl=1.30.0-00
systemctl daemon-reload
systemctl restart kubelet

# Verify
kubectl get nodes    # control plane should show v1.30
```

---

**Q2. Create a Role and RoleBinding**
Create a Role named `pod-reader` in the `default` namespace that allows `get`, `list`, and `watch` on Pods. Bind it to a user named `jane` using a RoleBinding named `pod-reader-binding`.

```bash
# Verify jane's access
kubectl auth can-i get pods --as=jane
kubectl auth can-i delete pods --as=jane    # should be: no
```

---

**Q3. Create a ClusterRole and ClusterRoleBinding**
Create a ClusterRole named `node-reader` that allows `get`, `list`, and `watch` on nodes. Bind it to a ServiceAccount named `monitor-sa` in the `monitoring` namespace.

```bash
kubectl auth can-i get nodes \
  --as=system:serviceaccount:monitoring:monitor-sa    # should be: yes
```

---

**Q4. Create a Deployment and scale it**
Create a Deployment named `webapp` with 3 replicas using the `nginx:1.19` image. Scale it to 5 replicas without editing the manifest.

```bash
kubectl scale deployment webapp --replicas=5
kubectl get deployment webapp    # confirm READY shows 5/5
```

---

**Q5. Roll out an update and roll back**
Update the `webapp` Deployment from Q4 to use `nginx:1.21`. Verify the rollout, then roll back to the previous version.

```bash
kubectl set image deployment/webapp nginx=nginx:1.21
kubectl rollout status deployment/webapp
kubectl rollout history deployment/webapp
kubectl rollout undo deployment/webapp
kubectl rollout status deployment/webapp    # confirm rollback complete
```

---

**Q6. Create a Job**
Create a Job named `pi` that runs a single Pod using the `perl` image to compute pi to 2000 decimal places:

```bash
perl -Mbignum=bpi -wle 'print bpi(2000)'
```

Verify the Job completes successfully.

```bash
kubectl get job pi           # COMPLETIONS should be 1/1
kubectl logs job/pi          # view output
```

---

**Q7. Create a CronJob**
Create a CronJob named `date-printer` that runs every 2 minutes, using the `busybox` image to print the current date:

```bash
date
```

Verify a Job is created and completes on schedule.

```bash
kubectl get cronjob date-printer
kubectl get jobs --watch    # watch for new Job every 2 minutes
```

---

**Q8. Add a liveness probe**
Create a Pod named `health-pod` using the `nginx` image. Add an HTTP liveness probe that checks `GET /` on port `80` every `10` seconds, with an initial delay of `5` seconds. Verify the probe is configured.

```bash
kubectl describe pod health-pod    # check Liveness section
```

---

**Q9. Add a readiness probe**
Create a Pod named `ready-pod` using `nginx`. Add a readiness probe that checks for the existence of the file `/tmp/ready` using an `exec` command. The Pod should not receive traffic until the file exists.

```bash
# Make Pod ready
kubectl exec -it ready-pod -- touch /tmp/ready

# Verify
kubectl get pod ready-pod    # READY should change from 0/1 to 1/1
```

---

**Q10. Create a multi-container Pod with an init container**
Create a Pod named `init-pod` using `nginx` as the main container. Add an init container using `busybox` that creates the file `/work/index.html` with content `Hello from init`. Mount a shared `emptyDir` volume so the main container can serve the file.

```bash
kubectl exec -it init-pod -- cat /usr/share/nginx/html/index.html
# Expected: Hello from init
```

---

**Q11. Create a ConfigMap and inject it as env variables**
Create a ConfigMap named `app-env` with the following:
- `APP_COLOR=blue`
- `APP_MODE=production`

Create a Pod named `env-pod` using `busybox` with command `sleep 3600` that injects these values as environment variables. Verify inside the container.

```bash
kubectl exec -it env-pod -- env | grep APP
```

---

**Q12. Create a Secret and use it in a Pod**
Create a Secret named `db-creds` with:
- `username=admin`
- `password=supersecret`

Mount it into a Pod named `secret-pod` using `busybox` at `/etc/creds`. Verify both keys appear as files.

```bash
kubectl exec -it secret-pod -- ls /etc/creds
kubectl exec -it secret-pod -- cat /etc/creds/password
```

---

**Q13. Apply resource quotas to a namespace**
Create a namespace named `limited`. Apply a ResourceQuota named `compute-quota` that limits:
- Max Pods: `5`
- Max CPU requests: `1`
- Max memory requests: `1Gi`

Verify the quota is in effect.

```bash
kubectl describe quota compute-quota -n limited
```

---

**Q14. Use labels and selectors**
Create 3 Pods — `pod-a`, `pod-b`, `pod-c` — all using `nginx`. Label `pod-a` and `pod-b` with `env=prod`, and `pod-c` with `env=dev`. List only the `prod` Pods using a selector.

```bash
kubectl get pods -l env=prod         # should return pod-a and pod-b
kubectl get pods -l env!=prod        # should return pod-c
```

---

**Q15. Find and fix a broken Pod**
A Pod named `broken-pod` exists in the `default` namespace but is in `CrashLoopBackOff`. Investigate, identify the root cause, and fix it.

```bash
kubectl describe pod broken-pod     # check Events
kubectl logs broken-pod             # check container logs
kubectl logs broken-pod --previous  # check logs from last crash
```

*Common causes: wrong image name, bad command, missing ConfigMap or Secret, failing liveness probe.*

---

**Q16. Set a static pod on a worker node**
SSH into a worker node. Create a static Pod named `static-web` using `nginx` by placing a manifest in the kubelet's `staticPodPath` directory. Verify the Pod appears in the cluster.

```bash
# On the worker node
cat /var/lib/kubelet/config.yaml | grep staticPodPath
vi /etc/kubernetes/manifests/static-web.yaml

# From the control plane
kubectl get pods    # static-web-<node-name> should appear
```

---

**Q17. Identify and evict the highest CPU-consuming Pod**
Using the Metrics Server, find the Pod consuming the most CPU across all namespaces. Then delete it.

```bash
kubectl top pods -A --sort-by=cpu   # find the top consumer
kubectl delete pod <pod-name> -n <namespace>
```

---

## Topics Covered

| Q | Topic |
|---|---|
| Q1 | Cluster upgrade |
| Q2 | RBAC — Role + RoleBinding |
| Q3 | RBAC — ClusterRole + ServiceAccount |
| Q4 | Deployments + scaling |
| Q5 | Rollout + rollback |
| Q6 | Jobs |
| Q7 | CronJobs |
| Q8 | Liveness probe |
| Q9 | Readiness probe |
| Q10 | Init containers + shared volume |
| Q11 | ConfigMap as env variables |
| Q12 | Secrets as volume mount |
| Q13 | ResourceQuota |
| Q14 | Labels + selectors |
| Q15 | Troubleshooting CrashLoopBackOff |
| Q16 | Static Pods |
| Q17 | Metrics Server + top |

*Tip: In the real exam you have ~17 questions across 2 hours. Each question has a weight — RBAC, upgrades, and etcd tend to carry the most marks. Always read the question twice and check which cluster/namespace you need to be in before running any command.*
