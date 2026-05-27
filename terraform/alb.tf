# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "prod"

  tags = merge(local.env_tags, {
    Name = "${local.name_prefix}-alb"
  })
}

# Target Group for API
resource "aws_lb_target_group" "api" {
  name        = "${local.name_prefix}-api-tg"
  port        = 8003
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  tags = local.env_tags
}

# Target Group for UAP
resource "aws_lb_target_group" "uap" {
  name        = "${local.name_prefix}-uap-tg"
  port        = 8002
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/mapi/v1/health"
    matcher             = "200"
  }

  tags = local.env_tags
}

# HTTP Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS Listener (requires certificate)
resource "aws_lb_listener" "https" {
  count             = var.environment == "prod" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate.main[0].arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# API path-based routing
resource "aws_lb_listener_rule" "api" {
  listener_arn = var.environment == "prod" ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# UAP path-based routing
resource "aws_lb_listener_rule" "uap" {
  listener_arn = var.environment == "prod" ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 2

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.uap.arn
  }

  condition {
    path_pattern {
      values = ["/mapi/*"]
    }
  }
}

# ACM Certificate (for HTTPS)
resource "aws_acm_certificate" "main" {
  count             = var.environment == "prod" ? 1 : 0
  domain_name       = "api.adrion369.dev"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = local.env_tags
}
