# Terraform Infrastructure as Code — ADRION 369

Terraform configuration for AWS cloud provisioning of ADRION 369 system.

## Architecture

```
AWS Primary Region (eu-central-1)
├── VPC (10.0.0.0/16)
│   ├── Public Subnets (2 AZ) — NAT Gateway, ALB
│   ├── Private Subnets (2 AZ) — ECS, RDS
│   ├── ALB → API/UAP target groups
│   ├── ECS Cluster
│   │   ├── API service (FARGATE, 512 CPU / 1GB RAM)
│   │   └── UAP service (FARGATE, 512 CPU / 1GB RAM)
│   └── RDS PostgreSQL (Multi-AZ, 15.4, encrypted)
│
└── Replication Flow (Production only)
    ├── Primary RDS → Standby RDS (async, eu-west-1)
    ├── Replication lag monitoring (< 5 sec threshold)
    ├── Automated daily backups → Backup Vault (KMS)
    ├── CloudWatch alarms & SNS alerts
    └── Lambda failover detector (runs every 5 min)

AWS Standby Region (eu-west-1) — Prod only
├── Standby RDS (read-only replica, same class)
├── Backup Vault (KMS-encrypted, 30-day retention)
└── SNS Topic (DR alerts)
```

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with credentials
- AWS account with appropriate permissions

## Environment Setup

### Dev Deployment

```bash
cd terraform
terraform init -backend-config="bucket=adrion-tf-state-dev" \
  -backend-config="key=dev/terraform.tfstate" \
  -backend-config="region=eu-central-1"

terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/dev.tfvars"
```

### Production Deployment

```bash
terraform init -backend-config="bucket=adrion-tf-state-prod" \
  -backend-config="key=prod/terraform.tfstate" \
  -backend-config="region=eu-central-1" \
  -backend-config="dynamodb_table=terraform-locks"

terraform plan -var-file="environments/prod.tfvars"
terraform apply -var-file="environments/prod.tfvars"
```

### Disaster Recovery Deployment

Production environments enable cross-region replication to `eu-west-1`:

```bash
# Apply DR configuration (creates standby replica)
terraform apply -var-file="environments/prod.tfvars"

# Verify standby replication
aws rds describe-db-instances \
  --db-instance-identifier adrion-standby \
  --region eu-west-1 \
  --query 'DBInstances[0].[DBInstanceStatus,AvailabilityZone]'

# Monitor replication lag
watch -n 5 'aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name AuroraBinlogReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=adrion-standby \
  --start-time $(date -u -d "10 min ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average \
  --region eu-west-1 \
  --query "Datapoints[0].Average"'
```

**See [`docs/RECOVERY_PLAN.md`](../docs/RECOVERY_PLAN.md) for full DR procedures, RTO/RPO targets, and failover runbooks.**

## Disaster Recovery Targets

| Metric                       | Dev    | Prod   |
|------------------------------|--------|--------|
| **RPO** (Recovery Point Obj) | 24 hrs | 24 hrs |
| **RTO** (Recovery Time Obj)  | 15 min | 5 min  |
| **Backup Retention**         | 7 days | 30 days|
| **Replication Lag Target**   | N/A    | < 5 s  |
| **Failover Automation**      | Manual | Lambda |
| **Multi-Region Replica**     | No     | Yes    |

## Terraform State Management

State is stored in **S3 with DynamoDB locking**:
- Bucket: `adrion-tf-state-{environment}`
- Key: `{environment}/terraform.tfstate`
- Lock table: `terraform-locks`
- Encryption: KMS enabled

**Create S3 bucket and lock table manually:**

```bash
# S3 bucket for state
aws s3api create-bucket \
  --bucket adrion-tf-state-dev \
  --region eu-central-1 \
  --create-bucket-configuration LocationConstraint=eu-central-1

aws s3api put-bucket-versioning \
  --bucket adrion-tf-state-dev \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket adrion-tf-state-dev \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

# DynamoDB lock table
aws dynamodb create-table \
  --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-central-1
```

## Resource Overview

| Component | Dev | Prod |
|-----------|-----|------|
| **ECS Tasks** | 1 | 3 |
| **Instance Type** | t3.medium | t3.large |
| **RDS Storage** | 50 GB | 500 GB |
| **RDS Multi-AZ** | No | Yes |
| **RDS Retention** | 7 days | 30 days |
| **ALB Deletion Protection** | No | Yes |

## Outputs

After `terraform apply`, retrieve outputs:

```bash
terraform output alb_dns_name
terraform output rds_endpoint
terraform output db_secret_arn
```

## Security

- ✅ RDS encryption with KMS
- ✅ Secrets Manager for credentials
- ✅ Security groups with least privilege
- ✅ NAT Gateway for private subnet egress
- ✅ CloudWatch alarms for monitoring
- ✅ VPC flow logs (optional, add to vpc.tf)

## Monitoring & Alarms

CloudWatch alarms configured for:
- RDS CPU utilization > 80%
- RDS free storage < 10%
- ECS API CPU > 70%
- ECS API memory > 80%
- ALB unhealthy targets

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy -var-file="environments/prod.tfvars"
```

**WARNING:** This deletes all resources including the RDS database (snapshot saved in production).

## Notes

- ACM certificate requires DNS validation (production only)
- Update `api.adrion369.dev` DNS records to point to ALB
- Enable HTTPS after certificate validation
- Consider adding CloudFront CDN for edge caching
- RDS backups retained for 7 (dev) / 30 (prod) days
