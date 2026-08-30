variable "aws_region" {
  description = "AWS region for the CI/CD instance"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type (Jenkins + containers)"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI ID (x86_64 per region)"
  type        = string
  default     = "ami-0e86e20dae9224db8" # Ubuntu 22.04 x86_64 (us-east-1)
}

variable "key_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "instance_name" {
  description = "Name tag for the instance"
  type        = string
  default     = "ci-cd-monitoring-host"
}

variable "repo_url" {
  description = "Git repo URL cloned during user_data (contains project files)"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID to launch into (defaults to the default VPC)"
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Subnet ID to launch into (defaults to default subnet)"
  type        = string
  default     = ""
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
