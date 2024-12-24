# Bastion host EC2 instance
resource "aws_instance" "bastion" {
  ami           = "ami-0fc5d935ebf8bc3bc"  # Ubuntu 22.04 LTS in us-east-1
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.flaskr_public_subnet[0].id  # Place in first public subnet

  # Reference the bastion security group declared in sg.tf
  vpc_security_group_ids = [aws_security_group.flaskr_bastion_sg.id]
  key_name              = "nginxubuntu"

  tags = {
    Name = "flaskr-bastion"
  }

  # Install PostgreSQL client on startup
  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y postgresql-client
              EOF

  user_data_replace_on_change = true
}

# Output the bastion's public IP for easy access
output "bastion_public_ip" {
  value       = aws_instance.bastion.public_ip
  description = "Public IP address of the bastion host"
}
