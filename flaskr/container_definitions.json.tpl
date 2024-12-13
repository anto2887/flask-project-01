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
        "name": "FLASK_ENV",
        "value": "production"
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
        "name": "GUNICORN_CMD_ARGS",
        "value": "--workers=3 --threads=2 --timeout=120 --access-logfile=- --error-logfile=- --capture-output --enable-stdio-inheritance --log-level=info"
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
        "curl -f http://localhost:5000/health || exit 1"
      ],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    },
    "ulimits": [
      {
        "name": "nofile",
        "softLimit": 65536,
        "hardLimit": 65536
      }
    ],
    "mountPoints": [],
    "volumesFrom": [],
    "linuxParameters": {
      "initProcessEnabled": true
    },
    "systemControls": [
      {
        "namespace": "net.core.somaxconn",
        "value": "65535"
      }
    ],
    "memory": 512,
    "memoryReservation": 256,
    "cpu": 256,
    "privileged": false,
    "readonlyRootFilesystem": false
  }
]