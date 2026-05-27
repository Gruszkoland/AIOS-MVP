# Disaster Recovery — Cross-Region RDS Replication

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  alias  = "dr"
  region = var.dr_region
}

# Data source: primary RDS instance
data "aws_db_instance" "primary" {
  db_instance_identifier = aws_db_instance.main.id
}

# Cross-region read replica (standby)
resource "aws_db_instance" "standby" {
  provider              = aws.dr
  identifier            = "${local.name_prefix}-standby"
  replicate_source_db   = aws_db_instance.main.identifier
  instance_class        = var.rds_instance_class_dr
  publicly_accessible   = false
  skip_final_snapshot   = var.environment == "dev"
  backup_retention_days = var.rds_backup_retention

  tags = merge(
    local.env_tags,
    {
      Name = "${local.name_prefix}-standby-${var.dr_region}"
      Role = "DR-Standby"
    }
  )

  depends_on = [aws_db_instance.main]
}

# Enhanced failover: enable automatic failover for production
resource "aws_db_instance_automated_backups_replication" "main" {
  count              = var.environment == "prod" ? 1 : 0
  source_db_instance = aws_db_instance.main.arn
  target_region      = var.dr_region
  retention_period   = var.rds_backup_retention

  tags = local.env_tags
}

# RDS event subscription for replication lag monitoring
resource "aws_db_event_subscription" "replication_lag" {
  provider    = aws.dr
  name        = "${local.name_prefix}-replication-lag"
  sns_topic   = aws_sns_topic.dr_alerts.arn
  source_type = "db-instance"

  event_categories = [
    "availability",
    "failover",
    "failure",
    "maintenance"
  ]

  tags = local.env_tags
}

# SNS topic for DR alerts
resource "aws_sns_topic" "dr_alerts" {
  provider = aws.dr
  name     = "${local.name_prefix}-dr-alerts"

  tags = local.env_tags
}

resource "aws_sns_topic_subscription" "dr_alerts_email" {
  count     = var.environment == "prod" ? 1 : 0
  provider  = aws.dr
  topic_arn = aws_sns_topic.dr_alerts.arn
  protocol  = "email"
  endpoint  = var.dr_alert_email
}

# CloudWatch alarm: Replication lag (primary → standby)
resource "aws_cloudwatch_metric_alarm" "replication_lag" {
  provider            = aws.dr
  alarm_name          = "${local.name_prefix}-rds-replication-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "AuroraBinlogReplicaLag"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 5000  # milliseconds (5 seconds)

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.standby.id
  }

  alarm_description = "RDS replication lag exceeds 5 seconds"
  alarm_actions     = [aws_sns_topic.dr_alerts.arn]
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}

# Promote standby to primary (manual intervention trigger)
resource "aws_db_instance" "promoted_standby" {
  count                    = var.force_dr_promotion ? 1 : 0
  provider                 = aws.dr
  skip_final_snapshot      = true
  backup_retention_period  = 0
  identifier               = "${local.name_prefix}-promoted"

  tags = merge(
    local.env_tags,
    { Name = "${local.name_prefix}-promoted-standby" }
  )

  lifecycle {
    ignore_changes = [identifier]
  }

  depends_on = [aws_db_instance.standby]
}

# Backup vault for cross-region retention
resource "aws_backup_vault" "dr_vault" {
  provider    = aws.dr
  name        = "${local.name_prefix}-dr-vault"
  kms_key_arn = aws_kms_key.dr_backup.arn

  tags = local.env_tags
}

# KMS key for DR backup encryption
resource "aws_kms_key" "dr_backup" {
  provider                = aws.dr
  description             = "KMS key for ${local.name_prefix} DR backups"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = local.env_tags
}

resource "aws_kms_alias" "dr_backup" {
  provider      = aws.dr
  name          = "alias/${local.name_prefix}-dr-backup"
  target_key_id = aws_kms_key.dr_backup.key_id
}

# Backup plan for automated cross-region snapshots
resource "aws_backup_plan" "dr_plan" {
  provider = aws.dr
  name     = "${local.name_prefix}-dr-backup-plan"

  rule {
    rule_name         = "daily_backup"
    target_backup_vault_name = aws_backup_vault.dr_vault.name
    schedule          = "cron(0 3 * * ? *)"  # 3 AM UTC daily
    start_window      = 60
    completion_window = 120

    lifecycle {
      cold_storage_after = var.environment == "prod" ? 30 : 0
      delete_after       = var.rds_backup_retention
    }

    copy_action {
      destination_vault_arn = aws_backup_vault.dr_vault.arn
    }
  }

  tags = local.env_tags
}

# Backup selection for RDS
resource "aws_backup_selection" "rds_selection" {
  provider      = aws.dr
  name          = "${local.name_prefix}-rds-selection"
  plan_id       = aws_backup_plan.dr_plan.id
  iam_role_arn  = aws_iam_role.backup_role.arn
  db_instance_identifiers = [aws_db_instance.standby.identifier]

  tags = local.env_tags
}

# IAM role for backup service
resource "aws_iam_role" "backup_role" {
  provider = aws.dr
  name     = "${local.name_prefix}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = local.env_tags
}

resource "aws_iam_role_policy_attachment" "backup_policy" {
  provider       = aws.dr
  role           = aws_iam_role.backup_role.name
  policy_arn     = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

# Route53 health check for failover routing
resource "aws_route53_health_check" "primary_db" {
  provider              = aws.dr
  type                  = "CLOUDWATCH_METRIC"
  cloudwatch_alarm_name = aws_cloudwatch_metric_alarm.rds_cpu.alarm_name
  cloudwatch_alarm_region = var.aws_region
  measure_latency       = true

  tags = local.env_tags
}

# Parameter group for standby (read-only mode initially)
resource "aws_db_parameter_group" "standby" {
  provider   = aws.dr
  name       = "${local.name_prefix}-standby-params"
  family     = "postgres15"
  description = "Parameter group for DR standby (read-only replica)"

  parameter {
    name  = "shared_preload_libraries"
    value = "pgaudit,pg_stat_statements"
  }

  tags = local.env_tags
}

# Output for DR setup
output "standby_endpoint" {
  description = "RDS standby endpoint (read-only replica)"
  value       = aws_db_instance.standby.endpoint
  sensitive   = true
}

output "standby_arn" {
  description = "ARN of standby RDS instance"
  value       = aws_db_instance.standby.arn
}

output "dr_region" {
  description = "DR region for standby deployment"
  value       = var.dr_region
}

output "backup_vault_arn" {
  description = "ARN of DR backup vault"
  value       = aws_backup_vault.dr_vault.arn
}

output "rpo_minutes" {
  description = "Recovery Point Objective (backup frequency)"
  value       = 1440 / 1  # Daily = 1440 minutes
}

output "rto_minutes" {
  description = "Recovery Time Objective (estimated failover time)"
  value       = var.environment == "prod" ? 5 : 15
}
