# Kubernetes Secrets Management

## IMPORTANT: Do NOT commit real secrets to version control!

All Secret resources in `configmap-secrets.yaml` use placeholder values (`CHANGE_ME_IN_PRODUCTION`).

## How to create secrets in production:

```bash
# PostgreSQL
kubectl create secret generic postgres-credentials -n adrion-369 \
  --from-literal=POSTGRES_USER=adrion \
  --from-literal=POSTGRES_PASSWORD=<your-secure-password> \
  --from-literal=POSTGRES_DB=genesis_record

# Grafana
kubectl create secret generic grafana-credentials -n adrion-369 \
  --from-literal=GF_SECURITY_ADMIN_USER=admin \
  --from-literal=GF_SECURITY_ADMIN_PASSWORD=<your-secure-password>

# n8n
kubectl create secret generic n8n-credentials -n adrion-369 \
  --from-literal=N8N_ADMIN_PASSWORD=<your-secure-password>

# Alerting webhooks
kubectl create secret generic alerting-webhooks -n adrion-369 \
  --from-literal=SLACK_WEBHOOK_URL=<your-webhook-url> \
  --from-literal=PAGERDUTY_KEY=<your-key>
```

## Alternative: Use sealed-secrets or external-secrets-operator for GitOps workflows.
