# CloudWatch Alarms for RDS
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${local.name_prefix}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  alarm_description = "RDS CPU utilization is high"
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${local.name_prefix}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.rds_allocated_storage * 1024 * 1024 * 1024 * 0.1

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  alarm_description = "RDS free storage space is low (< 10%)"
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}

# CloudWatch Alarms for ECS
resource "aws_cloudwatch_metric_alarm" "ecs_api_cpu" {
  alarm_name          = "${local.name_prefix}-ecs-api-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 70

  dimensions = {
    ServiceName = aws_ecs_service.api.name
    ClusterName = aws_ecs_cluster.main.name
  }

  alarm_description = "ECS API CPU utilization is high"
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_api_memory" {
  alarm_name          = "${local.name_prefix}-ecs-api-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    ServiceName = aws_ecs_service.api.name
    ClusterName = aws_ecs_cluster.main.name
  }

  alarm_description = "ECS API memory utilization is high"
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}

# CloudWatch Alarms for ALB
resource "aws_cloudwatch_metric_alarm" "alb_target_count" {
  alarm_name          = "${local.name_prefix}-alb-unhealthy-targets"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }

  alarm_description = "ALB has unhealthy targets"
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}
