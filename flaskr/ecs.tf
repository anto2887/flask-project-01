data "aws_secretsmanager_secret" "existing_secrets" {
  name = "football_api_key"
}

locals {
  secret_exists = length(data.aws_secretsmanager_secret.existing_secrets) > 0
  secret_id     = local.secret_exists ? data.aws_secretsmanager_secret.existing_secrets.id : aws_secretsmanager_secret.api_football_key.id
}

resource "random_id" "secret_suffix" {
  byte_length = 8
}

resource "aws_secretsmanager_secret" "api_football_key" {
  name = local.secret_exists ? data.aws_secretsmanager_secret.existing_secrets.name : "football_api_key_${random_id.secret_suffix.hex}"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "api_football_key" {
  secret_id     = local.secret_id
  secret_string = var.api_football_key_value
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "flaskr_ecs_task_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_secrets_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access_policy.arn
}

resource "aws_iam_policy" "secrets_access_policy" {
  name        = "flaskr_secrets_access_policy"
  description = "Policy to allow ECS tasks to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Resource = local.secret_id
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "flaskr_ecs_task_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_ecs_cluster" "flaskr_ecs_cluster" {
  name = "flaskr-ecs-cluster"
}

locals {
  db_user                 = "myuser"
  db_password             = "mypassword"
  db_host                 = aws_db_instance.flaskr_db.address
  db_port                 = "5432"
  sqlalchemy_database_uri = "postgresql://${local.db_user}:${local.db_password}@${local.db_host}:${local.db_port}/flaskrdb"
  container_definitions = templatefile("${path.module}/container_definitions.json.tpl", {
    image                   = "193482034911.dkr.ecr.us-east-1.amazonaws.com/flaskr-app:latest"
    awslogs_group           = "/ecs/flaskr-app"
    awslogs_region          = var.region
    awslogs_stream_prefix   = "ecs"
    db_host                 = local.db_host
    db_port                 = local.db_port
    db_user                 = local.db_user
    db_password             = local.db_password
    sqlalchemy_database_uri = local.sqlalchemy_database_uri
    api_football_key_arn    = local.secret_id
  })
}

resource "aws_ecs_task_definition" "flaskr_app_task" {
  family                   = "flaskr-app-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = local.container_definitions

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}

resource "aws_ecs_service" "flaskr_ecs_service" {
  name            = "flaskr-ecs-service"
  cluster         = aws_ecs_cluster.flaskr_ecs_cluster.id
  task_definition = aws_ecs_task_definition.flaskr_app_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.flaskr_public_subnet[*].id
    security_groups  = [aws_security_group.flaskr_ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.flaskr_app_tg.arn
    container_name   = "flaskr-app"
    container_port   = 5000
  }
}