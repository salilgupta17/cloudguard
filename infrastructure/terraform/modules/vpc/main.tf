# CloudGuard Isolated VPC Architecture
# Provides strict 3-tier network isolation: Public, Private Application, Private Isolated Database

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "cloudguard-vpc-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Internet Gateway for Public Subnets
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "cloudguard-igw-${var.environment}"
  }
}

# Public Subnets (ALB / Ingress)
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "cloudguard-public-subnet-${count.index + 1}-${var.environment}"
    Tier = "Public"
  }
}

# Elastic IP & NAT Gateway for Private Application Outbound (Pulling ECR images)
resource "aws_eip" "nat" {
  domain = "vpc"
  tags = {
    Name = "cloudguard-nat-eip-${var.environment}"
  }
}

resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "cloudguard-nat-gw-${var.environment}"
  }
}

# Private Application Subnets (ECS Fargate Workers & API)
resource "aws_subnet" "app" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 2)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "cloudguard-app-subnet-${count.index + 1}-${var.environment}"
    Tier = "Application"
  }
}

# Private Isolated Database Subnets (RDS PostgreSQL Primary & Restore Test Sandbox)
# Zero internet routing for maximum security
resource "aws_subnet" "database" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + 4)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "cloudguard-db-subnet-${count.index + 1}-${var.environment}"
    Tier = "IsolatedDatabase"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "cloudguard-public-rt-${var.environment}"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "app" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }

  tags = {
    Name = "cloudguard-app-rt-${var.environment}"
  }
}

resource "aws_route_table_association" "app" {
  count          = length(aws_subnet.app)
  subnet_id      = aws_subnet.app[count.index].id
  route_table_id = aws_route_table.app.id
}

# Isolated DB Route Table (No Internet / No NAT Gateway routes)
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "cloudguard-db-isolated-rt-${var.environment}"
  }
}

resource "aws_route_table_association" "database" {
  count          = length(aws_subnet.database)
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}
