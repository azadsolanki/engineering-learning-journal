# CKA Practice Questions — Scheduling

> All tasks are hands-on. Write YAML from scratch unless stated otherwise. Use `kubectl` to verify.

---

**Q1. Assign a Pod to a specific node using nodeName**
Create a Pod named `pinned` using the `nginx` image. Force it to run on a specific node by setting `nodeName` directly in the spec. Verify it lands on the correct node.

```bash
kubectl get pod pinned -o wide    # check NODE column
```

---

**Q2. Schedule using nodeSelector**
Label a node with `disk=ssd`. Create a Pod named `ssd-app` using `nginx` that only schedules on nodes with that label.

```bash
kubectl label node <node-name> disk=ssd
kubectl get pod ssd-app -o wide    # confirm it landed on the labelled node
```

---

**Q3. Add a Taint to a node and tolerate it**
Add a taint to a node:
```bash
kubectl taint nodes <node-name> env=prod:NoSchedule
```
Create a Pod named `prod-app` using `nginx` with a toleration for that taint. Then create a second Pod named `dev-app` without the toleration — verify `dev-app` does not schedule on the tainted node.

---

**Q4. Remove a Taint from a node**
Remove the taint added in Q3 and verify previously pending Pods now schedule.

```bash
kubectl taint nodes <node-name> env=prod:NoSchedule-    # note the trailing -
```

---

**Q5. Set resource requests and limits**
Create a Pod named `resource-pod` using `nginx` with the following resource constraints:
- CPU request: `250m`, limit: `500m`
- Memory request: `64Mi`, limit: `128Mi`

Verify with:
```bash
kubectl describe pod resource-pod    # check Requests and Limits section
```

---

**Q6. Create a Pod with node Affinity**
Create a Pod named `affinity-pod` using `nginx` that uses `requiredDuringSchedulingIgnoredDuringExecution` node affinity to only schedule on nodes labeled `zone=us-east`.

```bash
kubectl label node <node-name> zone=us-east
```

*Key distinction:*
| Affinity type | Behaviour |
|---|---|
| `required...` | Hard rule — Pod stays Pending if no match |
| `preferred...` | Soft rule — tries to match, schedules anyway |

---

**Q7. Cordon and Drain a node**
Cordon `node-2` so no new Pods schedule on it. Then drain it safely, evicting all Pods. Verify no Pods remain on the node.

```bash
kubectl cordon node-2
kubectl drain node-2 --ignore-daemonsets --delete-emptydir-data
kubectl get pods -o wide    # confirm no Pods on node-2
```

Uncordon when done:
```bash
kubectl uncordon node-2
```

---

**Q8. Troubleshoot a Pending Pod**
A Pod has been in `Pending` state for several minutes. Identify the reason and fix it.

*Hint: check these common causes:*
- No node matches the `nodeSelector` or affinity rule
- All nodes are tainted and Pod has no toleration
- Insufficient CPU or memory on available nodes
- Node is cordoned

```bash
kubectl describe pod <pod-name>    # look at Events section at the bottom
kubectl get nodes                  # check node status
kubectl describe node <node-name>  # check Taints and Allocatable resources
```

---

**Q9. Schedule a DaemonSet on all nodes**
Create a DaemonSet named `monitor` using the `busybox` image with command `sleep 3600`. Verify a Pod runs on every node including the control plane.

*To schedule on control plane nodes, add a toleration:*
```yaml
tolerations:
- key: node-role.kubernetes.io/control-plane
  operator: Exists
  effect: NoSchedule
```

```bash
kubectl get pods -o wide    # one Pod per node
```

---

**Q10. Full scheduling scenario**
Complete the following end-to-end task:
1. Label `node-1` with `tier=frontend` and `node-2` with `tier=backend`
2. Taint `node-2` with `team=backend:NoSchedule`
3. Create a Deployment named `frontend` with 2 replicas using `nginx` — must only schedule on `tier=frontend` nodes using nodeSelector
4. Create a Deployment named `backend` with 2 replicas using `nginx` — must only schedule on `tier=backend` nodes using nodeSelector, with a toleration for the taint
5. Verify each Deployment's Pods land on the correct nodes

```bash
kubectl get pods -o wide    # confirm node placement for both deployments
```

---

## Quick Reference

| Concept | Hard rule? | Removes existing Pods? |
|---|---|---|
| `nodeName` | Yes | No |
| `nodeSelector` | Yes | No |
| `Taint + NoSchedule` | Yes | No |
| `Taint + NoExecute` | Yes | Yes — evicts running Pods |
| `Affinity (required)` | Yes | No |
| `Affinity (preferred)` | No | No |
| `cordon` | Yes | No |
| `drain` | Yes | Yes — evicts running Pods |

*Tip: `NoSchedule` prevents new Pods from landing. `NoExecute` also evicts Pods already running — know this distinction cold.*
