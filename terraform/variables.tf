variable "namespace" {
  type        = string
  description = "The Kubernetes namespace to deploy the application into"
}

variable "environment" {
  type        = string
  description = "The environment to deploy to (dev, staging, prod)"
}

variable "image_tag" {
  type        = string
  description = "The Docker image tag to deploy"
}