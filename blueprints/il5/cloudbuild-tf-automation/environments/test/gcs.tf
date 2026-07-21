module "dev_bucket" {
  source        = "../../../../../modules/gcs"
  project_id    = var.project_id
  name          = var.bucket_name
  location      = local.locations.gcs
  storage_class = local.gcs_storage_class
}