data "aws_availability_zones" "available" {}

resource "aws_vpc" "flaskr_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true
}

resource "aws_internet_gateway" "flaskr_igw" {
  vpc_id = aws_vpc.flaskr_vpc.id
}

resource "aws_route_table" "flaskr_public_rt" {
  vpc_id = aws_vpc.flaskr_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.flaskr_igw.id
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
}

resource "aws_route_table_association" "flaskr_private_rt_assoc" {
  count          = 2
  subnet_id      = element(aws_subnet.flaskr_private_subnet.*.id, count.index)
  route_table_id = aws_route_table.flaskr_private_rt.id
}

# VPC Endpoints for ECR and other services
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id            = aws_vpc.flaskr_vpc.id
  service_name      = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.flaskr_private_subnet[*].id
  security_group_ids = [aws_security_group.flaskr_vpc_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id            = aws_vpc.flaskr_vpc.id
  service_name      = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type = "Interface"
  subnet_ids        = aws_subnet.flaskr_private_subnet[*].id
  security_group_ids = [aws_security_group.flaskr_vpc_sg.id]
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.flaskr_vpc.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.flaskr_private_rt.id]
}

resource "aws_lb" "flaskr_app_alb" {
  name               = "flaskr-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.flaskr_alb_sg.id]
  subnets            = aws_subnet.flaskr_public_subnet[*].id
}

resource "aws_lb_target_group" "flaskr_app_tg" {
  name         = "flaskr-app-tg"
  port         = 80
  protocol     = "HTTP"
  vpc_id       = aws_vpc.flaskr_vpc.id
  target_type  = "ip"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}

resource "aws_lb_listener" "flaskr_app_listener" {
  load_balancer_arn = aws_lb.flaskr_app_alb.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.flaskr_app_tg.arn
  }
}
