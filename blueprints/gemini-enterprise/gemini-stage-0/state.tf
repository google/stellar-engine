data "google_storage_bucket" "terraform_state" {
  name = var.terraform_state_bucket
}
