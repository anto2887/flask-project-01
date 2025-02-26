[
  {
    "name": "frontend-app",
    "image": "${frontend_image}",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 80,
        "hostPort": 80,
        "protocol": "tcp"
      },
      {
        "containerPort": 443,
        "hostPort": 443,
        "protocol": "tcp"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${awslogs_group}",
        "awslogs-region": "${awslogs_region}",
        "awslogs-stream-prefix": "frontend"
      }
    },
    "healthCheck": {
      "command": [
        "CMD-SHELL",
        "curl -f http://localhost/health || exit 1"
      ],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    },
    "memory": 256,
    "cpu": 128
  },
  {
    "name": "flaskr-app",
    "image": "${backend_image}",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 5000,
        "hostPort": 5000,
        "protocol": "tcp"
      }
    ],
    "environment": [
      {"name": "FLASK_ENV", "value": "production"},
      {"name": "DB_HOST", "value": "${db_host}"},
      {"name": "DB_PORT", "value": "${db_port}"},
      {"name": "DB_NAME", "value": "flaskrdb"},
      {"name": "DB_USER", "value": "${db_user}"},
      {"name": "DB_PASSWORD", "value": "${db_password}"},
      {"name": "SQLALCHEMY_DATABASE_URI", "value": "${sqlalchemy_database_uri}"},
      {"name": "REDIS_HOST", "value": "${redis_endpoint}"},
      {"name": "REDIS_PORT", "value": "6379"},
      {"name": "CREATE_TABLES_ON_STARTUP", "value": "True"},
      {"name": "SECRET_NAME", "value": "api-football-key"},
      {"name": "SCORE_PROCESSOR_TYPE", "value": "default"}
    ],
    "secrets": [
      {
        "name": "API_FOOTBALL_KEY",
        "valueFrom": "${api_football_key_arn}"
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${awslogs_group}",
        "awslogs-region": "${awslogs_region}",
        "awslogs-stream-prefix": "backend"
      }
    },
    "healthCheck": {
      "command": [
        "CMD-SHELL",
        "curl -f http://localhost:5000/health || exit 1"
      ],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    },
    "memory": 256,
    "cpu": 128
  }
]