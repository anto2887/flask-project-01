resource "aws_s3_bucket" "alb_logs" {
  bucket = "flaskr-app-alb-logs"

  tags = {
    Name        = "flaskr-app-alb-logs"
    Environment = "production"
  }
}

resource "aws_s3_bucket_policy" "alb_logs_policy" {
  bucket = aws_s3_bucket.alb_logs.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          AWS = "arn:aws:iam::127311923021:root"
        },
        Action = "s3:PutObject",
        Resource = "arn:aws:s3:::flaskr-app-alb-logs/AWSLogs/193482034911/*"
      }
    ]
  })
}

data "aws_caller_identity" "current" {}
