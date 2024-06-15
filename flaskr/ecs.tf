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

resource "aws_ecs_task_definition" "flaskr_app_task" {
  family                   = "flaskr-app-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "flaskr-app"
      image     = "193482034911.dkr.ecr.us-east-1.amazonaws.com/flaskr-app:latest"
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/flaskr-app"
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = [
        {
          name  = "DB_HOST"
          value = aws_db_instance.flaskr_db.address
        },
        {
          name  = "DB_PORT"
          value = "5432"
        },
        {
          name  = "DB_USER"
          value = "myuser"
        },
        {
          name  = "DB_PASSWORD"
          value = "mypassword"
        }
      ]
      command = ["/usr/local/bin/wait-for-it.sh", "db:5432", "--", "/flaskr/entrypoint.sh"]
    }
  ])
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
    container_port   = 80
  }
}