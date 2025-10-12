# Grafana on Kubernetes — Quick Usage Guide

### Prerequisites
- Kubernetes cluster with `kubectl` access  
- Namespace `monitoring`
- Prometheus service available inside the cluster  
  (e.g. `http://prometheus-service.monitoring.svc:8080`)

```bash
kubectl create namespace monitoring
```

---

### 1. Deploy Grafana

```bash
kubectl apply -f https://raw.githubusercontent.com/bibinwilson/kubernetes-grafana/master/deployment.yaml
```

---

### 2. Expose Grafana

```bash
kubectl apply -f https://raw.githubusercontent.com/bibinwilson/kubernetes-grafana/master/service.yaml
```

Once deployed, get the access URL:

```bash
kubectl get svc -n monitoring grafana
```

If using NodePort, visit:
```
http://<node-ip>:32000
```

Or port-forward:

```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

Then open [http://localhost:3000](http://localhost:3000).

Default login:
```
username: admin
password: admin
```

---

### 3. Add Prometheus Data Source

In Grafana UI:
1. Go to **Connections → Data Sources → Add data source**
2. Choose **Prometheus**
3. Set URL:
   ```
   http://prometheus-service.monitoring.svc:8080
   ```
4. Click **Save & Test**

---

### 4. Import Kubernetes Dashboards

In Grafana UI:
1. Go to **Dashboards → Import**
2. Paste any dashboard ID from [grafana.com/dashboards](https://grafana.com/grafana/dashboards/)
3. Select the `prometheus` data source

Example IDs:  
- **6417** — Kubernetes Cluster Monitoring  
- **8588** — Kubernetes Cluster (Prometheus)

---

### 5. Uninstall

```bash
kubectl delete -f https://raw.githubusercontent.com/bibinwilson/kubernetes-grafana/master/service.yaml
kubectl delete -f https://raw.githubusercontent.com/bibinwilson/kubernetes-grafana/master/deployment.yaml
```

---

### References
- [DevOpsCube: Setup Grafana on Kubernetes](https://devopscube.com/setup-grafana-kubernetes/)
- [Bibin Wilson’s GitHub Repo](https://github.com/bibinwilson/kubernetes-grafana)
