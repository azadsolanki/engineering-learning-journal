# K8s Volumes

## Overview
Containers are ephemeral — data dies with them. Kubernetes Volumes are tied to the **Pod lifecycle**, not the container, so data survives container restarts but not Pod deletion. For data that must outlive a Pod, use PersistentVolumes.

---

## Lifecycle Comparison

| Storage Type | Survives container restart? | Survives Pod deletion? |
|---|---|---|
| Container storage | No | No |
| Volume (emptyDir) | Yes | No |
| PersistentVolume | Yes | Yes |

---

## Key Concepts

### Volume
- A directory accessible to containers within a Pod
- Each volume requires: a **name**, a **type**, and a **mount point**
- Can be shared across containers in the same Pod (watch for concurrent write conflicts)

### Volume Types
| Type | Backed by | Persists after Pod? |
|---|---|---|
| `emptyDir` | Node local storage | No |
| `hostPath` | Node filesystem path | No (node-dependent) |
| `NFS`, `Ceph (RBD)` | External storage | Yes |
| `AWS EBS`, `GCE PD` | Cloud storage via CSI | Yes |

### CSI (Container Storage Interface)
- Moves storage drivers **out-of-tree** — vendors maintain their own
- Replaces deprecated in-tree plugins and Flex plugin
- Enables dynamic provisioning with better security

### PersistentVolume (PV)
- Cluster-wide storage resource — pre-provisioned or dynamic via StorageClass
- Survives Pod deletion

### PersistentVolumeClaim (PVC)
- A Pod's **request** for a PV (size, access mode)
- Pods always reference PVCs — never PVs directly

### ConfigMaps & Secrets
| | ConfigMap | Secret |
|---|---|---|
| Data | Non-sensitive (env vars, config files) | Sensitive (passwords, SSH keys) |
| Format | Plain text | base64-encoded (not encrypted) |
| Usage | Mount as volume or inject as env var | Mount as volume or inject as env var |

---

## emptyDir — Ephemeral Shared Volume

Temporary directory created by kubelet when Pod starts. Deleted when Pod terminates.
Use for: scratch space, caching, inter-container file sharing.

### Single container example
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fordpinto
spec:
  containers:
  - name: gastank
    image: simpleapp
    command: ["sleep", "3600"]
    volumeMounts:
    - name: scratch-volume
      mountPath: /scratch
  volumes:
  - name: scratch-volume
    emptyDir: {}
```

### Shared volume between two containers
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: exampleA
spec:
  containers:
  - name: alphacont
    image: busybox
    volumeMounts:
    - name: sharevol
      mountPath: /alphadir
  - name: betacont
    image: busybox
    volumeMounts:
    - name: sharevol
      mountPath: /betadir
  volumes:
  - name: sharevol
    emptyDir: {}
```

### Test shared access
```bash
# Write from one container
kubectl exec -ti exampleA -c betacont -- touch /betadir/foobar

# Read from the other
kubectl exec -ti exampleA -c alphacont -- ls -l /alphadir
```

> **Warning**: Kubernetes has no built-in concurrency control — simultaneous writes to a shared volume can cause data corruption. Apps must handle their own locking.

---

## PersistentVolume Lifecycle

```
Provision → Bind → Use → Release → Reclaim
```

| Phase | What happens |
|---|---|
| **Provision** | PV created manually or dynamically via StorageClass |
| **Bind** | PVC matched to a suitable PV (by size + access mode) |
| **Use** | Pod mounts the PVC and uses the storage |
| **Release** | Pod/PVC deleted — PV is released but not yet available |
| **Reclaim** | PV is retained, recycled, or deleted based on policy |

```bash
kubectl get pv      # list PersistentVolumes
kubectl get pvc     # list PersistentVolumeClaims
```

---

## Access Modes

| Mode | Short | Who can mount |
|---|---|---|
| ReadWriteOnce | RWO | One node, read-write |
| ReadOnlyMany | ROX | Many nodes, read-only |
| ReadWriteMany | RWX | Many nodes, read-write |
| ReadWriteOncePod | RWOP | One Pod only, read-write |

> **Watch out**: RWO allows multiple Pods on the **same** node, but a Pod on a **different** node will get a `FailedAttachVolume` error. No built-in concurrency control — apps must handle their own locking.

---

## PV + PVC + Pod — Full Example

### 1. Create a PersistentVolume
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: 10Gpv01
  labels:
    type: local
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /somepath/data01
```

### 2. Create a PersistentVolumeClaim
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 8Gi
```

### 3. Mount PVC in a Pod
```yaml
spec:
  containers:
  - name: myapp
    volumeMounts:
    - name: test-volume
      mountPath: /data
  volumes:
  - name: test-volume
    persistentVolumeClaim:
      claimName: myclaim
```

---

## CKA Tips
- `emptyDir` = simplest volume, no setup needed, dies with Pod
- Pods **never** reference PVs directly — always through a PVC
- StorageClass enables **dynamic provisioning** — no manual PV creation needed
- Secrets are base64-encoded, **not encrypted**
- Shared volumes: use `emptyDir` or `hostPath` for temp, `PVC` for persistent
- RWO allows multi-Pod on same node — different node = `FailedAttachVolume`
- Legacy `rbd:` volume type removed — must use **Ceph CSI driver** instead
- Raw Block Volumes (since 1.13) allow direct block device access — no filesystem
