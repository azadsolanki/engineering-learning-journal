Tasks: 
- create a role that allows for viewing of pods in the default Namespace 
- Configure a RoleBinding that allows all authenticated users to use this role
- 
```bash 
#.. create a role
kubectl create role defaultprodviewer --verb=get --verb=list --verb=watch --resource=pod -n default

# .. get cluster role binding 
kubectl get clusterrolebindings | grep basic-user

# .. test to see the permission and expect an error
kubectl get pods --as system:basic-user

# .. create role binding 

kubectl create rolebinding defaultpodviewer --role=defaultpodviewer --user=system:basic-user -n default
