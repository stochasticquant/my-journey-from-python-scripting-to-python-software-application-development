
# Day 9 – Kubernetes Deployment

> Goal: Deploy your containerized inventory application to **Kubernetes**, using Deployments, Services, ConfigMaps, Secrets, and StatefulSets to achieve a production-style setup.

---

## 1. Kubernetes: Container Orchestration Explained

### What is Kubernetes?

**Kubernetes (K8s)** is an open-source system for automating **deployment, scaling, and management** of containerized applications.

**Analogy:** If Docker is like a **shipping container**, Kubernetes is like a fully automated **port management system**:

- **Docker Containers** – Individual shipping containers.
- **Kubernetes** – Automated cranes, storage yards, and traffic control.

### Why Kubernetes?

```bash
# Without Kubernetes (manual management)
docker run -p 8000:8000 myapp
docker run -p 8001:8000 myapp  # Manual load balancing
# What if a container crashes? What about scaling?
```

```bash
# With Kubernetes (automated management)
kubectl create deployment myapp --image=myapp:latest
kubectl scale deployment myapp --replicas=3  # Easy scaling
kubectl expose deployment myapp --port=8000  # Built-in load balancing
```

Kubernetes continuously watches the **desired state** (YAML manifests) and reconciles the **actual state** of the cluster.

---

## 2. Kubernetes Architecture and Components

### Kubernetes Cluster Structure

```text
Kubernetes Cluster
├── Control Plane (Master Nodes)
│   ├── API Server
│   ├── Scheduler
│   ├── Controller Manager
│   └── etcd (Cluster State)
└── Worker Nodes
    ├── Kubelet
    ├── Container Runtime (Docker / containerd)
    ├── Pods (Your Applications)
    └── kube-proxy
```

### Key Components

- **Pod** – Smallest deployable unit; one or more containers running together.
- **Deployment** – Manages replicated Pods and rolling updates.
- **Service** – Stable network endpoint that load balances across Pods.

#### Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
spec:
  containers:
  - name: app
    image: myapp:latest
```

#### Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-deployment
spec:
  replicas: 3  # Run 3 identical pods
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:latest
        ports:
        - containerPort: 8000
```

#### Service Example

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp  # Selects pods with this label
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

---

## 3. Kubernetes Manifests: Declarative Configuration

### Declarative vs Imperative

```bash
# Imperative (commands)
kubectl run myapp --image=myapp:latest
kubectl expose deployment myapp --port=8000
```

```bash
# Declarative (YAML files - preferred)
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Benefits of Declarative Approach

- **Version Control** – Store manifests in Git.
- **Reproducibility** – Same configuration can be applied repeatedly.
- **Audit Trail** – Track changes over time.
- **GitOps** – Manage infrastructure via pull requests and pipelines.

Kubernetes works best when you treat manifests as **Infrastructure as Code**.

---

## 4. Namespaces: Isolating Environments

### What Are Namespaces?

Namespaces provide **virtual clusters** within a physical Kubernetes cluster.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: inventory-system
```

### Why Use Namespaces?

- **Isolation** – Separate dev, staging, and prod.
- **Resource Quotas** – Limit CPU/memory per namespace.
- **Access Control** – Different RBAC rules per namespace.
- **Organization** – Group related applications and services.

In this course, you’ll deploy everything into the `inventory-system` namespace.

---

## 5. ConfigMaps and Secrets: Configuration Management

### ConfigMaps

ConfigMaps store **non-sensitive configuration** like hostnames, ports, or feature flags.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: inventory-config
  namespace: inventory-system
data:
  db-host: "sqlserver"
  db-port: "1433"
  db-name: "inventory"
  db-user: "sa"
  app-port: "8000"
```

### Secrets

Secrets store **sensitive information**, encoded as base64 (not encrypted by default).

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: inventory-secrets
  namespace: inventory-system
type: Opaque
data:
  db-password: <base64-encoded-password>
  secret-key: <base64-encoded-secret-key>
```

#### Creating Base64 Values

```bash
echo -n "YourStrong!Passw0rd" | base64
# WW91clN0cm9uZyFQYXNzdzByZA==

echo -n "your-super-secret-key" | base64
# eW91ci1zdXBlci1zZWNyZXQta2V5
```

> **Security Note:** Don’t commit real secrets to version control. Use **external secret managers** (e.g., Azure Key Vault + CSI driver, HashiCorp Vault, External Secrets Operator) in real production systems.

---

