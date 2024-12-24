# Security group for Application Load Balancer
resource "aws_security_group" "flaskr_alb_sg" {
  name        = "flaskr-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.flaskr_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for ECS instances
resource "aws_security_group" "flaskr_ecs_sg" {
  name        = "flaskr-ecs-sg"
  description = "Security group for ECS instances"
  vpc_id      = aws_vpc.flaskr_vpc.id

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.flaskr_alb_sg.id]
  }

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.flaskr_alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for RDS
resource "aws_security_group" "flaskr_rds_sg" {
  name        = "flaskr-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.flaskr_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.flaskr_ecs_sg.id]
  }

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.flaskr_bastion_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security group for Bastion Host
resource "aws_security_group" "flaskr_bastion_sg" {
  name        = "flaskr-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = aws_vpc.flaskr_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["185.207.249.146/32"]  # Replace with your IP
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
