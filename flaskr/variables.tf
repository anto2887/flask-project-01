variable "region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"  # You can set your default region here
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  type        = string
  default     = "arn:aws:acm:us-east-1:193482034911:certificate/11a0ef6b-e195-4f02-989b-6d4de71feacc"
}

variable "api_football_key_value" {
  description = "The API key for football data"
  type        = string
  sensitive   = true
}