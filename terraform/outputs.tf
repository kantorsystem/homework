output "namespace" {
  value       = kubernetes_namespace.homework.metadata[0].name
  description = "The namespace where the application is deployed"
}

output "helm_release_name" {
  value       = helm_release.homework.name
  description = "The name of the Helm release"
}

output "docker_image_tag" {
  value       = var.image_tag
  description = "The Docker image tag used for the deployment"
}