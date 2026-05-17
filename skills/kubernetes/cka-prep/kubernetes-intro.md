# Kubernetes — Intro Notes

## Why does Kubernetes exist?

Imagine you have 50 containers to run across 10 servers. Some crash. Some need more memory. Traffic spikes and you need 5 more copies. A server dies — you need its containers moved elsewhere, *now*. Doing this by hand doesn't scale, and shell scripts break the moment reality drifts from what you assumed.

**Kubernetes is the system that does all of this for you.** You tell it *what* you want ("run 3 copies of my app, give each 1 CPU"), and it figures out *how* to make that true and *keeps* it true — placing containers on healthy nodes, restarting them when they crash, moving them when nodes die, scaling them when you ask.

That's it. Everything below is just the machinery that makes this work.

## Architecture

![Kubernetes Architecture](./k8s-architecture.png)

The cluster splits into two halves:

**Control Plane** — the brain that decides what should happen
- **kube-api-server** — front door; only component that talks to etcd
- **etcd** — key-value store holding cluster state
- **kube-scheduler** — picks which node a pod runs on
- **kube-controller-manager** — keeps actual state = desired state

**Worker Nodes** — where your containers actually run
- **kubelet** — runs assigned pods, reports status
- **kube-proxy** — networking rules for Services
- **CRI** — container runtime (containerd, CRI-O)

## Two rules that explain everything

1. Only the **api-server** talks to etcd.
2. Workers connect to the control plane — never the reverse.

## Workflow: `kubectl apply -f pod.yaml`

When you run `kubectl apply -f pod.yaml`, the request hits the **kube-api-server**, which authenticates it and writes the pod to **etcd** with no node assigned. The **kube-scheduler**, which continuously watches the api-server, sees the unscheduled pod, picks the best node based on its cached view of node resources, and writes the assignment (`nodeName: worker-1`) back through the api-server into etcd. The **kubelet** on worker-1 is also watching the api-server and notices a pod has been assigned to it — it pulls the spec, calls the **CRI** to start the container, and reports the pod's status back to the api-server. Throughout this flow, nothing pushes work to anyone: every component watches the api-server and reacts, and the api-server is the only component that ever touches etcd.

> Mental model: api-server is a bulletin board, etcd is the filing cabinet behind it. Everyone else watches the board and pins their own updates.
