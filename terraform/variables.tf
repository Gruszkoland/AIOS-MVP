variable "aws_region" {
  description = "AWS region for infrastructure"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "adrion"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type for ECS"
  type        = string
  default     = "t3.medium"
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_multi_az" {
  description = "Enable RDS Multi-AZ"
  type        = bool
  default     = true
}

variable "enable_elasticache" {
  description = "Enable ElastiCache Redis"
  type        = bool
  default     = true
}

variable "dr_region" {
  description = "AWS region for disaster recovery (standby)"
  type        = string
  default     = "eu-west-1"
}

variable "rds_instance_class_dr" {
  description = "RDS instance class for DR standby"
  type        = string
  default     = "db.t3.small"
}

variable "rds_backup_retention" {
  description = "RDS backup retention in days"
  type        = number
  default     = 7
  validation {
    condition     = var.rds_backup_retention >= 1 && var.rds_backup_retention <= 35
    error_message = "Backup retention must be between 1 and 35 days."
  }
}

variable "dr_alert_email" {
  description = "Email for DR alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "force_dr_promotion" {
  description = "Force promote standby to primary (destructive)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default = {
    Project     = "ADRION 369"
    ManagedBy   = "Terraform"
    CreatedDate = "2026-05-27"
  }
}
