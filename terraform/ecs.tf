# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.env_tags
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = local.env_tags
}

# IAM role for ECS task execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${local.name_prefix}-ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.env_tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM role for ECS task (application permissions)
resource "aws_iam_role" "ecs_task_role" {
  name = "${local.name_prefix}-ecsTaskRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.env_tags
}

# Task Definition for ADRION API
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "adrion-api"
      image     = "ghcr.io/adiha/adrion:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8003
          hostPort      = 8003
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
      environment = [
        {
          name  = "DB_ENGINE"
          value = "postgres"
        },
        {
          name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
          value = "http://jaeger:4317"
        }
      ]
    }
  ])

  tags = local.env_tags
}

# Task Definition for UAP
resource "aws_ecs_task_definition" "uap" {
  family                   = "${local.name_prefix}-uap"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "adrion-uap"
      image     = "ghcr.io/adiha/adrion-uap:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8002
          hostPort      = 8002
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "uap"
        }
      }
      environment = [
        {
          name  = "MAPI_HOST"
          value = "0.0.0.0"
        },
        {
          name  = "MAPI_PORT"
          value = "8002"
        },
        {
          name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
          value = "http://jaeger:4317"
        }
      ]
    }
  ])

  tags = local.env_tags
}

# ECS Service for API
resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "adrion-api"
    container_port   = 8003
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = local.env_tags
}

# ECS Service for UAP
resource "aws_ecs_service" "uap" {
  name            = "${local.name_prefix}-uap-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.uap.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.uap.arn
    container_name   = "adrion-uap"
    container_port   = 8002
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.ecs_task_role_policy
  ]

  tags = local.env_tags
}

# IAM policy for ECS task role (S3, CloudWatch, etc.)
resource "aws_iam_role_policy" "ecs_task_role_policy" {
  name   = "${local.name_prefix}-ecsTaskRolePolicy"
  role   = aws_iam_role.ecs_task_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}
