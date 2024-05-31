resource "aws_vpc" "flaskr_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "flaskr_public_subnet" {
  count                   = 2
  vpc_id                  = aws_vpc.flaskr_vpc.id
  cidr_block              = cidrsubnet(aws_vpc.flaskr_vpc.cidr_block, 8, count.index)
  availability_zone       = element(data.aws_availability_zones.available.names, count.index)
  map_public_ip_on_launch = true
}

resource "aws_subnet" "flaskr_private_subnet" {
  count             = 2
  vpc_id            = aws_vpc.flaskr_vpc.id
  cidr_block        = cidrsubnet(aws_vpc.flaskr_vpc.cidr_block, 8, count.index + 2)
  availability_zone = element(data.aws_availability_zones.available.names, count.index)
}

resource "aws_lb" "flaskr_app_alb" {
  name               = "flaskr-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.flaskr_alb_sg.id]
  subnets            = aws_subnet.flaskr_public_subnet[*].id
}

resource "aws_lb_target_group" "flaskr_app_tg" {
  name     = "flaskr-app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.flaskr_vpc.id

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