## 6. SQL Server with StatefulSet

Databases are **stateful** and need stable identities and persistent storage. For this, we use a **StatefulSet**.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: sqlserver
  namespace: inventory-system
spec:
  serviceName: sqlserver         # Headless service for stable network identity
  replicas: 1                    # Single instance for database
  selector:
    matchLabels:
      app: sqlserver
  template:
    metadata:
      labels:
        app: sqlserver
    spec:
      containers:
      - name: sqlserver
        image: mcr.microsoft.com/mssql/server:2022-latest
        env:
        - name: SA_PASSWORD
          valueFrom:
            secretKeyRef:
              name: inventory-secrets
              key: db-password
        - name: ACCEPT_EULA
          value: "Y"
        - name: MSSQL_PID
          value: "Standard"
        ports:
        - containerPort: 1433
        volumeMounts:
        - name: sqlserver-data
          mountPath: /var/opt/mssql
  volumeClaimTemplates:
  - metadata:
      name: sqlserver-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### Why StatefulSet for Database?

- **Stable network identity** – Pods get deterministic names (`sqlserver-0`, etc.).
- **Persistent storage** – Data survives restarts via PVCs.
- **Ordered deployment and scaling** – Useful for replicated DBs or clusters.

---

## 7. Application Deployment

Your application is **stateless**, so it uses a **Deployment**.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory-app
  namespace: inventory-system
spec:
  replicas: 3  # High availability and load balancing
  selector:
    matchLabels:
      app: inventory-app
  template:
    metadata:
      labels:
        app: inventory-app
    spec:
      containers:
      - name: app
        image: your-registry/inventory-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: inventory-secrets
              key: db-password
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: inventory-secrets
              key: secret-key
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: inventory-config
              key: db-host
        - name: DB_PORT
          valueFrom:
            configMapKeyRef:
              name: inventory-config
              key: db-port
        - name: DB_NAME
          valueFrom:
            configMapKeyRef:
              name: inventory-config
              key: db-name
        - name: DB_USER
          valueFrom:
            configMapKeyRef:
              name: inventory-config
              key: db-user
        - name: APP_PORT
          valueFrom:
            configMapKeyRef:
              name: inventory-config
              key: app-port
        # Liveness and readiness probes will be added below
```

### Key Deployment Features

- **Replicas** – Multiple instances for high availability.
- **Environment variables** – Pulled from ConfigMaps and Secrets.
- **Declarative configuration** – Entire app definition in YAML.

---

## 8. Services for Network Access

### SQL Server Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sqlserver-service
  namespace: inventory-system
spec:
  selector:
    app: sqlserver
  ports:
  - port: 1433
    targetPort: 1433
  type: ClusterIP  # Internal-only
```

### Application Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-service
  namespace: inventory-system
spec:
  type: LoadBalancer  # Expose externally (or NodePort if no LB support)
  selector:
    app: inventory-app
  ports:
  - port: 80
    targetPort: 8000  # Forward to container port 8000
```

### Service Types

- **ClusterIP** – Internal-only, default type.
- **NodePort** – Exposes service on `<NodeIP>:<NodePort>`.
- **LoadBalancer** – Provisions external load balancer (cloud).
- **Headless (ClusterIP: None)** – Used with StatefulSets for direct pod access.

If you’re on bare metal, you’ll often pair `LoadBalancer` with **MetalLB** or use `NodePort` + external reverse proxy.

---

## 9. Health Checks and Probes

### Liveness Probe

Checks if the container is **still alive**. If it fails, Kubernetes restarts the container.

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

### Readiness Probe

Checks if the container is **ready to receive traffic**. If it fails, Kubernetes removes the pod from Service endpoints.

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

**Difference:**

- **Liveness** – “Should this pod be restarted?”
- **Readiness** – “Should this pod receive traffic right now?”

Your FastAPI app should expose `/health` to support these probes.

---

## 10. Persistent Volume Claims (PVCs)

For the database, you request persistent storage via **PVCs** (as in the StatefulSet example).

### Storage Access Modes

- **ReadWriteOnce (RWO)** – Single node read/write.
- **ReadOnlyMany (ROX)** – Multiple nodes read-only.
- **ReadWriteMany (RWX)** – Multiple nodes read/write (depends on storage backend).

Choosing the right access mode depends on your storage system and architecture.

---

## 11. Common Questions

**Q: Why use StatefulSet for the database but Deployment for the app?**  
**A:** Databases are **stateful** and need stable identities and persistent storage. Stateless application pods can be freely created/destroyed, so **Deployments** are ideal.

---

**Q: What's the difference between Deployment and StatefulSet?**  

- **Deployment** – Stateless, interchangeable pods, no stable identity.
- **StatefulSet** – Stateful, stable network IDs, ordered scaling, persistent storage.

---

**Q: How do pods find each other?**  
**A:** Kubernetes DNS makes services discoverable via names like:

```text
sqlserver-service.inventory-system.svc.cluster.local
```

Your app uses `DB_HOST=sqlserver-service` or the FQDN as needed.

---

**Q: Why use `LoadBalancer` instead of `NodePort`?**  
**A:** `LoadBalancer` integrates with cloud providers to create external load balancers. On bare metal, you can use `NodePort` or tools like **MetalLB** for a load balancer-like experience.

---

## 12. Deployment Commands

### Applying Manifests

```bash
# Apply all manifests
kubectl apply -f deployments/kubernetes/

