terraform {
    required_version = ">= 1.5"
}

provider "kubernetes" {
    config_path = "~/.kube/config"
}

provider "helm" {
    kubernetes {
        config_path = "~/.kube/config"
    }
}