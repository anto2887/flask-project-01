# eventbridge.tf

# EventBridge rule for daily updates
resource "aws_cloudwatch_event_rule" "daily_update" {
  name                = "flaskr-daily-update"
  description         = "Trigger daily fixture updates"
  schedule_expression = "cron(0 8 * * ? *)"  # 8 AM UTC daily

  tags = {
    Name = "flaskr-daily-update"
  }
}

# EventBridge rule for live match updates
resource "aws_cloudwatch_event_rule" "live_match_update" {
  name                = "flaskr-live-match-update"
  description         = "Check for live match updates"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Name = "flaskr-live-match-update"
  }
}

# IAM role for EventBridge to invoke ECS tasks
resource "aws_iam_role" "eventbridge_role" {
  name = "flaskr-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for EventBridge to run ECS tasks
resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "flaskr-eventbridge-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = [
          aws_ecs_task_definition.flaskr_app_task.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution_role.arn,
          aws_iam_role.ecs_task_role.arn
        ]
      }
    ]
  })
}

# EventBridge targets for daily update
resource "aws_cloudwatch_event_target" "daily_update_target" {
  rule      = aws_cloudwatch_event_rule.daily_update.name
  target_id = "FlaskrDailyUpdate"
  arn       = aws_ecs_cluster.flaskr_ecs_cluster.arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.flaskr_app_task.arn
    launch_type         = "FARGATE"
    network_configuration {
      subnets          = aws_subnet.flaskr_private_subnet[*].id
      security_groups  = [aws_security_group.flaskr_ecs_sg.id]
      assign_public_ip = true
    }
  }

  input = jsonencode({
    containerOverrides = [
      {
        name    = "flaskr-app"
        command = ["/usr/local/bin/python", "-c", "from app.date_utils import daily_update; daily_update()"]
      }
    ]
  })
}

# EventBridge target for live match updates
resource "aws_cloudwatch_event_target" "live_match_target" {
  rule      = aws_cloudwatch_event_rule.live_match_update.name
  target_id = "FlaskrLiveMatchUpdate"
  arn       = aws_ecs_cluster.flaskr_ecs_cluster.arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.flaskr_app_task.arn
    launch_type         = "FARGATE"
    network_configuration {
      subnets          = aws_subnet.flaskr_private_subnet[*].id
      security_groups  = [aws_security_group.flaskr_ecs_sg.id]
      assign_public_ip = true
    }
  }

  input = jsonencode({
    containerOverrides = [
      {
        name    = "flaskr-app"
        command = ["/usr/local/bin/python", "-c", "from app.api_client import process_live_scores; process_live_scores()"]
      }
    ]
  })
}