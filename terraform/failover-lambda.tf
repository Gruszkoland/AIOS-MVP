# Lambda function for automated failover detection & notification

resource "aws_iam_role" "failover_lambda_role" {
  name = "${local.name_prefix}-failover-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.env_tags
}

resource "aws_iam_role_policy" "failover_lambda_policy" {
  name = "${local.name_prefix}-failover-lambda-policy"
  role = aws_iam_role.failover_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters",
          "rds:ListTagsForResource"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.dr_alerts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.env_tags
}

resource "aws_lambda_function" "failover_detector" {
  filename      = "lambda_failover_detector.zip"
  function_name = "${local.name_prefix}-failover-detector"
  role          = aws_iam_role.failover_lambda_role.arn
  handler       = "index.handler"
  runtime       = "python3.11"
  timeout       = 60

  environment {
    variables = {
      PRIMARY_DB_ID    = aws_db_instance.main.id
      STANDBY_DB_ID    = aws_db_instance.standby.id
      SNS_TOPIC_ARN    = aws_sns_topic.dr_alerts.arn
      ENVIRONMENT      = var.environment
      PRIMARY_REGION   = var.aws_region
      STANDBY_REGION   = var.dr_region
    }
  }

  tags = local.env_tags
}

# EventBridge rule: run failover detector every 5 minutes
resource "aws_cloudwatch_event_rule" "failover_check" {
  name                = "${local.name_prefix}-failover-check"
  description         = "Periodic failover readiness check"
  schedule_expression = "rate(5 minutes)"

  tags = local.env_tags
}

resource "aws_cloudwatch_event_target" "failover_lambda" {
  rule      = aws_cloudwatch_event_rule.failover_check.name
  target_id = "FailoverLambda"
  arn       = aws_lambda_function.failover_detector.arn
}

resource "aws_lambda_permission" "failover_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.failover_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.failover_check.arn
}

# Log group for Lambda
resource "aws_cloudwatch_log_group" "failover_logs" {
  name              = "/aws/lambda/${aws_lambda_function.failover_detector.function_name}"
  retention_in_days = 14

  tags = local.env_tags
}

# Alarm: Lambda execution errors
resource "aws_cloudwatch_metric_alarm" "failover_lambda_errors" {
  alarm_name          = "${local.name_prefix}-failover-lambda-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1

  dimensions = {
    FunctionName = aws_lambda_function.failover_detector.function_name
  }

  alarm_description = "Failover detector Lambda has errors"
  alarm_actions     = [aws_sns_topic.dr_alerts.arn]
  treat_missing_data = "notBreaching"

  tags = local.env_tags
}

output "failover_detector_lambda_arn" {
  description = "ARN of failover detector Lambda function"
  value       = aws_lambda_function.failover_detector.arn
}

output "failover_detector_log_group" {
  description = "CloudWatch log group for failover detector"
  value       = aws_cloudwatch_log_group.failover_logs.name
}
