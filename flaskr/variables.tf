variable "region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"  # You can set your default region here
}

variable "acm_certificate_arn" {
  description = "arn:aws:acm:us-east-1:193482034911:certificate/11a0ef6b-e195-4f02-989b-6d4de71feacc"
  type        = string
}