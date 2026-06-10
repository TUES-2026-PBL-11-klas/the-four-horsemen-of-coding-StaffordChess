#!/bin/bash

echo "Configuring context for kubectl..."
#kubectl config use-context docker-desktop
kubectl config use-context stafford-chess-cluster


echo "test_1"

echo "Starting port forwarding to ArgoCD server..."
kubectl port-forward svc/argocd-server -n argocd 8080:443

echo "test_2"

echo "Waiting for ArgoCd password..."
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

echo "test_3"

echo "Starting port forwarding to Prometheus, Grafana, and Loki..."
kubectl port-forward -n observability svc/prometheus 9090:9090
kubectl port-forward -n observability svc/grafana 3000:3000
kubectl port-forward -n observability svc/loki 3100:3100

echo