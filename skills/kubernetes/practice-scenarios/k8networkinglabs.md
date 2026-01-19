# Kubernetes Networking & Services - Hands-On Labs

## Lab Environment Setup

You have:
- 1 Master node
- 2 Worker nodes
- Kubeadm cluster

Let's verify your cluster is ready:

```bash
# Check cluster status
kubectl get nodes

# Verify networking plugin is running (Calico/Flannel/Weave)
kubectl get pods -n kube-system | grep -E 'calico|flannel|weave'

# Check CoreDNS is running
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

---

## Lab 1: Understanding Pod Networking Basics

### Objective
Understand how Pods get IPs and communicate with each other.

### Steps

**1. Create Pods on different nodes**

```bash
# Create first Pod
kubectl run pod1 --image=nginx --labels="app=test"

# Create second Pod
kubectl run pod2 --image=nginx --labels="app=test"

# Create third Pod
kubectl run pod3 --image=nginx --labels="app=test"
```

**2. Inspect Pod IPs and Node placement**

```bash
# Get Pod details
kubectl get pods -o wide

# Note the IP addresses and which nodes they're on
# Output example:
# NAME   READY   IP            NODE
# pod1   1/1     10.244.1.5    worker-1
# pod2   1/1     10.244.2.8    worker-2
# pod3   1/1     10.244.1.9    worker-1
```

**3. Test Pod-to-Pod connectivity**

```bash
# Exec into pod1
kubectl exec -it pod1 -- /bin/bash

# Inside pod1, install curl
apt update && apt install curl -y

# Test connectivity to pod2 (use the IP from previous command)
curl http://10.244.2.8  # Replace with actual pod2 IP

# Test connectivity to pod3
curl http://10.244.1.9  # Replace with actual pod3 IP

# Exit pod1
exit
```

**4. Understanding the Network**

```bash
# Check the routes on a worker node (SSH to worker node)
ssh worker-1
ip route

# Look for routes to other Pod subnets (e.g., 10.244.2.0/24)
# Exit worker node
exit
```

### Expected Results
- Pods on different nodes can communicate directly
- Each Pod has a unique IP from the Pod CIDR range
- No NAT is involved in Pod-to-Pod communication

### Questions to Answer
1. What IP range are your Pods using?
2. Can Pods on the same node communicate?
3. Can Pods on different nodes communicate?
4. What happens when you delete and recreate a Pod? (Check if IP changes)

---

## Lab 2: Creating and Understanding ClusterIP Services

### Objective
Learn how Services provide stable endpoints for dynamic Pods.

### Steps

**1. Create a deployment with multiple replicas**

```bash
# Create deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
        ports:
        - containerPort: 80
EOF
```

**2. Create a ClusterIP Service**

```bash
# Expose the deployment as a service
kubectl expose deployment nginx-deployment --port=80 --target-port=80 --name=nginx-service

# Alternative: Using YAML
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: nginx-service-yaml
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
EOF
```

**3. Inspect the Service**

```bash
# Get Service details
kubectl get svc nginx-service

# Describe the Service
kubectl describe svc nginx-service

# Check the Endpoints (should show 3 Pod IPs)
kubectl get endpoints nginx-service

# Detailed endpoint info
kubectl describe endpoints nginx-service
```

**4. Test the Service**

```bash
# Create a test Pod
kubectl run test-pod --image=busybox --rm -it -- /bin/sh

# Inside the test Pod:
# Install wget
wget -O- nginx-service

# Test multiple times to see load balancing
wget -O- nginx-service
wget -O- nginx-service
wget -O- nginx-service

# Test with full DNS name
wget -O- nginx-service.default.svc.cluster.local

# Exit
exit
```

**5. Observe Service behavior when Pods change**

```bash
# Scale down
kubectl scale deployment nginx-deployment --replicas=1

# Check endpoints (should now show only 1 Pod IP)
kubectl get endpoints nginx-service

# Scale up
kubectl scale deployment nginx-deployment --replicas=5

# Check endpoints again (should show 5 Pod IPs)
kubectl get endpoints nginx-service

# Delete a Pod manually
kubectl get pods
kubectl delete pod <one-of-the-nginx-pods>

