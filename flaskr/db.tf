resource "aws_db_instance" "flaskr_db" {
  identifier          = "flaskr-database"
  allocated_storage   = 20
  storage_type        = "gp2"
  engine              = "postgres"
  engine_version      = "13"
  instance_class      = "db.t3.micro"
  db_name             = "mydatabase"
  username            = "myuser"
  password            = "mypassword"
  parameter_group_name = "default.postgres13"
  skip_final_snapshot = true
  publicly_accessible = false
  vpc_security_group_ids = [aws_security_group.flaskr_rds_sg.id]
  db_subnet_group_name = aws_db_subnet_group.flaskr_subnet_group.name
}

resource "aws_db_subnet_group" "flaskr_subnet_group" {
  name       = "flaskr-subnet-group"
  subnet_ids = aws_subnet.flaskr_private_subnet[*].id
}
