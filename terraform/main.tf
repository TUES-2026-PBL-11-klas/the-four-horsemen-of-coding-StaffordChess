terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.0"
    }
  }
}

provider "vault" {
  address = "http://127.0.0.1:8200"
}

provider "github" {
  token = data.vault_kv_secret_v2.terraform_secrets.data["Stafford_github_token"]
  owner = var.github_owner
}

data "vault_kv_secret_v2" "terraform_secrets" {
  mount = "secret"
  name  = "terraform"
}