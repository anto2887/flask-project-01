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
          Service = "logging.elb.amazonaws.com"
        },
        Action = "s3:PutObject",
        Resource = "${aws_s3_bucket.alb_logs.arn}/*"
      },
      {
        Effect = "Allow",
        Principal = {
          Service = "logging.elb.amazonaws.com"
        },
        Action = "s3:PutObject",
        Resource = "${aws_s3_bucket.alb_logs.arn}"
      }
    ]
  })
}
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
          Service = "logging.elb.amazonaws.com"
        },
        Action = "s3:PutObject",
        Resource = "${aws_s3_bucket.alb_logs.arn}/*"
      },
      {
        Effect = "Allow",
        Principal = {
          Service = "logging.elb.amazonaws.com"
        },
        Action = "s3:PutObject",
        Resource = "${aws_s3_bucket.alb_logs.arn}"
      }
    ]
  })
}
