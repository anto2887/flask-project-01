terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # This will use the latest 5.x version
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.3"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.1.1"
    }
  }
  required_version = ">= 0.14"
}

provider "aws" {
  region = var.region
}

provider "random" {}

provider "null" {}