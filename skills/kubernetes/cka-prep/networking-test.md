# CKA Practice Questions — Networking

> All tasks are hands-on. Write YAML from scratch unless stated otherwise. Use `kubectl` to verify.

---

**Q1. Create a ClusterIP Service**
Create a Deployment named `web` with 3 replicas using the `nginx` image. Expose it internally with a `ClusterIP` Service named `web-svc` on port `80`. Verify the Service has endpoints.

```bash
kubectl get endpoints web-svc
```

---

**Q2. Create a NodePort Service**
Expose the `web` Deployment from Q1 using a `NodePort` Service named `web-nodeport` on port `80`, mapped to node port `30080`. Verify you can reach it from outside the cluster.

```bash
curl http://<node-ip>:30080
```

---

**Q3. Create a LoadBalancer Service**
Expose a Deployment named `api` using a `LoadBalancer` Service named `api-lb` on port `8080`. Describe the Service and identify the external IP field.

```bash
kubectl get svc api-lb     # watch for EXTERNAL-IP
```

---

**Q4. DNS resolution between Pods**
Create two Pods — `client` and `server` — both using `busybox` with `sleep 3600`. Create a ClusterIP Service named `server-svc` exposing the `server` Pod on port `80`.
From the `client` Pod, verify DNS resolution:

```bash
kubectl exec -it client -- nslookup server-svc
kubectl exec -it client -- nslookup server-svc.default.svc.cluster.local
```

---

**Q5. Create a NetworkPolicy — deny all ingress**
Create a `NetworkPolicy` named `deny-all` in the `default` namespace that denies all ingress traffic to all Pods. Verify by attempting to reach a Pod from another Pod.

```yaml
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

---

**Q6. Create a NetworkPolicy — allow specific traffic**
Create a NetworkPolicy named `allow-web` that allows ingress traffic to Pods labeled `app=web` only from Pods labeled `app=frontend` on port `80`. All other ingress should be denied.

---

**Q7. Troubleshoot a Service with no endpoints**
A Service exists but `kubectl get endpoints <svc-name>` returns no endpoints. Identify and fix the issue.

*Hint: check these common causes:*
- Label selector on Service doesn't match Pod labels
- Pod is not in `Running` state
- Port mismatch between Service and container

```bash
kubectl describe svc <svc-name>       # check Selector field
kubectl get pods --show-labels        # compare labels
```

---

**Q8. Expose a Pod on a specific port using a Service**
A Pod named `myapp` is running with container port `8080` and label `app=myapp`. Create a ClusterIP Service named `myapp-svc` that forwards traffic from port `80` to the Pod's port `8080`.

*Key fields to get right:*
```yaml
port: 80          # Service port
targetPort: 8080  # Container port
```

---

**Q9. Identify the CNI plugin in use**
Without looking at cluster documentation, identify which CNI plugin is running in the cluster and verify it is healthy.

```bash
kubectl get pods -n kube-system          # look for calico, flannel, weave etc.
ls /etc/cni/net.d/                       # CNI config on the node
```

---

**Q10. Full networking scenario**
Complete the following end-to-end task:
1. Create a Deployment named `backend` with 2 replicas using `nginx`, labeled `app=backend`
2. Expose it with a ClusterIP Service named `backend-svc` on port `80`
3. Create a NetworkPolicy named `backend-policy` that allows ingress to `app=backend` Pods only from Pods labeled `app=frontend` on port `80`
4. Create a `frontend` Pod using `busybox` with label `app=frontend` — verify it can reach `backend-svc`
5. Create a `blocked` Pod using `busybox` with label `app=other` — verify it cannot reach `backend-svc`

```bash
# Should succeed
kubectl exec -it frontend -- wget -qO- http://backend-svc

# Should fail / timeout
kubectl exec -it blocked -- wget -qO- http://backend-svc --timeout=5
```

---

## Quick Reference

| Service Type | Reachable from | Use case |
|---|---|---|
| `ClusterIP` | Inside cluster only | Internal communication |
| `NodePort` | Outside via node IP + port | Dev/testing |
| `LoadBalancer` | Outside via external IP | Production cloud |
| `ExternalName` | DNS alias to external service | Legacy/external integration |

*Tip: Know the DNS format by heart — `<service>.<namespace>.svc.cluster.local`. It appears in almost every networking question.*
