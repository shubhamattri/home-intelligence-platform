# Deploying

## Local (docker-compose)

```bash
make compose-up      # gateway + 4 services + redis + 2 Postgres + loaders
# platform entrypoint: http://localhost:8080
#   POST /dec/decision, GET /re/corridors, GET /hosp/hospitals/quality, POST /sch/schools/shortlist
# Traefik dashboard:   http://localhost:8081
```

The one-shot loaders (`re-loader`, `sch-loader`) ingest the JSON snapshots into
Postgres before the apps start. Set `TOMTOM_API_KEY` in the environment to enable
real peak-traffic drive times.

## Kubernetes (Helm)

Chart: `deploy/helm/bhi`. Validate and render:

```bash
helm lint deploy/helm/bhi
helm template bhi deploy/helm/bhi | less
```

Install (after building + pushing the per-service images to `image.repository`):

```bash
helm install bhi deploy/helm/bhi -n bhi --create-namespace
```

The chart creates, per service: a Deployment, Service, HPA (CPU-targeted), and a
Prometheus `ServiceMonitor`. It creates a StatefulSet + Service per Postgres
(DB-per-service), a Redis Deployment, and an Ingress routing `/re /hosp /sch /dec`.

## Observability

Every service exposes Prometheus metrics at `/metrics` (request count + latency
histogram, added by `service_kit`). The `ServiceMonitor` objects are picked up by
a `kube-prometheus-stack` install (label `release: prometheus`). Logs are JSON
(structlog) and collected by Loki/Promtail if deployed. `metrics.serviceMonitor=false`
disables the monitors if Prometheus Operator is absent.

## CI

`.github/workflows/ci.yml` runs on push/PR: ruff lint + format check, mypy `--strict`,
pytest, compose-config validation, and a matrix build of all four service images.
