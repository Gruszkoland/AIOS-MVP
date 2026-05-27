environment = "dev"
aws_region  = "eu-central-1"
vpc_cidr    = "10.0.0.0/16"

instance_type        = "t3.medium"
ecs_desired_count    = 1
rds_allocated_storage = 50
rds_instance_class   = "db.t3.micro"
rds_multi_az         = false
enable_elasticache   = false

# Disaster Recovery (optional for dev)
dr_region              = "eu-west-1"
rds_instance_class_dr = "db.t3.micro"
rds_backup_retention  = 7
dr_alert_email        = ""
force_dr_promotion    = false

tags = {
  Project     = "ADRION 369"
  Environment = "dev"
  ManagedBy   = "Terraform"
  CreatedDate = "2026-05-27"
}
