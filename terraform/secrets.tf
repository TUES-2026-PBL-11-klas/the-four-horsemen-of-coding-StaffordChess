resource "github_actions_secret" "docker_username" {
  repository      = github_repository.chess_app.name
  secret_name     = "DOCKER_USERNAME"
  value = data.vault_kv_secret_v2.terraform_secrets.data["Stafford_docker_username"]
}

resource "github_actions_secret" "docker_password" {
  repository      = github_repository.chess_app.name
  secret_name     = "DOCKER_PASSWORD"
  value = data.vault_kv_secret_v2.terraform_secrets.data["Stafford_docker_password"]
}