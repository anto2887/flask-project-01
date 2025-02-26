resource "aws_ecs_cluster" "flaskr_ecs_cluster" {
  name = "flaskr-ecs-cluster"
}

# Create a new secret with a fixed name instead of random suffix
resource "aws_secretsmanager_secret" "api_football_key" {
  name = "api-football-key"  # Use a fixed name that matches what your app expects

  lifecycle {
    create_before_destroy = true
  }
}

# Add the secret value to the newly created secret
resource "aws_secretsmanager_secret_version" "api_football_key" {
  secret_id     = aws_secretsmanager_secret.api_football_key.id
  secret_string = var.api_football_key_value
}

# IAM role for ECS task execution
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

# Attach the Amazon ECS task execution role policy
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Attach policy to allow ECS tasks to access Secrets Manager
resource "aws_iam_role_policy_attachment" "ecs_task_execution_secrets_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access_policy.arn
}

# Define IAM policy for Secrets Manager access
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
        Resource = [
          aws_secretsmanager_secret.api_football_key.arn
        ]
      }
    ]
  })
}

# Define ECS task role
resource "aws_iam_role" "ecs_task_role" {
  name = "flaskr_ecs_task_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Attach Secrets Manager access policy to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_task_secrets_policy" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.secrets_access_policy.arn
}

# Define local variables for database connection and container definitions
locals {
  db_user                 = "myuser"
  db_password             = "mypassword"
  db_host                 = aws_db_instance.flaskr_db.address
  db_port                 = "5432"
  sqlalchemy_database_uri = "postgresql://${local.db_user}:${local.db_password}@${local.db_host}:${local.db_port}/flaskrdb"

  # Container definitions populated from a template file
  container_definitions = templatefile("${path.module}/container_definitions.json.tpl", {
    frontend_image          = "193482034911.dkr.ecr.us-east-1.amazonaws.com/flaskr-frontend:latest"
    backend_image           = "193482034911.dkr.ecr.us-east-1.amazonaws.com/flaskr-backend:latest"
    awslogs_group           = "/ecs/flaskr-app"
    awslogs_region          = var.region
    awslogs_stream_prefix   = "ecs"
    db_host                 = local.db_host
    db_port                 = local.db_port
    db_user                 = local.db_user
    db_password             = local.db_password
    sqlalchemy_database_uri = local.sqlalchemy_database_uri
    api_football_key_arn    = aws_secretsmanager_secret.api_football_key.arn
    api_football_key_name   = aws_secretsmanager_secret.api_football_key.name
    redis_endpoint          = aws_elasticache_cluster.redis.cache_nodes[0].address
  })
}

# Define ECS task definition
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

# Define ECS service
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