# Monitoring Setup (Kubernetes + Prometheus + Grafana)

## Overview
This setup provisions a managed Kubernetes cluster, deploys Prometheus for metrics collection, and Grafana for metrics visualization.  
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
- Access to a Kubernetes cluster.
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
   http://localhost:30305/
   ```

4. **Import the Dashboard:**
   - Log in to Grafana (default credentials: `admin` / `aRiejzrACo35ZkzPgJry5Qly74hWaHfN5Jv8lJcV`). **Change these credentials immediately after the first login.**
   - Navigate to **Dashboards → Import**.
   - Upload the provided `dashboard.json` file located in the same directory.
   - Click **Load**, then **Import** to make the dashboard visible.

