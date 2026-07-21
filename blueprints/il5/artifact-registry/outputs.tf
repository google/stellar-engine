output "docker_registries" {
  description = "Docker registries created from the docker-registries.yaml file, with Docker Hub appended."
  value       = local.docker-registries
}

output "yum_repositories" {
  description = "Yum repositories created from the yum-repos.yaml file."
  value       = google_artifact_registry_repository.yum-repos
}
