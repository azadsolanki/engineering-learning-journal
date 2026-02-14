The kube-scheduler uses a topology-aware algorithm - filtering, scoring, and assignment.    

When the API server receives a request to create a Pod, the scheduler evaluates the cluster’s nodes. Here is how it operates. 
- Filtering: The scheduler identifies nodes that meet a Pod’s resource requirements (e.g., CPU, memory) and any specific constraints.
- Scoring: It ranks the filtered nodes based on criteria like resource availability, affinity rules, and policies.
- Assignment: The scheduler selects the highest-scoring node and sends the Pod’s specification to the kubelet on that node, which creates and runs the Pod.

The scheduler then selects the most suitable node and informs the API server about its findings. In turn, the API server passes the Pod specification to the kubelet on that selected node, which handles Pod creation.

Flow:
![Chart](images/kube-scheduler-workflow.png)
Kubernetes scheduling workflow, illustrating how the kube-scheduler filters and scores nodes before selecting the optimal node where the kubelet creates the Pod.

Various configuration options in the Pod specification can influence the scheduler:

*Pod Priority and Preemption*:
  - You can assign a priority to a Pod to indicate its importance. If resources are limited, a higher-priority Pod can preempt (evict) lower-priority Pods to secure a place on a node. To use this feature:
      - Define a PriorityClass in your cluster.
      - Assign the PriorityClass to your Pod in its specification.
      - The scheduler will evict lower-priority Pods if necessary to schedule the higher-priority Pod.
      
*Labels and Selector*:
  - Labels applied to nodes and Pods help control where Pods can be scheduled 

*Taints and Tolerations*:
  - Taints mark nodes to repel Pods, while Tolerations allow specific Pods to run on tainted Nodes. 
  - Useful for reserving nodes for specific workloads or preventing certain Pods from running on specific Nodes

*Affinity and Anti-Affinity*
Using labels, you can configure affinity and anti-affinity rules:

    Node Affinity: Encourages or requires a Pod to be scheduled on nodes with specific labels. For example, you might prefer a Pod to run on nodes in a particular region but allow scheduling elsewhere if needed.

    Pod Affinity: Encourages Pods to be scheduled near other Pods with specific labels (e.g., to reduce latency between services).

    Pod Anti-Affinity: Prevents Pods from being scheduled on the same node as other Pods with specific labels (e.g., to spread replicas for high availability).

Some rules are "soft" preferences (the scheduler tries to satisfy the rule but will schedule the Pod elsewhere if needed), while others are "hard" requirements (the scheduler will only schedule the Pod if the rule is met). For example, requiredDuringSchedulingIgnoredDuringExecution requires the condition to be met during scheduling and will evict the Pod if the condition is no longer true during execution, while preferredDuringSchedulingIgnoredDuringExecution encourages scheduling on a node but doesn’t evict the Pod if conditions change after scheduling.
