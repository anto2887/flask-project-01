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
    "command": [
      "/usr/local/bin/wait-for-it.sh",
      "${db_host}:5432",
      "--",
      "/flaskr/entrypoint.sh"
    ]
  }
]
