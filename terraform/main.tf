resource "kubernetes_namespace" "homework" {
    metadata {
        name = "production"
    }
}

resource "helm_release" "homework" {
    name       = "homework"
    chart      = "../helm/homework"
    namespace  = kubernetes_namespace.homework.metadata[0].name

    set {
        name  = "image.tag"
        value = 
    }

    set {
        name  = "environment"
        value = prod
    }
}