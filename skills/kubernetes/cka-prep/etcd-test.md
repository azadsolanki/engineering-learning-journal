# CKA Practice Questions — etcd

> etcd questions on the CKA are almost always about backup and restore. Know the `etcdctl` commands cold.

---

**Q1. Check etcd health**
Verify the etcd cluster is healthy using `etcdctl`. Identify the endpoint, cert, key, and CA cert from the etcd static Pod manifest.

```bash
# Find etcd connection details
cat /etc/kubernetes/manifests/etcd.yaml

# Check health
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

---

**Q2. Check etcd member list**
List all members of the etcd cluster and identify the leader.

```bash
ETCDCTL_API=3 etcdctl member list \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

---

**Q3. Take an etcd snapshot (backup)**
Take a snapshot of the etcd datastore and save it to `/opt/etcd-backup.db`.

```bash
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

---

**Q4. Verify a snapshot**
Confirm the snapshot taken in Q3 is valid and check its metadata.

```bash
ETCDCTL_API=3 etcdctl snapshot status /opt/etcd-backup.db \
  --write-out=table
```

*Expected output includes: snapshot hash, revision, total keys, total size.*

---

**Q5. Restore an etcd snapshot**
Restore the snapshot from `/opt/etcd-backup.db` to a new data directory `/var/lib/etcd-restore`.

```bash
ETCDCTL_API=3 etcdctl snapshot restore /opt/etcd-backup.db \
  --data-dir=/var/lib/etcd-restore
```

After restoring, update the etcd static Pod manifest to point to the new data directory:

```bash
vi /etc/kubernetes/manifests/etcd.yaml
```

```yaml
volumes:
- hostPath:
    path: /var/lib/etcd-restore    # change from /var/lib/etcd
    type: DirectoryOrCreate
  name: etcd-data
```

Kubelet will automatically restart the etcd Pod. Verify:
```bash
kubectl get pods -n kube-system    # wait for etcd Pod to restart
kubectl get nodes                  # confirm cluster is responsive
```

---

**Q6. Locate etcd certificates**
Without looking at documentation, find all etcd certificate paths on the cluster.

```bash
cat /etc/kubernetes/manifests/etcd.yaml | grep -i cert
ls /etc/kubernetes/pki/etcd/
```

*Expected files:*
| File | Purpose |
|---|---|
| `ca.crt` | etcd CA certificate |
| `server.crt` | etcd server certificate |
| `server.key` | etcd server key |
| `peer.crt` | etcd peer certificate |
| `peer.key` | etcd peer key |

---

**Q7. Identify the etcd data directory**
Find where etcd is storing its data on the node.

```bash
cat /etc/kubernetes/manifests/etcd.yaml | grep data-dir
```

*Default path: `/var/lib/etcd`*

---

**Q8. Troubleshoot etcd not starting**
The etcd Pod is in `Error` or `CrashLoopBackOff` state after a restore. Identify and fix the issue.

*Hint: check these common causes:*
- `--data-dir` in the manifest doesn't match the restored directory
- Wrong file permissions on the data directory
- Certificate paths are incorrect

```bash
kubectl describe pod etcd-<node> -n kube-system    # check Events
crictl logs <etcd-container-id>                    # check container logs directly
ls -la /var/lib/etcd-restore                       # check permissions
chmod -R 700 /var/lib/etcd-restore                 # fix if needed
```

---

**Q9. Back up and restore — identify what changed**
1. Create a ConfigMap named `pre-backup` before taking a snapshot
2. Take a snapshot
3. Create a second ConfigMap named `post-backup`
4. Restore the snapshot
5. Verify `pre-backup` exists but `post-backup` is gone — confirming the restore worked

```bash
kubectl create configmap pre-backup --from-literal=key=value
# take snapshot (see Q3)
kubectl create configmap post-backup --from-literal=key=value
# restore snapshot (see Q5)
kubectl get configmap    # post-backup should not exist
```

---

**Q10. Full backup and restore scenario**
Complete the following end-to-end task:
1. Verify etcd is healthy
2. Take a snapshot to `/opt/etcd-snapshot.db` and verify it
3. Simulate data loss by deleting a namespace with running workloads
4. Restore the snapshot to `/var/lib/etcd-from-backup`
5. Update the etcd manifest to use the new data directory
6. Wait for etcd and the API server to recover
7. Confirm the deleted namespace and its workloads are back

```bash
# Step 3 — simulate loss
kubectl delete namespace production

# Step 6 — wait for recovery
watch kubectl get nodes

# Step 7 — verify restore
kubectl get namespace production
kubectl get pods -n production
```

---

## Quick Reference

| Task | Command |
|---|---|
| Health check | `etcdctl endpoint health` |
| Member list | `etcdctl member list` |
| Take backup | `etcdctl snapshot save <path>` |
| Verify backup | `etcdctl snapshot status <path> --write-out=table` |
| Restore backup | `etcdctl snapshot restore <path> --data-dir=<new-path>` |

## Key Paths to Memorise

| Path | What |
|---|---|
| `/etc/kubernetes/manifests/etcd.yaml` | etcd static Pod manifest |
| `/etc/kubernetes/pki/etcd/` | All etcd certificates |
| `/var/lib/etcd` | Default etcd data directory |

*Tip: Always set `ETCDCTL_API=3` — the default is v2 and commands will silently behave differently. Every `etcdctl` command needs `--cacert`, `--cert`, and `--key` — missing any one of them causes an auth error.*
