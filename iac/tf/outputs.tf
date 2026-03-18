output "vscode" {
  value = "http://${aws_instance.gpu_ubuntu.public_ip}:8080"
}
