# Security group for Redis
resource "aws_security_group" "redis_sg" {
  name        = "flaskr-redis-sg"
  description = "Security group for Redis cluster"
  vpc_id      = aws_vpc.flaskr_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.flaskr_ecs_sg.id]
  }

  tags = {
    Name = "flaskr-redis-sg"
  }
}

# Redis subnet group
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "flaskr-redis-subnet-group"
  subnet_ids = aws_subnet.flaskr_private_subnet[*].id
}

# Redis parameter group
resource "aws_elasticache_parameter_group" "redis_params" {
  family = "redis7"
  name   = "flaskr-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

# Redis cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "flaskr-redis"
  engine              = "redis"
  node_type           = "cache.t4g.micro"  # Smallest instance, adjust as needed
  num_cache_nodes     = 1
  parameter_group_name = aws_elasticache_parameter_group.redis_params.name
  port                = 6379
  security_group_ids  = [aws_security_group.redis_sg.id]
  subnet_group_name   = aws_elasticache_subnet_group.redis_subnet_group.name

  tags = {
    Name = "flaskr-redis"
  }
}

# Output the Redis endpoint for use in application
output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}