# Watch endpoints update automatically
kubectl get endpoints nginx-service -w
# Press Ctrl+C to stop watching
```

### Expected Results
- Service gets a stable ClusterIP
- Endpoints automatically track healthy Pods
- Traffic is load-balanced across all Pods
- Service survives Pod restarts and rescaling

### Challenge Questions
1. What happens to the Service ClusterIP when you delete all Pods?
2. Do Endpoints update immediately when Pods become ready/unready?
3. Can you access the Service from any namespace?

---

## Lab 3: DNS Resolution and Service Discovery

### Objective
Master DNS-based service discovery in Kubernetes.

### Steps

**1. Create Services in different namespaces**

```bash
# Create namespaces
kubectl create namespace frontend
kubectl create namespace backend

# Deploy in frontend namespace
kubectl create deployment web --image=nginx --replicas=2 -n frontend
kubectl expose deployment web --port=80 -n frontend

# Deploy in backend namespace
kubectl create deployment api --image=nginx --replicas=2 -n backend
kubectl expose deployment api --port=80 -n backend
```

**2. Test DNS resolution patterns**

```bash
# Create test Pod in frontend namespace
kubectl run dns-test --image=busybox -n frontend --rm -it -- /bin/sh

# Inside the Pod, test DNS:

# Short name (same namespace)
nslookup web

# Full service name (same namespace)
nslookup web.frontend

# Full FQDN (same namespace)
nslookup web.frontend.svc.cluster.local

# Access service in different namespace
nslookup api.backend

# Full FQDN (different namespace)
nslookup api.backend.svc.cluster.local

# Exit
exit
```

**3. Test cross-namespace communication**

```bash
# Create test Pod in frontend namespace
kubectl run curl-test --image=curlimages/curl -n frontend --rm -it -- /bin/sh

# Inside the Pod:

# Access service in same namespace
curl http://web

# Access service in different namespace
curl http://api.backend

# Full FQDN
curl http://api.backend.svc.cluster.local

# Exit
exit
```

**4. Inspect CoreDNS configuration**

```bash
# View CoreDNS ConfigMap
kubectl get configmap coredns -n kube-system -o yaml

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50
```

### Expected Results
- Services are accessible via short names within the same namespace
- Cross-namespace access requires namespace qualification
- DNS resolves to ClusterIP
- All DNS patterns work consistently

### Challenge
Create a Service in namespace "prod" and access it from a Pod in namespace "dev".

---

## Lab 4: NodePort Services - External Access

### Objective
Expose services externally using NodePort.

### Steps

**1. Create a NodePort Service**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: webapp-nodeport
spec:
  type: NodePort
  selector:
    app: webapp
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # Specific port, or omit for random assignment
EOF
```

**2. Inspect the NodePort Service**

```bash
# Get Service details
kubectl get svc webapp-nodeport

# Describe service
kubectl describe svc webapp-nodeport

# Note the NodePort (should be 30080)
```

**3. Test external access**

```bash
# Get node IPs
kubectl get nodes -o wide

# Test from outside cluster (use actual node IPs)
curl http://<master-node-ip>:30080
curl http://<worker1-ip>:30080
curl http://<worker2-ip>:30080

# All should work and return the same content
```

**4. Understand NodePort behavior**

```bash
# Check which node the Pods are on
kubectl get pods -o wide -l app=webapp

# Even if no Pods are on master, you can still access via master IP
# This is because kube-proxy forwards traffic between nodes

# Scale to 1 replica
kubectl scale deployment webapp --replicas=1

# Note which node the single Pod is on
kubectl get pods -o wide -l app=webapp

# Access via ALL node IPs still works
curl http://<master-node-ip>:30080
curl http://<worker1-ip>:30080
curl http://<worker2-ip>:30080
```

### Expected Results
- Service accessible on the same port on ALL nodes
- Works even if Pods aren't on that specific node
- Combines ClusterIP + NodePort functionality

### Challenge
1. Create a NodePort service without specifying nodePort (let Kubernetes assign)
2. What port range can NodePort use? (Hint: check kube-apiserver flags)

---

## Lab 5: Headless Services and StatefulSets

### Objective
Understand headless services for direct Pod access.

### Steps

**1. Create a Headless Service**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: headless-service
spec:
  clusterIP: None  # This makes it headless
  selector:
    app: stateful
  ports:
  - port: 80
    targetPort: 80
