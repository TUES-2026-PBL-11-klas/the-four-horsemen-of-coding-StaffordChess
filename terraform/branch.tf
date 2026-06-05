resource "github_branch" "infrastructure" {
  repository    = github_repository.chess_app.name
  branch        = "Infrastructure"
  source_branch = "main"

  depends_on = [github_repository.chess_app]
}

resource "github_branch_protection" "protected_branches" {
  for_each = toset(["main", "Infrastructure"])

  repository_id = github_repository.chess_app.node_id
  pattern       = each.value

  required_pull_request_reviews {
    required_approving_review_count = 1
    dismiss_stale_reviews           = true
  }

  required_status_checks {
    strict   = true
    contexts = ["build-and-test"]
  }

  enforce_admins = false

  depends_on = [github_branch.infrastructure]
}