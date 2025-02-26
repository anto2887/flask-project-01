variable "region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  type        = string
  default     = "arn:aws:acm:us-east-1:193482034911:certificate/6cbb62d4-13f2-411c-9419-fb3bccbab2fe"
}

variable "api_football_key_value" {
  description = "The API key for football data"
  type        = string
  sensitive   = true
}