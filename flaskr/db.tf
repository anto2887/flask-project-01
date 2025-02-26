resource "aws_db_subnet_group" "flaskr_subnet_group" {
  name       = "flaskr-subnet-group"
  subnet_ids = aws_subnet.flaskr_private_subnet[*].id

  tags = {
    Name = "flaskr-subnet-group"
  }
}

resource "aws_db_instance" "flaskr_db" {
  identifier             = "flaskrdb"
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "13.12"
  instance_class         = "db.t3.micro"
  db_name                = "flaskrdb"
  username               = "myuser"
  password               = "mypassword"
  db_subnet_group_name   = aws_db_subnet_group.flaskr_subnet_group.name
  vpc_security_group_ids = [aws_security_group.flaskr_rds_sg.id]
  skip_final_snapshot    = true

  # Add these lines to handle the backup configuration
  backup_retention_period = 0
  backup_window           = "03:00-04:00"

  tags = {
    Name = "flaskr-db"
  }
}