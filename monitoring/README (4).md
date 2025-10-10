# Monitoring Setup (Kubernetes + Prometheus + Grafana)

## Overview
This setup provisions a managed Kubernetes cluster (EKS, GKE, or local via kind/minikube), deploys Prometheus for metrics collection, and Grafana for metrics visualization.  
It satisfies **NFR-4** and **NFR-6** from the Software Requirements Specification.

## Features
- Kubernetes cluster accessible via `kubectl`.
- Prometheus deployed and scraping cluster metrics.
- Grafana deployed and accessible through a browser.
- Preconfigured Grafana dashboard displaying CPU and memory usage for cluster nodes and pods.

## Prerequisites
- Docker installed and running.
- Kubernetes CLI (`kubectl`) installed and configured.
- Helm installed.
- Access to a Kubernetes cluster (EKS/GKE/minikube/kind).
- Internet connectivity to pull container images.

## Setup Instructions
1. **Navigate to the monitoring directory:**
   ```bash
   cd monitoring
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   This script performs the following:
   - Deploys Prometheus and Grafana using Helm.
   - Exposes Grafana via a LoadBalancer or NodePort (depending on cluster type).
   - Configures basic scraping for Kubernetes metrics.

3. **Access Grafana:**
   Once the script completes, open Grafana in your browser:
   ```
   https://x
   ```
   (Replace `x` with the actual address output by the setup script.)

4. **Import the Dashboard:**
   - Log in to Grafana (default credentials: `admin` / `admin`).
   - Navigate to **Dashboards → Import**.
   - Upload the provided `dashboard.json` file located in the same directory.
   - Click **Load**, then **Import** to make the dashboard visible.

5. **Verify Deployment:**
   - Check Prometheus targets:
     ```bash
     kubectl port-forward svc/prometheus-server 9090:80 -n monitoring
     ```
     Visit [http://localhost:9090](http://localhost:9090).
   - Check Grafana dashboard for cluster CPU/memory graphs.

## File Structure
```
monitoring/
├── setup.sh           # Automated setup script for Prometheus & Grafana
├── dashboard.json     # Grafana dashboard configuration
└── README.md          # This file
```

## Cleanup
To tear down the monitoring stack:
```bash
kubectl delete ns monitoring
```
