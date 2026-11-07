resource "kubernetes_namespace" "homework" {
  metadata {
    name = var.namespace
  }
}

resource "helm_release" "homework" {
  name      = "homework"
  chart     = "${path.module}/../helm"
  namespace = kubernetes_namespace.homework.metadata[0].name

  set {
    name  = "image.tag"
    value = var.image_tag
  }

  set {
    name  = "environment"
    value = var.environment
  }
}