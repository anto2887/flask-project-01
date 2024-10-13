[
  {
    "name": "flaskr-app",
    "image": "${image}",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 5000,
        "hostPort": 5000
      }
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${awslogs_group}",
        "awslogs-region": "${awslogs_region}",
        "awslogs-stream-prefix": "${awslogs_stream_prefix}"
      }
    },
    "environment": [
      {
        "name": "FLASK_APP",
        "value": "app"
      },
      {
        "name": "PYTHONPATH",
        "value": "/flaskr"
      },
      {
        "name": "CREATE_TABLES_ON_STARTUP",
        "value": "True"
      },
      {
        "name": "DB_HOST",
        "value": "${db_host}"
      },
      {
        "name": "DB_PORT",
        "value": "${db_port}"
      },
      {
        "name": "DB_USER",
        "value": "${db_user}"
      },
      {
        "name": "DB_PASSWORD",
        "value": "${db_password}"
      },
      {
        "name": "SQLALCHEMY_DATABASE_URI",
        "value": "${sqlalchemy_database_uri}"
      }
    ],
    "secrets": [
      {
        "name": "API_FOOTBALL_KEY",
        "valueFrom": "${api_football_key_arn}"
      }
    ],
    "command": [
      "/usr/local/bin/wait-for-it.sh",
      "${db_host}:${db_port}",
      "--",
      "/flaskr/entrypoint.sh"
    ],
    "healthCheck": {
      "command": [
        "CMD-SHELL",
        "curl -f http://localhost:5000/health || exit 1"
      ],
      "interval": 300,
      "timeout": 30,
      "retries": 3,
      "startPeriod": 60
    }
  }
]