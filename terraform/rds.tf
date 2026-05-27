# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(local.env_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier            = "${local.name_prefix}-db"
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = var.rds_instance_class
  allocated_storage    = var.rds_allocated_storage
  db_name              = "adrion"
  username             = "postgres"
  password             = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az               = var.rds_multi_az
  publicly_accessible    = false

  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${local.name_prefix}-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn

  enabled_cloudwatch_logs_exports = ["postgresql"]

  deletion_protection = var.environment == "prod"

  tags = merge(local.env_tags, {
    Name = "${local.name_prefix}-db"
  })

  depends_on = [aws_db_subnet_group.main]
}

# KMS key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = local.env_tags
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for RDS credentials
resource "aws_secretsmanager_secret" "db" {
  name                    = "${local.name_prefix}/rds/credentials"
  recovery_window_in_days = 7

  tags = local.env_tags
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.main.endpoint
    port     = 5432
    dbname   = aws_db_instance.main.db_name
  })
}
