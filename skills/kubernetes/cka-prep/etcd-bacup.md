etcd Backup

root access is needed to run `etcdctl` tool 
use `sudo apt install etcd-client` to install this tool 

```bash
# .. install etcd-client or etcd, esnure etcd-api is version 3
# ..on ubuntu 
sudo apt install etcd-client
# .. on Fedora
sudo dnf install -y etcd

# .. cert to be used, check --etcd-server
ps aux | grep etcd

# .. check what's inside etcd container and find out the certificats that exists
ls /etc/kubernetes/pki/etcd

```

```bash
# .. before back up, use --key-only param to see if it works 
sudo etcdctl --endpoints=localhost:2379 --cacert /etc/kubernetes/pki/etcd/ca.crt --cert /etc/kubernetes/pki/etcd/server.crt --key /etc/kubernetes/pki/etcd/server.key get / --prefix --keys-only

# ..get backup
sudo etcdctl --endpoints=localhost:2379 --cacert /etc/kubernetes/pki/etcd/ca.crt --cert /etc/kubernetes/pki/etcd/server.crt --key /etc/kubernetes/pki/etcd/server.key snapshot save /tmp/etcdbackup.db 

```

verify etcd back up
```bash
sudo etcdctl --write-out=table snaptshot status /tmp/etcdbackup.db
# .. take another copy of the back up 
sudo cp /tmp/etcdbackup.db /tmp/etcdbackup.db.2
```