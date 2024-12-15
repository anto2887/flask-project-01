[
  {
    "name": "flaskr-app",
    "image": "${image}",
    "essential": true,
    "portMappings": [
      {
        "containerPort": 5000,
        "hostPort": 5000,
        "protocol": "tcp"
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
        "name": "FLASK_ENV",
        "value": "production"
      },
      {
        "name": "CREATE_TABLES_ON_STARTUP",
        "value": "True"
      },
      {
        "name": "POPULATE_DATA_ON_STARTUP",
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
      },
      {
        "name": "AWS_DEFAULT_REGION",
        "value": "${awslogs_region}"
      },
      {
        "name": "SECRET_NAME",
        "value": "${api_football_key_name}"
      },
      {
        "name": "PYTHONUNBUFFERED",
        "value": "1"
      }
    ],
    "secrets": [
      {
        "name": "API_FOOTBALL_KEY",
        "valueFrom": "${api_football_key_arn}"
      }
    ],
    "command": [
      "/flaskr/entrypoint.sh"
    ],
    "healthCheck": {
      "command": [
        "CMD-SHELL",
        "python3 -c \"from app import create_app; app=create_app(); ctx=app.test_request_context(); ctx.push(); print('Health check succeeded')\""
      ],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    },
    "mountPoints": [],
    "volumesFrom": [],
    "linuxParameters": {
      "initProcessEnabled": true
    },
    "memory": 512,
    "memoryReservation": 256,
    "cpu": 256,
    "privileged": false,
    "readonlyRootFilesystem": false
  }
]