environment = "prod"
aws_region  = "eu-central-1"
vpc_cidr    = "10.0.0.0/16"

instance_type          = "t3.large"
ecs_desired_count      = 3
rds_allocated_storage  = 500
rds_instance_class     = "db.t3.large"
rds_multi_az           = true
enable_elasticache     = true

# Disaster Recovery (active for production)
dr_region              = "eu-west-1"
rds_instance_class_dr = "db.t3.large"
rds_backup_retention  = 30
dr_alert_email        = "ops-team@adrion369.dev"
force_dr_promotion    = false

tags = {
  Project     = "ADRION 369"
  Environment = "prod"
  ManagedBy   = "Terraform"
  CreatedDate = "2026-05-27"
  CostCenter  = "ADRION"
}
