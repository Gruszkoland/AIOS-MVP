terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    # Configure via backend config at init time:
    # terraform init -backend-config="bucket=..." -backend-config="key=..." -backend-config="region=..."
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

provider "aws" {
  alias  = "dr"
  region = var.dr_region

  default_tags {
    tags = var.tags
  }
}

locals {
  env_tags = merge(var.tags, {
    Environment = var.environment
    Region      = var.aws_region
  })

  name_prefix = "${var.project_name}-${var.environment}"
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for available AZs
data "aws_availability_zones" "available" {
  state = "available"
}
