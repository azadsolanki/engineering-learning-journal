# CKA Practice Questions — Volumes

> All tasks are hands-on. Write YAML from scratch unless stated otherwise. Use `kubectl` to verify.

---

**Q1. emptyDir volume**
Create a Pod named `logger` using the `busybox` image with command `sleep 3600`. Mount an `emptyDir` volume named `log-volume` at `/var/log/app` inside the container.

---

**Q2. Shared volume between two containers**
Create a Pod named `shared-pod` with two containers — `writer` and `reader`, both using `busybox` with command `sleep 3600`. Both must share the same `emptyDir` volume. `writer` mounts it at `/output`, `reader` at `/input`.
Verify by writing a file from `writer` and reading it from `reader`.

---

**Q3. Create a PersistentVolume**
Create a `PersistentVolume` named `my-pv` with the following spec:
- Capacity: `5Gi`
- Access mode: `ReadWriteOnce`
- Reclaim policy: `Retain`
- Backed by `hostPath` at `/mnt/data`

---

**Q4. Create a PersistentVolumeClaim**
Create a `PersistentVolumeClaim` named `my-pvc` requesting `3Gi` with `ReadWriteOnce` access mode. Confirm it binds to `my-pv` from Q3.

```bash
# Expected status
kubectl get pvc my-pvc   # STATUS should be: Bound
```

---

**Q5. Mount a PVC into a Pod**
A PVC named `app-storage` already exists in the `default` namespace. Create a Pod named `app` using the `nginx` image that mounts this PVC at `/usr/share/nginx/html`.

---

**Q6. Troubleshoot a Pending PVC**
A PVC has been in `Pending` state for several minutes. Identify the cause and fix it.

*Hint: check these common causes:*
- No matching PV (size or access mode mismatch)
- Missing or incorrect StorageClass
- PV already bound to another PVC

```bash
kubectl describe pvc <pvc-name>    # look at Events section
kubectl get pv                     # check available PVs and their status
```

---

**Q7. Access mode scenario**
A Pod on `node-2` is failing with `FailedAttachVolume`. The PV uses `ReadWriteOnce` and is already mounted by a Pod on `node-1`.
- What is the cause?
- What access mode would allow both Pods on different nodes to read and write?
- What access mode would allow both Pods on different nodes to only read?

---

**Q8. ConfigMap as a volume**
Create a ConfigMap named `app-config` with the following data:
```
APP_ENV=production
LOG_LEVEL=info
```
Create a Pod named `config-pod` using the `busybox` image that mounts this ConfigMap as a volume at `/etc/config`. Verify the files are visible inside the container.

---

**Q9. Secret as a volume**
Create a Secret named `db-secret` with the following data:
- `username: admin`
- `password: s3cr3t`

Mount it into a Pod named `secret-pod` using the `busybox` image at `/etc/secret`. Confirm both keys appear as files inside the container.

---

**Q10. Full PV → PVC → Pod chain**
Complete the following end-to-end task:
1. Create a `PersistentVolume` named `data-pv` — `2Gi`, `ReadWriteOnce`, `hostPath` at `/tmp/data`
2. Create a `PersistentVolumeClaim` named `data-pvc` requesting `1Gi`, `ReadWriteOnce`
3. Create a Pod named `data-pod` using `busybox` with command `sleep 3600`, mounting `data-pvc` at `/data`
4. Exec into the Pod and write a file to `/data`
5. Delete the Pod and recreate it — verify the file is gone (emptyDir) vs. still present (PV)

```bash
kubectl exec -it data-pod -- sh
echo "hello" > /data/test.txt
exit
kubectl delete pod data-pod
# recreate pod, then:
kubectl exec -it data-pod -- cat /data/test.txt
```

---
