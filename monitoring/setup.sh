winget install Helm.Helm

# Installing Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/prometheus

kubectl expose service prometheus-server --type=NodePort --target-port=9090 --name=prometheus-server-ext

# Installing Grafana
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install grafana grafana/grafana

kubectl expose service grafana --type=NodePort --target-port=3000 --name=grafana-ext
kubectl port-forward svc/grafana-ext 30305:80
