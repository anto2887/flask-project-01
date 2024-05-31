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
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        },
        Action = "s3:PutObject",
        Resource = "${aws_s3_bucket.alb_logs.arn}/*",
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = "${data.aws_caller_identity.current.account_id}"
          },
          ArnLike = {
            "aws:SourceArn" = "arn:aws:elasticloadbalancing:${var.region}:${data.aws_caller_identity.current.account_id}:loadbalancer/app/${aws_lb.flaskr_app_alb.name}/*"
          }
        }
      }
    ]
  })
}

data "aws_caller_identity" "current" {}
