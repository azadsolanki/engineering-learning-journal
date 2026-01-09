etcd Restore

1. use `sudo` or use `root -i`. Stop API servers and etcd (prevent conflicts), move the manifests temporarily so the pods stop and files aren't locked.
```bash
 mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp
 mv /etc/kubernetes/manifests/etcd.yaml /tmp
```

2. run restore 
```bash 
# ..Use a new data directory to avoid the "not empty" error.
ETCDCTL_API=3 etcdutl snapshot restore /opt/cluster_backup.db \
  --data-dir /var/lib/etcd-new
```

3. IF needed Fix Permissions:
```bash 
chown -R root:root /var/lib/etcd-new
```

4. **Update the Manifest:** just move the old folder and rename the new one
```bash 
 mv /var/lib/etcd /var/lib/etcd-broken
 mv /var/lib/etcd-new /var/lib/etcd
```

5. **Restart:** Move the manifests back.
```bash 
sudo mv /tmp/etcd.yaml /etc/kubernetes/manifests/ 
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
```

6. verify: check if "Static Pods" are back online 
```bash 
#.. check pod status
kubectl get pods -n kube-system 

# .. check container runtime 
sudo crictl ps 

# checl api health 
kubectl get nodes
```
