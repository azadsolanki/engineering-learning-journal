# Networking Fundamentals for Kubernetes

## Table of Contents
1. [IP Addresses & Subnets](#ip-addresses--subnets)
2. [CIDR Notation](#cidr-notation)
3. [DNS (Domain Name System)](#dns)
4. [NAT (Network Address Translation)](#nat)
5. [Ports](#ports)
6. [Routing Basics](#routing)
7. [CNI (Container Network Interface)](#cni)

---

## IP Addresses & Subnets

### What is an IP Address?

**IP Address** = A unique identifier for a device on a network (like a phone number for computers)

**Example**: `192.168.1.10`

**Analogy**: Like a street address for mail delivery
- `192.168.1` = Street name
- `10` = House number

### Two Types of IP Addresses

**IPv4**: `192.168.1.10` (4 numbers, 0-255 each)
**IPv6**: `2001:0db8:85a3::8a2e:0370:7334` (longer, more addresses available)

We'll focus on IPv4 for simplicity.

### Public vs Private IP Addresses

**Public IP** = Unique on the entire internet (like your home address)
- Assigned by ISP
- Routable on internet
- Example: `8.8.8.8` (Google DNS)

**Private IP** = Only unique within your local network (like apartment numbers in a building)
- Not routable on internet
- Can be reused in different networks
- Ranges:
  - `10.0.0.0` to `10.255.255.255`
  - `172.16.0.0` to `172.31.255.255`
  - `192.168.0.0` to `192.168.255.255`

**Your home example**:
- Router has public IP: `203.0.113.5` (visible to internet)
- Your laptop has private IP: `192.168.1.10` (only in your home)
- Your phone has private IP: `192.168.1.11` (only in your home)

### What is a Subnet?

**Subnet** = A group of IP addresses that belong together (like a neighborhood)

**Example**: All addresses from `192.168.1.0` to `192.168.1.255` form one subnet

**Why subnets?**
- Organize networks into logical groups
- Control traffic flow
- Improve security

---

## CIDR Notation

### What is CIDR?

**CIDR** = Classless Inter-Domain Routing (a way to write IP ranges compactly)

**Format**: `IP-address/prefix-length`

**Example**: `192.168.1.0/24`

### Breaking Down CIDR

`192.168.1.0/24` means:
- **192.168.1.0** = Network address (starting point)
- **/24** = First 24 bits are the network part (last 8 bits are for hosts)

### Understanding the /Number

The number after `/` tells you how many bits are "fixed" (network part):

| CIDR | Subnet Mask | # of IPs | Usable IPs | Example Use |
|------|-------------|----------|------------|-------------|
| /32 | 255.255.255.255 | 1 | 1 | Single host |
| /24 | 255.255.255.0 | 256 | 254 | Small network |
| /16 | 255.255.0.0 | 65,536 | 65,534 | Medium network |
| /8 | 255.0.0.0 | 16,777,216 | 16,777,214 | Large network |

### Common Examples

**10.244.0.0/16**
- Network: 10.244.0.0
- First IP: 10.244.0.1
- Last IP: 10.244.255.254
- Total: 65,534 usable IPs
- Use: Pod network in Kubernetes

**192.168.1.0/24**
- Network: 192.168.1.0
- First IP: 192.168.1.1
- Last IP: 192.168.1.254
- Total: 254 usable IPs
- Use: Home network

### Quick CIDR Reference

```
/32 = 1 IP       (255.255.255.255)
/31 = 2 IPs      (255.255.255.254)
/30 = 4 IPs      (255.255.255.252)
/29 = 8 IPs      (255.255.255.248)
/28 = 16 IPs     (255.255.255.240)
/27 = 32 IPs     (255.255.255.224)
/26 = 64 IPs     (255.255.255.192)
/25 = 128 IPs    (255.255.255.128)
/24 = 256 IPs    (255.255.255.0)    ← Most common
/16 = 65,536 IPs (255.255.0.0)      ← Kubernetes default
/8  = 16M IPs    (255.0.0.0)
```

### Visual Example

```
192.168.1.0/24

192.168.1.0   ← Network address (not usable)
192.168.1.1   ← First usable IP
192.168.1.2
192.168.1.3
...
192.168.1.254 ← Last usable IP
192.168.1.255 ← Broadcast address (not usable)
```

---

## DNS (Domain Name System)

### What is DNS?

**DNS** = Phone book for the internet (translates names to IP addresses)

**Example**:
- You type: `google.com`
- DNS translates to: `142.250.185.46`
- Your browser connects to that IP

### Why DNS?

**Without DNS**: Remember `142.250.185.46` to visit Google  
**With DNS**: Just remember `google.com`

### How DNS Works

```
1. You type: www.example.com
2. Computer asks DNS server: "What's the IP for www.example.com?"
3. DNS server responds: "It's 93.184.216.34"
4. Your computer connects to 93.184.216.34
```

### DNS in Kubernetes

Kubernetes has **internal DNS** (CoreDNS) that lets pods find each other by name:

```
# Instead of:
curl http://10.244.1.5

# You can use:
curl http://my-service
curl http://my-service.default.svc.cluster.local
```

**How it works**:
1. Service `my-service` gets IP `10.96.10.5`
2. CoreDNS creates DNS record: `my-service` → `10.96.10.5`
3. Pods can use the name `my-service` instead of remembering the IP

### DNS Records Types

**A Record**: Name → IPv4 address
- `example.com` → `93.184.216.34`

**AAAA Record**: Name → IPv6 address
- `example.com` → `2606:2800:220:1:248:1893:25c8:1946`

**CNAME Record**: Name → Another name (alias)
- `www.example.com` → `example.com`

**In Kubernetes**:
- Services get A records: `my-service` → ClusterIP
- Headless services return multiple A records (all Pod IPs)

---

## NAT (Network Address Translation)

### What is NAT?

**NAT** = Translates private IPs to public IPs (like a receptionist forwarding calls)

**Problem NAT Solves**:
- You have 5 devices at home (private IPs)
- Internet only sees 1 public IP
- How do return packets know which device to go to?

### How NAT Works

```
Inside your home:
- Laptop: 192.168.1.10
- Phone: 192.168.1.11
- Tablet: 192.168.1.12

Your router public IP: 203.0.113.5

When laptop accesses google.com:
1. Laptop sends: 192.168.1.10:54321 → 142.250.185.46:80
2. Router translates: 203.0.113.5:12345 → 142.250.185.46:80
3. Google responds to: 203.0.113.5:12345
4. Router translates back: 192.168.1.10:54321
```

### NAT Translation Table

| Internal IP:Port | External IP:Port | Destination |
|------------------|------------------|-------------|
| 192.168.1.10:54321 | 203.0.113.5:12345 | 142.250.185.46:80 |
| 192.168.1.11:54322 | 203.0.113.5:12346 | 8.8.8.8:53 |

Router remembers which internal device made each request.

### Types of NAT

**1. SNAT (Source NAT)** - Changes source IP
- Used when internal devices access internet
- Private IP → Public IP

**2. DNAT (Destination NAT)** - Changes destination IP  
- Used for port forwarding
- Public IP:Port → Private IP:Port

**3. Masquerading** - Dynamic SNAT
- Common in home routers

### NAT in Kubernetes

**Without NAT**:
- Pod (10.244.1.5) → Internet
- Internet sees Pod IP directly
- Problem: Pod IPs not routable on internet

**With NAT**:
- Pod (10.244.1.5) → Internet
- Node translates to its IP (192.168.1.100)
- Internet sees node IP
- Return traffic works

Kubernetes uses **iptables** or **IPVS** to do NAT automatically.

---

## Ports

### What is a Port?

**Port** = A numbered door on a computer (determines which application gets the data)

**IP Address** = Building address  
**Port** = Apartment number

**Example**: `192.168.1.10:80`
- `192.168.1.10` = IP (which computer)
- `80` = Port (which application)

### Port Numbers

**Range**: 0-65535

**Well-Known Ports** (0-1023):
- `20/21` = FTP
- `22` = SSH
- `25` = SMTP (email)
- `53` = DNS
- `80` = HTTP (web)
- `443` = HTTPS (secure web)
- `3306` = MySQL
- `5432` = PostgreSQL
- `6443` = Kubernetes API

**Registered Ports** (1024-49151):
- Used by specific applications

**Dynamic Ports** (49152-65535):
- Temporary ports for client connections

### Port Example

```
You visit: http://example.com:80

Translation:
- DNS: example.com → 93.184.216.34
- Connect to: 93.184.216.34:80
- Port 80 = web server

Your computer:
- Source: 192.168.1.10:54321 (random high port)
- Destination: 93.184.216.34:80 (web server)
```

### Ports in Kubernetes

**Three types**:

1. **containerPort** - Port inside the Pod container
   ```yaml
   ports:
   - containerPort: 8080  # App listens here
   ```

2. **port** - Port on the Service
   ```yaml
   ports:
   - port: 80  # Service listens here
   ```

3. **nodePort** - Port on every node (30000-32767)
   ```yaml
   ports:
   - nodePort: 30080  # External access
   ```

**Traffic flow**:
```
External → NodePort (30080)
    → Service (80)
    → Pod Container (8080)
```

---

## Routing

### What is Routing?

**Routing** = Finding the path for data to travel from source to destination

**Analogy**: GPS navigation for network packets

### How Routing Works

```
You (192.168.1.10) want to reach Google (8.8.8.8):

1. Check: Is 8.8.8.8 on my local network (192.168.1.0/24)?
   → No
2. Send packet to default gateway (router: 192.168.1.1)
3. Router checks its routing table
4. Router forwards to next hop
5. ... (multiple hops through internet)
6. Packet reaches 8.8.8.8
```

### Routing Table

Every device has a routing table:

```bash
# View routing table
ip route

# Example output:
default via 192.168.1.1 dev eth0
10.244.0.0/16 via 10.244.0.1 dev cni0
192.168.1.0/24 dev eth0 scope link
```

**Reading the table**:
- `default via 192.168.1.1` = Send everything else to router
- `10.244.0.0/16 via 10.244.0.1` = Send Pod traffic to CNI
- `192.168.1.0/24 dev eth0` = Local network, direct connection

### Routing in Kubernetes

**Pod-to-Pod on Same Node**:
```
Pod1 (10.244.1.5) → Pod2 (10.244.1.6)
No routing needed - direct connection via bridge
```

**Pod-to-Pod on Different Nodes**:
```
Node1: Pod1 (10.244.1.5) → Node2: Pod2 (10.244.2.8)

1. Pod1 sends to 10.244.2.8
2. Node1 checks route: 10.244.2.0/24 → Node2
3. Packet sent to Node2
4. Node2 delivers to Pod2
```

CNI plugin (Flannel/Calico) sets up these routes automatically!

---

## CNI (Container Network Interface)

### What is CNI?

**CNI** = Standard for connecting containers to networks

**Analogy**: Like USB - a standard interface so any device (container) can connect

### Why CNI Exists

**Problem**: Every container runtime (Docker, containerd) had different networking
**Solution**: CNI - a standard interface they all use

### What CNI Does

When a Pod starts:
1. **Allocate IP** - Assign IP to Pod from available range
2. **Create network interface** - Add virtual network card to Pod
3. **Connect to network** - Attach Pod to cluster network
4. **Set up routes** - Configure routing so Pod can reach others
5. **Configure DNS** - Set DNS so Pod can resolve names

### CNI Plugins

**Popular CNI Plugins**:

1. **Flannel** - Simple, easy to use
   - Creates overlay network
   - Uses VXLAN by default
   - Good for beginners

2. **Calico** - Advanced features
   - Network policies
   - BGP routing
   - Good for production

3. **Weave** - Mesh networking
   - Automatic encryption
   - Easy multi-cluster

4. **Cilium** - Modern, eBPF-based
   - High performance
   - Advanced security

### CNI Components

**1. CNI Configuration File** (what to do)
```json
{
  "name": "cbr0",
  "type": "flannel",
  "delegate": {...}
}
```
Location: `/etc/cni/net.d/10-flannel.conflist`

**2. CNI Binary Plugins** (how to do it)
```
/opt/cni/bin/
├── flannel    - Main plugin
├── bridge     - Create network bridges
├── portmap    - Port forwarding
├── host-local - IP management
└── loopback   - Loopback interface
```

**3. CNI Runtime** (when to do it)
- containerd/CRI-O calls CNI when Pod starts/stops

### CNI Workflow

```
1. kubelet: "Start Pod xyz"
2. containerd: "Create container"
3. containerd calls CNI: "Set up networking for container abc"
4. CNI reads config: /etc/cni/net.d/10-flannel.conflist
5. CNI executes: /opt/cni/bin/flannel
6. Flannel assigns IP: 10.244.1.5
7. Flannel creates interface in Pod
8. Flannel sets up routes
9. CNI returns: "Done! IP is 10.244.1.5"
10. containerd: "Container ready"
11. kubelet: "Pod running"
```

### Why You Need Both Config AND Binaries

**Config file** = Instructions (what network to create)
**Binary plugins** = Tools (programs that do the work)

**Analogy**:
- Config = Recipe
- Binaries = Kitchen tools

You need both! Recipe without tools = can't cook.

---

## How It All Fits Together in Kubernetes

### Complete Network Flow Example

**Scenario**: Pod on worker1 accesses Service on worker2

```
1. Pod1 (10.244.1.5) on worker1 wants to reach "backend-service"

2. DNS Resolution:
   - Pod asks CoreDNS: "What's backend-service?"
   - CoreDNS responds: "10.96.10.5" (Service ClusterIP)

3. Routing:
   - Pod sends to 10.96.10.5:80
   - kube-proxy intercepts (iptables rule)
   - kube-proxy selects backend Pod: 10.244.2.8:8080

4. Inter-Node Routing:
   - Worker1 routing table: 10.244.2.0/24 → Worker2
   - Packet sent to Worker2
   - Worker2 delivers to Pod (10.244.2.8)

5. Response:
   - Backend Pod responds to 10.244.1.5
   - Reverse path via routing
   - Pod1 receives response
```

### Network Components Summary

| Component | Purpose | Example |
|-----------|---------|---------|
| **IP Address** | Identify device | 10.244.1.5 |
| **CIDR** | Define IP range | 10.244.0.0/16 |
| **DNS** | Name to IP | my-service → 10.96.10.5 |
| **NAT** | Private ↔ Public IP | Pod IP → Node IP |
| **Port** | Identify application | :8080 |
| **Routing** | Path packets | 10.244.2.0/24 → Worker2 |
| **CNI** | Connect Pods to network | Flannel/Calico |

---

## Practice Exercises

### Exercise 1: CIDR Calculation
```
Given: 192.168.1.0/24
Questions:
1. How many total IPs? (256)
2. How many usable IPs? (254)
3. First usable IP? (192.168.1.1)
4. Last usable IP? (192.168.1.254)
5. Broadcast IP? (192.168.1.255)
```

### Exercise 2: DNS Lookup
```bash
# Try DNS lookup
nslookup google.com
dig google.com

# In Kubernetes
kubectl run test --image=busybox --rm -it -- nslookup kubernetes.default
```

### Exercise 3: Check Routes
```bash
# On your Linux machine
ip route

# On Kubernetes node
ssh node1
ip route | grep 10.244
```

### Exercise 4: Verify CNI
```bash
# Check CNI config exists
ls -la /etc/cni/net.d/

# Check CNI binaries exist
ls -la /opt/cni/bin/

# Both must exist for pods to work!
```

---

## Key Takeaways

1. **IP Address** = Unique identifier for a device
2. **CIDR** = Compact way to write IP ranges (/24, /16, etc.)
3. **DNS** = Translates names to IPs (like a phone book)
4. **NAT** = Translates private IPs to public IPs (router magic)
5. **Ports** = Identify which application on a device
6. **Routing** = How packets find their way
7. **CNI** = Standard for connecting containers to networks

**In Kubernetes**:
- Pods get IPs from Pod CIDR (CNI allocates)
- Services get IPs from Service CIDR (kube-apiserver)
- DNS (CoreDNS) lets Pods find Services by name
- CNI plugins connect Pods to the network
- kube-proxy handles Service routing

Now you're ready to dive into Kubernetes networking! 🚀