EOF
```

**2. Create a StatefulSet with the Headless Service**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web-stateful
spec:
  serviceName: headless-service
  replicas: 3
  selector:
    matchLabels:
      app: stateful
  template:
    metadata:
      labels:
        app: stateful
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
        ports:
        - containerPort: 80
EOF
```

**3. Inspect StatefulSet Pods**

```bash
# Get Pods (note the predictable names)
kubectl get pods -l app=stateful

# Output:
# web-stateful-0
# web-stateful-1
# web-stateful-2

# Get Pod IPs
kubectl get pods -l app=stateful -o wide
```

**4. Test DNS resolution for Headless Service**

```bash
# Create test Pod
kubectl run dns-test --image=busybox --rm -it -- /bin/sh

# Inside Pod:

# Regular service DNS (returns ClusterIP)
nslookup nginx-service.default.svc.cluster.local

# Headless service DNS (returns all Pod IPs)
nslookup headless-service.default.svc.cluster.local

# Individual Pod DNS (only works with StatefulSet + Headless Service)
nslookup web-stateful-0.headless-service.default.svc.cluster.local
nslookup web-stateful-1.headless-service.default.svc.cluster.local
nslookup web-stateful-2.headless-service.default.svc.cluster.local

# Exit
exit
```

**5. Compare with regular ClusterIP**

```bash
# Create regular ClusterIP service for comparison
kubectl expose statefulset web-stateful --port=80 --name=stateful-clusterip

# Test DNS
kubectl run dns-compare --image=busybox --rm -it -- /bin/sh

# Inside Pod:
nslookup stateful-clusterip     # Returns single ClusterIP
nslookup headless-service       # Returns multiple Pod IPs

# Exit
exit
```

### Expected Results
- Headless service has no ClusterIP
- DNS returns all Pod IPs
- Each StatefulSet Pod has a stable DNS name
- Perfect for distributed systems (databases, etc.)

### Use Cases
- Databases (MongoDB, Cassandra, etc.)
- Applications that need peer discovery
- When you need stable network identities

---

## Lab 6: Session Affinity (Sticky Sessions)

### Objective
Understand client session affinity in Services.

### Steps

**1. Create Service without Session Affinity**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-no-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: no-affinity
  template:
    metadata:
      labels:
        app: no-affinity
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: svc-no-affinity
spec:
  selector:
    app: no-affinity
  ports:
  - port: 80
    targetPort: 80
EOF
```

**2. Test load balancing (no affinity)**

```bash
# Deploy a Pod to test from
kubectl run test-client --image=curlimages/curl --rm -it -- /bin/sh

# Inside Pod - make multiple requests and note which Pod responds
# First, we need to make Pods return their hostname
exit

# Update deployment to return Pod name
kubectl set env deployment/app-no-affinity HOSTNAME=\$HOSTNAME

# Wait for rollout
kubectl rollout status deployment/app-no-affinity

# Create test script
cat <<'SCRIPT' > test-affinity.sh
#!/bin/sh
for i in $(seq 1 10); do
  kubectl exec -it test-client -- curl -s http://svc-no-affinity | grep -o 'pod.*'
  sleep 1
done
SCRIPT

chmod +x test-affinity.sh

# Run test - you should see different Pods responding
./test-affinity.sh
```

**3. Create Service WITH Session Affinity**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-with-affinity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: with-affinity
  template:
    metadata:
      labels:
        app: with-affinity
    spec:
      containers:
      - name: nginx
        image: nginx:1.19
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: svc-with-affinity
spec:
  selector:
    app: with-affinity
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 300  # 5 minutes
  ports:
  - port: 80
    targetPort: 80
EOF
```

**4. Test session affinity**

```bash
# From the same client, make multiple requests
kubectl run test-sticky --image=curlimages/curl --rm -it -- /bin/sh

# Inside Pod - make multiple requests
for i in $(seq 1 10); do curl -s http://svc-with-affinity; done

# All requests should go to the SAME Pod
exit
```

### Expected Results
- Without affinity: Requests distributed across all Pods
- With ClientIP affinity: All requests from same client go to same Pod
- Affinity persists for the timeout duration

### Use Case
When application stores session data in memory (not recommended, but sometimes necessary).

---

