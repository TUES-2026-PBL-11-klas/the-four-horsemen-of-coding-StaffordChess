output "repo_url" {
  value = github_repository.chess_app.html_url
}

output "clone_url" {
  value = github_repository.chess_app.ssh_clone_url
}