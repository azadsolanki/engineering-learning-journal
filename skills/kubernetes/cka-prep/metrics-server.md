How to add Metrics Server?
1. find metric server github link through kubernetes.io and download 
```bash
wget https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

2. edit  the file - Add the "Insecure" flag
```bash
vi components.yaml
```

```yaml
containers:
      - args:
        - --cert-dir=/tmp
        - --secure-port=4443
        - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
        - --kubelet-use-node-status-port
        - --metric-resolution=15s
        - --kubelet-insecure-tls    # <--- YOU MUST ADD THIS
```

3. apply 
```bash
kubectl apply -f component.yaml
```

4. verify 
```bash 
kubectl -n kube-system get pods 
kubectl top nodes
kubectl top pods
```