## Lab 7: Network Policies - Traffic Control

### Objective
Control Pod-to-Pod traffic using Network Policies.

**Note**: Network Policies require a CNI plugin that supports them (Calico, Weave, Cilium). Check if yours does:

```bash
kubectl get pods -n kube-system | grep -E 'calico|weave|cilium'
```

### Steps

**1. Set up test environment**

```bash
# Create namespaces
kubectl create namespace frontend
kubectl create namespace backend
kubectl create namespace restricted

# Deploy apps in each namespace
kubectl create deployment web --image=nginx --replicas=2 -n frontend
kubectl create deployment api --image=nginx --replicas=2 -n backend
kubectl create deployment database --image=nginx --replicas=1 -n restricted

# Expose as services
kubectl expose deployment web --port=80 -n frontend
kubectl expose deployment api --port=80 -n backend
kubectl expose deployment database --port=80 -n restricted
```

**2. Test initial connectivity (all open)**

```bash
# Create test Pod in frontend
kubectl run test -n frontend --image=curlimages/curl --rm -it -- /bin/sh

# Test connectivity to all services
curl http://web.frontend
curl http://api.backend
curl http://database.restricted

# All should work
exit
```

**3. Apply Network Policy - Deny all ingress to restricted namespace**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: restricted
spec:
  podSelector: {}  # Applies to all Pods in namespace
  policyTypes:
  - Ingress
EOF
```

**4. Test after policy**

```bash
# Try to access database
kubectl run test -n frontend --image=curlimages/curl --rm -it -- /bin/sh

curl http://database.restricted --max-time 5

# Should timeout - no ingress allowed
exit
```

**5. Allow specific ingress**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-backend
  namespace: restricted
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: backend
    ports:
    - protocol: TCP
      port: 80
EOF
```

**6. Label the backend namespace**

```bash
kubectl label namespace backend name=backend
```

**7. Test selective access**

```bash
# From frontend - should fail
kubectl run test -n frontend --image=curlimages/curl --rm -it -- sh -c "curl http://database.restricted --max-time 5"

# From backend - should succeed
kubectl run test -n backend --image=curlimages/curl --rm -it -- sh -c "curl http://database.restricted"
```

**8. Example: Allow egress only to specific service**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress-policy
  namespace: frontend
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: backend
    ports:
    - protocol: TCP
      port: 80
  - to:  # Allow DNS
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
EOF
```

### Expected Results
- By default, all traffic is allowed
- Once a Network Policy exists, only allowed traffic passes
- Policies are additive (multiple policies combine)
- Must explicitly allow DNS if using egress policies

### Challenge
Create a three-tier app (frontend → backend → database) with Network Policies ensuring:
- Frontend can only access backend
- Backend can only access database
- Database accepts connections only from backend

---

## Lab 8: Service Troubleshooting Scenarios

### Scenario 1: Service not routing to Pods

**Problem Setup**:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: broken-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: broken
  template:
    metadata:
      labels:
        app: broken-wrong-label  # Wrong label!
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: broken-service
spec:
  selector:
    app: broken  # Doesn't match Pod labels
  ports:
  - port: 80
    targetPort: 80
EOF
```

**Troubleshooting Steps**:
```bash
# 1. Check Service
kubectl get svc broken-service
kubectl describe svc broken-service

# 2. Check Endpoints - will be empty!
kubectl get endpoints broken-service

# 3. Check Pod labels
kubectl get pods --show-labels

# 4. Fix by updating Pod labels or Service selector
kubectl label pods -l app=broken-wrong-label app=broken

# 5. Verify endpoints updated
kubectl get endpoints broken-service
```

### Scenario 2: Wrong targetPort

**Problem Setup**:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wrong-port-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: wrong-port
  template:
    metadata:
      labels:
        app: wrong-port
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80  # Nginx listens on 80
---
apiVersion: v1
kind: Service
metadata:
  name: wrong-port-service
spec:
  selector:
    app: wrong-port
  ports:
  - port: 80
    targetPort: 8080  # Wrong! Should be 80
EOF
```

**Troubleshooting**:
```bash
# 1. Service has endpoints
kubectl get endpoints wrong-port-service  # Shows IPs

# 2. But connection fails
kubectl run test --image=curlimages/curl --rm -it -- curl http://wrong-port-service --max-time 5

