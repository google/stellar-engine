#!/bin/bash

# Initialize variables
PROJECT_ID=""
CURRENT_USER=""

# Function to display help
usage() {
  echo "Usage: $0 --project-id=<project-id>"
  echo "  --project-id      The ID of the GCP project to delete."
  exit 1
}

# Function to display error message and exit
error_exit() {
  echo "ERROR: $1" >&2
  exit 1
}

# Function to validate required parameters
validate_parameters() {
  if [ -z "$PROJECT_ID" ]; then
    error_exit "Project ID is required. Use --project-id=<project-id>"
  fi
}

# Function to check if gcloud is installed
check_gcloud() {
  if ! command -v gcloud &> /dev/null; then
    error_exit "The gcloud CLI tool is not installed. Please install, configure, and try again."
  fi
}

check_project_status() {
    local project_status
    project_status=$(gcloud projects describe "$PROJECT_ID" --format="value(lifecycleState)" 2>/dev/null)

    if [ -z "$project_status" ]; then
        echo "Error: Project '$PROJECT_ID' does not exist or is inaccessible."
        exit 1
    elif [ "$project_status" == "DELETE_REQUESTED" ]; then
        echo "Error: Project '$PROJECT_ID' is marked for deletion and cannot be modified."
        exit 1
    elif [ "$project_status" != "ACTIVE" ]; then
        echo "Warning: Project '$PROJECT_ID' is in an unexpected state ('$project_status')."
    fi
}

# Function to get current user
get_current_user() {
  CURRENT_USER=$(gcloud config get-value account)
  if [ -z "$CURRENT_USER" ]; then
    error_exit "Failed to get current user. Please ensure you're logged into gcloud (gcloud auth login)."
  fi
}

# Function to manage project deleter role
manage_project_deleter() {
  local action=$1

  if [ "$action" == "add" ]; then
    echo "Adding projectDeleter role to $CURRENT_USER..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="user:$CURRENT_USER" \
      --role="roles/resourcemanager.projectDeleter" \
      --quiet \
      || error_exit "Failed to add projectDeleter role."

  elif [ "$action" == "remove" ]; then
    echo "Revoking projectDeleter role..."
    gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
      --member="user:$CURRENT_USER" \
      --role="roles/resourcemanager.projectDeleter" \
      --quiet \
      || echo "WARNING: Failed to revoke projectDeleter role. The project may already be deleted."
  fi
}

# Function to check user permissions
check_permissions() {
  echo "Checking user permissions..."
  local has_deleter_role
  has_deleter_role=$(gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --format="get(bindings.role)" \
    --filter="bindings.members:$CURRENT_USER AND bindings.role:roles/resourcemanager.projectDeleter" \
    --quiet)

  if [ -z "$has_deleter_role" ]; then
    manage_project_deleter "add"
  fi
}

# Function to get user confirmation
get_confirmation() {
  echo "WARNING: You are about to delete project: $PROJECT_ID"
  echo -n "To confirm, please re-enter the project ID: "
  read -r CONFIRMATION

  if [ "$CONFIRMATION" != "$PROJECT_ID" ]; then
    error_exit "Project ID confirmation did not match. Operation cancelled."
  fi
}

# Function to delete the project
delete_project() {
  echo "Deleting project $PROJECT_ID..."
  if ! gcloud projects delete "$PROJECT_ID" --quiet; then
    manage_project_deleter "remove"
    error_exit "Failed to delete project $PROJECT_ID"
  fi

  # Always remove the projectDeleter role
  manage_project_deleter "remove"

  echo "Project $PROJECT_ID has been successfully deleted."
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id=*)
      PROJECT_ID="${1#*=}"
      shift
      ;;
    *)
      usage
      ;;
  esac
done

# Functions
validate_parameters
check_gcloud
check_project_status
get_current_user
get_confirmation
check_permissions
delete_project
