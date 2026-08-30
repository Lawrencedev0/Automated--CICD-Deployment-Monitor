# ─────────────────────────────────────────────────────────────
# Terraform — AWS EC2 provisioning for the CI/CD monitoring host.
# Provisions: EC2 instance + security group.
# ─────────────────────────────────────────────────────────────
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Data: default VPC/subnet when not supplied ──────────────
data "aws_vpc" "default" {
  count   = var.vpc_id == "" ? 1 : 0
  default = true
}

data "aws_subnets" "default" {
  count = var.subnet_id == "" ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

# ── Security group ───────────────────────────────────────────
resource "aws_security_group" "cicd_sg" {
  name        = "cicd-monitoring-sg"
  description = "Allow SSH, Jenkins UI, app, and monitoring ports"
  vpc_id      = var.vpc_id != "" ? var.vpc_id : data.aws_vpc.default[0].id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }

  ingress {
    description = "Jenkins UI / API"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jenkins agent (JNLP)"
    from_port   = 50000
    to_port     = 50000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Sample app HTTP"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cicd-monitoring-sg"
  }
}

# ── EC2 instance ─────────────────────────────────────────────
resource "aws_instance" "cicd_host" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.cicd_sg.id]
  subnet_id              = var.subnet_id != "" ? var.subnet_id : data.aws_subnets.default[0].ids[0]

  user_data = templatefile("${path.module}/userdata.sh", {
    repo_url = var.repo_url
  })

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
  }

  tags = {
    Name = var.instance_name
  }
}
