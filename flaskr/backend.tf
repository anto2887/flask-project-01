terraform {
  backend "s3" {
    bucket = "1914kolaprojects"
    key    = "flaskr_app/terraform.tfstate"
    region = "us-east-1"
  }
}