# 3. Check container port
kubectl get pods -l app=wrong-port
kubectl describe pod <pod-name> | grep Port

# 4. Fix the service
kubectl patch service wrong-port-service -p '{"spec":{"ports":[{"port":80,"targetPort":80}]}}'

# 5. Test again
kubectl run test --image=curlimages/curl --rm -it -- curl http://wrong-port-service
```

### Scenario 3: DNS not resolving

**Troubleshooting**:
```bash
# 1. Check CoreDNS is running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# 2. Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# 3. Test DNS from a Pod
kubectl run test-dns --image=busybox --rm -it -- nslookup kubernetes.default

# 4. Check service exists
kubectl get svc <service-name>

# 5. Test with FQDN
kubectl run test-dns --image=busybox --rm -it -- nslookup <service-name>.<namespace>.svc.cluster.local
```

---

## Lab 9: Advanced: Multi-Port Services

### Objective
Create services exposing multiple ports.

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: multi-port-service
spec:
  selector:
    app: multi-port-app
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8080
  - name: https
    protocol: TCP
    port: 443
    targetPort: 8443
  - name: metrics
    protocol: TCP
    port: 9090
    targetPort: 9090
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-port-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: multi-port-app
  template:
    metadata:
      labels:
        app: multi-port-app
    spec:
      containers:
      - name: app
        image: nginx
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 8443
          name: https
        - containerPort: 9090
          name: metrics
EOF
```

**Important**: When a Service has multiple ports, each port MUST have a name.

---

## Lab 10: CKA Exam Practice Scenarios

### Scenario 1: Create Service Imperatively (Fast!)

```bash
# Create deployment
kubectl create deployment web --image=nginx --replicas=3

# Expose as ClusterIP
kubectl expose deployment web --name=web-svc --port=80 --target-port=80

# Expose as NodePort on specific port
kubectl expose deployment web --name=web-nodeport --type=NodePort --port=80 --target-port=80

# Edit to add specific nodePort
kubectl edit svc web-nodeport
# Change nodePort to 30100 and save
```

### Scenario 2: Fix a Broken Service (Time Pressure)

Given: A service exists but isn't working.

```bash
# Quick diagnostic checklist:
kubectl get svc <service-name>               # Service exists?
kubectl get endpoints <service-name>         # Has endpoints?
kubectl get pods -l <selector> --show-labels # Pods match selector?
kubectl describe svc <service-name>          # Check ports
```

### Scenario 3: Create Network Policy

Allow only pods with label `role=api` to access pods with label `app=database` on port 5432:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-access
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: api
    ports:
    - protocol: TCP
      port: 5432
EOF
```

---

## Quick Reference Commands

```bash
# Service Operations
kubectl expose deployment <name> --port=80 --target-port=8080
kubectl get svc
kubectl describe svc <name>
kubectl delete svc <name>

# Endpoints
kubectl get endpoints <service-name>
kubectl describe endpoints <service-name>

# DNS Testing
kubectl run test --image=busybox --rm -it -- nslookup <service-name>

# Network Policy
kubectl get networkpolicies
kubectl describe networkpolicy <name>

# Labels (critical for Services!)
kubectl label pods <pod-name> app=myapp
kubectl get pods --show-labels
kubectl get pods -l app=myapp
```

---

## Common Exam Tasks - Practice These!

1. **Create a deployment and expose it as a NodePort service on port 30080**
2. **Modify an existing ClusterIP service to become a NodePort**
3. **Create a NetworkPolicy that denies all ingress to a namespace**
4. **Troubleshoot why a service has no endpoints**
5. **Create a headless service for a StatefulSet**
6. **Test DNS resolution between services in different namespaces**
7. **Configure session affinity for a service**

---

## Cleanup

```bash
# Clean up all labs
kubectl delete deployment --all
kubectl delete service --all
kubectl delete statefulset --all
kubectl delete networkpolicy --all
kubectl delete namespace frontend backend restricted
```

## Next Steps

1. Practice all labs multiple times until you can do them from memory
2. Time yourself - CKA is time-constrained
3. Practice imperative commands (faster than YAML in exams)
4. Understand troubleshooting workflows
5. Read the Kubernetes documentation on Services and Networking

Good luck with your CKA exam!