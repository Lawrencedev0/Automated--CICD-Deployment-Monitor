output "public_ip" {
  description = "Public IP of the CI/CD instance"
  value       = aws_instance.cicd_host.public_ip
}

output "public_dns" {
  description = "Public DNS of the CI/CD instance"
  value       = aws_instance.cicd_host.public_dns
}

output "jenkins_url" {
  description = "Jenkins UI URL"
  value       = "http://${aws_instance.cicd_host.public_ip}:8080"
}

output "app_health_url" {
  description = "Sample app health endpoint"
  value       = "http://${aws_instance.cicd_host.public_ip}:5000/health"
}

output "ssh_command" {
  description = "Convenience SSH command"
  value       = "ssh -i ~/.ssh/<key>.pem ubuntu@${aws_instance.cicd_host.public_ip}"
}
