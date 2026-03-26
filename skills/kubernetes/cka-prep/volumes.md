# K8s Volumes 

## Overview
Containers are ephemeral — data dies with them. Kubernetes Volumes are tied to the **Pod lifecycle**, not the container, so data survives container restarts (but not Pod deletion). For data that must outlive a Pod, use PersistentVolumes.

---

## Key Concepts

### Volume
- A directory accessible to containers within a Pod
- Tied to Pod lifecycle — survives container crashes, not Pod deletion
- Types: local, NFS, Ceph (RBD), cloud (AWS EBS, GCE PD) via CSI drivers

### CSI (Container Storage Interface)
- Industry standard that moved storage drivers **out-of-tree** (vendors maintain their own)
- Replaces old in-tree plugins and deprecated Flex plugin
- Enables dynamic provisioning and better security (no elevated host access needed)

### PersistentVolume (PV)
- Cluster-wide storage resource, pre-provisioned or dynamically created via StorageClass
- Lives **beyond Pod lifecycle** — survives Pod deletion

### PersistentVolumeClaim (PVC)
- A Pod's **request** for a PV (specifies size, access mode)
- Once bound, PV is reserved — other Pods can claim and reuse the data later

### ConfigMaps & Secrets
| | ConfigMap | Secret |
|---|---|---|
| Data type | Non-sensitive (env vars, config files) | Sensitive (passwords, SSH keys) |
| Format | Plain text | base64-encoded |

---

## Lifecycle Comparison

| Storage Type | Survives container restart? | Survives Pod deletion? |
|---|---|---|
| Container storage | No | No |
| Volume | Yes | No |
| PersistentVolume | Yes | Yes |

---

## CKA Tips
- Volume vs PV: Volume = Pod-scoped, PV = cluster-scoped
- PVC is always the middleman between Pod and PV — Pods never reference PVs directly
- StorageClass enables **dynamic provisioning** — no need to manually create PVs
- Secrets are base64-encoded, **not encrypted** — know this distinction
- ConfigMaps and Secrets can be mounted as volumes or injected as env variables