# Apply specific manifest
kubectl apply -f deployments/kubernetes/namespace.yaml

# View resources in namespace
kubectl get all -n inventory-system

# View pods with more details
kubectl get pods -n inventory-system -o wide
```

### Monitoring Deployment

```bash
# Watch pod creation and status
kubectl get pods -n inventory-system -w

# View deployment logs
kubectl logs -n inventory-system deployment/inventory-app

# View specific pod logs
kubectl logs -n inventory-system <pod-name>

# Check service endpoints
kubectl get endpoints -n inventory-system
```

### Troubleshooting

```bash
# Describe a pod for detailed info
kubectl describe pod -n inventory-system <pod-name>

# Check events
kubectl get events -n inventory-system

# Exec into a container for debugging
kubectl exec -n inventory-system -it <pod-name> -- bash
```

---

## 13. Kubernetes in Development

### Local Kubernetes Options

- **Minikube** – Single-node local cluster.
- **Kind** – Kubernetes in Docker.
- **Docker Desktop** – Built-in K8s for local use.

#### Example: Minikube

```bash
# Start Minikube
minikube start

# Enable ingress (if needed)
minikube addons enable ingress

# Get Minikube IP
minikube ip

# Access application via service
minikube service -n inventory-system app-service
```

This lets you rehearse production-style deployments locally.

---

## 14. Production Considerations

### Resource Management

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

Why set requests/limits?

- Prevent any single pod from consuming all node resources.
- Help the scheduler place pods intelligently.
- Enable autoscalers to make informed decisions.

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inventory-app-hpa
  namespace: inventory-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inventory-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```

HPA dynamically scales the number of pods based on metrics (e.g., CPU utilization).

---

## 15. Further Reading

### Essential References

- Kubernetes Documentation – <https://kubernetes.io/docs/>
- Kubernetes Tutorials – <https://kubernetes.io/docs/tutorials/>
- `kubectl` Reference – <https://kubernetes.io/docs/reference/kubectl/>
- YAML Syntax – <https://yaml.org/>

### Deep Dive Topics

- Kubernetes Networking – <https://kubernetes.io/docs/concepts/services-networking/>
- Storage in Kubernetes – <https://kubernetes.io/docs/concepts/storage/>
- Kubernetes Security – <https://kubernetes.io/docs/concepts/security/>
- Helm Package Manager – <https://helm.sh/>

---

## 16. Practice Exercises (Day 9)

1. Deploy the application to **Minikube** or **Kind** using your manifests.
2. Scale the application Deployment and observe load balancing.
3. Implement a **Horizontal Pod Autoscaler** for the app.
4. Set up the **Kubernetes Dashboard** for visualization and management.
5. Create an **Ingress** resource to expose your API on a friendly URL (e.g., `/api`).

---

## 17. Key Takeaways

- Kubernetes **automates deployment, scaling, and management** of containers.
- Use **Deployments** for stateless services, **StatefulSets** for stateful components.
- **ConfigMaps** and **Secrets** decouple configuration from application code.
- **Services** provide stable network access and load balancing to Pods.
- **Health probes** (liveness/readiness) improve reliability and self-healing.
- **Namespaces** organize and isolate environments within the same cluster.
- Resource requests/limits and HPA enable **controlled, auto-scaled** workloads.

---

## 18. Coming Up Next (Day 10)

Tomorrow we’ll implement **advanced features, monitoring, and error handling** to complete your professional-grade Python application stack.
