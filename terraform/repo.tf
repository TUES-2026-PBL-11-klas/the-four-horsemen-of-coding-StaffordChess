resource "github_repository" "chess_app" {
  name = "the-four-horsemen-of-coding-StaffordChess"
  description = "Python + FastAPI chess application"
  visibility  = "public"

  has_issues   = true
  has_projects = true
  has_wiki     = false

  auto_init          = true
  gitignore_template = "Python"
  license_template   = "mit"
}
