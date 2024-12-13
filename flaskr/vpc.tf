data "aws_availability_zones" "available" {}

resource "aws_vpc" "flaskr_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "flaskr-vpc"
  }
}

resource "aws_internet_gateway" "flaskr_igw" {
  vpc_id = aws_vpc.flaskr_vpc.id

  tags = {
    Name = "flaskr-igw"
  }
}

resource "aws_route_table" "flaskr_public_rt" {
  vpc_id = aws_vpc.flaskr_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.flaskr_igw.id
  }

  tags = {
    Name = "flaskr-public-rt"
  }
}

resource "aws_subnet" "flaskr_public_subnet" {
  count                   = 2
  vpc_id                  = aws_vpc.flaskr_vpc.id
  cidr_block              = cidrsubnet(aws_vpc.flaskr_vpc.cidr_block, 8, count.index)
  availability_zone       = element(data.aws_availability_zones.available.names, count.index)
  map_public_ip_on_launch = true

  tags = {
    Name = "flaskr-public-subnet-${count.index}"
  }
}

resource "aws_route_table_association" "flaskr_public_rt_assoc" {
  count          = 2
  subnet_id      = element(aws_subnet.flaskr_public_subnet.*.id, count.index)
  route_table_id = aws_route_table.flaskr_public_rt.id
}

resource "aws_subnet" "flaskr_private_subnet" {
  count             = 2
  vpc_id            = aws_vpc.flaskr_vpc.id
  cidr_block        = cidrsubnet(aws_vpc.flaskr_vpc.cidr_block, 8, count.index + 2)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)

  tags = {
    Name = "flaskr-private-subnet-${count.index}"
  }
}

resource "aws_route_table" "flaskr_private_rt" {
  vpc_id = aws_vpc.flaskr_vpc.id

  tags = {
    Name = "flaskr-private-rt"
  }
}

resource "aws_route_table_association" "flaskr_private_rt_assoc" {
  count          = 2
  subnet_id      = element(aws_subnet.flaskr_private_subnet.*.id, count.index)
  route_table_id = aws_route_table.flaskr_private_rt.id
}

resource "aws_lb" "flaskr_app_alb" {
  name               = "flaskr-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.flaskr_alb_sg.id]
  subnets            = aws_subnet.flaskr_public_subnet[*].id

  enable_deletion_protection = true

  tags = {
    Name = "flaskr-alb"
  }
}

resource "aws_lb_target_group" "flaskr_app_tg" {
  name        = "flaskr-app-tg"
  port        = 5000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.flaskr_vpc.id
  target_type = "ip"

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }

  tags = {
    Name = "flaskr-tg"
  }
}

resource "aws_lb_listener" "flaskr_app_http_listener" {
  load_balancer_arn = aws_lb.flaskr_app_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      protocol    = "HTTPS"
      port        = "443"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "flaskr_app_https_listener" {
  load_balancer_arn = aws_lb.flaskr_app_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.flaskr_app_tg.arn
  }
}

resource "aws_route53_record" "flaskr_alb" {
  zone_id = "Z1013243V3H94OXCQ2KV"
  name    = "ops76.co"
  type    = "A"

  alias {
    name                   = aws_lb.flaskr_app_alb.dns_name
    zone_id                = aws_lb.flaskr_app_alb.zone_id
    evaluate_target_health = true
  }
}