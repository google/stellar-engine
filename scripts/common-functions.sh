#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Common functions for Stellar Engine deployment scripts
# Source this file in other scripts to use these functions

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Logging Functions
# ==============================================================================

# Log info message (Green)
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

# Log warning message (Yellow)
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

# Log error message (Red)
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Log debug message (Blue) - only if DEBUG=true
log_debug() {
    if [[ "${DEBUG:-}" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1" >&2
    fi
}

# Setup persistent logging to file
# Creates a log file in experimental/logs/{script_name}/ and redirects stdout/stderr to it via tee
setup_logging() {
    local script_name=$(basename "$0" .sh)
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    # Use SCRIPT_DIR if available, otherwise fallback to current directory
    local log_dir="${SCRIPT_DIR:-.}/logs/${script_name}"
    
    if [[ ! -d "$log_dir" ]]; then
        mkdir -p "$log_dir" || echo "Warning: Could not create log directory $log_dir"
    fi
    
    local log_file="${log_dir}/${script_name}_${timestamp}.txt"
    
    # Export LOG_FILE so it can be used by other functions if needed
    export LOG_FILE="$log_file"
    
    echo "Logging execution to: $log_file"
    
    # Redirect stdout and stderr to tee
    # We use a pipe to tee, which writes to file and stdout
    # Note: This runs in a subshell for the redirection
    exec > >(tee -a "$log_file") 2>&1
}

# ==============================================================================
# Configuration & Validation Functions
# ==============================================================================

# Validate that required environment variables are set
# Usage: validate_env_vars "VAR1" "VAR2" ...
validate_env_vars() {
    local required_vars=("$@")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi

    return 0
}

# Load and validate configuration from config.env
# Usage: load_config "script_dir" "VAR1" "VAR2" ...
load_config() {
    local script_dir="$1"
    local required_vars=("${@:2}")

    if [ ! -f "${script_dir}/config.env" ]; then
        log_error "config.env file not found in ${script_dir}"
        return 1
    fi

    # shellcheck source=experimental/config.env.sample
    if ! source "${script_dir}/config.env"; then
        log_error "Failed to source config.env file"
        return 1
    fi

    if ! validate_env_vars "${required_vars[@]}"; then
        return 1
    fi

    return 0
}

# Create a backup of a configuration file
# Usage: backup_config "file_path" ["backup_dir"]
backup_config() {
    local config_file="$1"
    local backup_dir="${2:-./backups}"

    if [[ ! -f "$config_file" ]]; then
        log_warn "Config file not found: $config_file"
        return 1
    fi

    mkdir -p "$backup_dir"
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${backup_dir}/$(basename "$config_file").backup.${timestamp}"

    if cp "$config_file" "$backup_file"; then
        log_info "Config backed up to: $backup_file"
        return 0
    else
        log_error "Failed to backup config file"
        return 1
    fi
}

# Check prerequisites (commands, auth, project)
check_prerequisites() {
    local missing_commands=()

    # Check for required commands
    for cmd in gcloud terraform; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_commands+=("$cmd")
        fi
    done

    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        log_error "Please install the missing commands and try again"
        return 1
    fi

    # Check gcloud authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 >/dev/null 2>&1; then
        log_warn "No active gcloud authentication found"
        log_warn "Please run 'gcloud auth login' before proceeding"
        return 1
    fi

    # Check gcloud project is set
    if ! gcloud config get-value project >/dev/null 2>&1; then
        log_warn "No default project set in gcloud config"
    fi

    return 0
}

# Check GCP quotas for a project
# Usage: check_gcp_quotas "project_id"
check_gcp_quotas() {
    local project_id="$1"
    shift
    local _required_quotas=("$@")

    log_info "Checking GCP quotas for project: $project_id"

    # Check if project exists first
    if ! gcloud projects describe "$project_id" >/dev/null 2>&1; then
        log_error "Project does not exist: $project_id"
        return 1
    fi

    # Basic quota check
    if ! gcloud compute project-info describe --project="$project_id" >/dev/null 2>&1; then
        log_warn "Cannot access compute quotas for project: $project_id"
        return 1
    fi

    log_info "Basic quota check passed for project: $project_id"
    return 0
}

# ==============================================================================
# Execution & Flow Control Functions
# ==============================================================================

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Retry a command with exponential backoff
# Usage: retry_command "max_attempts" "initial_delay" "command" [args...]
retry_command() {
    local max_attempts="${1:-3}"
    local delay="${2:-1}"
    local command="${3}"
    shift 3
    local args=("$@")

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        log_debug "Attempt $attempt/$max_attempts: $command ${args[*]}"

        if "$command" "${args[@]}"; then
            log_debug "Command succeeded on attempt $attempt"
            return 0
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Command failed (attempt $attempt/$max_attempts), retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))  # Exponential backoff
        fi

        ((attempt++))
    done

    log_error "Command failed after $max_attempts attempts: $command ${args[*]}"
    return 1
}

# Safely execute gcloud commands with retry
gcloud_safe() {
    local max_retries="${GCLOUD_MAX_RETRIES:-3}"
    local retry_delay="${GCLOUD_RETRY_DELAY:-2}"

    if ! retry_command "$max_retries" "$retry_delay" gcloud "$@"; then
        log_error "gcloud command failed: gcloud $*"
        return 1
    fi
    return 0
}

# Safely execute terraform commands with retry
terraform_safe() {
    local max_retries="${TERRAFORM_MAX_RETRIES:-2}"
    local retry_delay="${TERRAFORM_RETRY_DELAY:-5}"

    if ! retry_command "$max_retries" "$retry_delay" terraform "$@"; then
        log_error "terraform command failed: terraform $*"
        return 1
    fi
    return 0
}

# Wait for eventual consistency
wait_for_consistency() {
    local operation="$1"
    local wait_time="${2:-30}"

    log_info "Waiting ${wait_time}s for $operation to take effect..."
    sleep "$wait_time"
}

# Setup error handling with trap
# Usage: setup_error_handling [cleanup_function_name]
setup_error_handling() {
    cleanup_function="${1:-cleanup}"

    # Error handler
    error_handler() {
        local line_no=$1
        local exit_code=$2
        log_error "Script failed at line $line_no with exit code $exit_code"

        # Call cleanup function if it exists
        if declare -f "$cleanup_function" > /dev/null; then
            log_info "Running cleanup..."
            "$cleanup_function"
        fi

        exit "$exit_code"
    }

    trap 'error_handler $LINENO $?' ERR
}

# Default cleanup function (can be overridden)
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f tmp_*.yaml tmp_*.json 2>/dev/null || true
}

# Display script header
display_header() {
    local script_name="$1"
    local description="$2"

    echo
    log_info "========================================"
    log_info "$script_name"
    log_info "$description"
    log_info "========================================"
    echo
}

# ==============================================================================
# Interactive Functions
# ==============================================================================

# Consolidated prompt function with timeout and non-interactive support
# Usage: promptUser "Prompt message" [commands...]
# Environment variables:
#   NON_INTERACTIVE: Set to "true" to skip prompts (defaults to PROMPT_DEFAULT_RESPONSE)
#   PROMPT_TIMEOUT: Timeout in seconds (default: 0/infinite)
#   PROMPT_DEFAULT_RESPONSE: Default response for timeout/non-interactive (default: n)
promptUser() {
    local prompt="$1"
    shift
    local commands=("$@")
    
    local timeout="${PROMPT_TIMEOUT:-0}"
    local default_response="${PROMPT_DEFAULT_RESPONSE:-n}"
    local timeout_arg=""

    if [[ "$timeout" -gt 0 ]]; then
        timeout_arg="-t $timeout"
    fi

    # Check for non-interactive mode
    if [[ "${NON_INTERACTIVE:-false}" == "true" ]]; then
        log_info "Non-interactive mode: using default response '$default_response' for: $prompt"
        if [[ "$default_response" =~ ^[Yy] ]]; then
             # Proceed to execute commands if any
             true
        else
             return 1
        fi
    else
        # Interactive prompt
        while true; do
            echo
            log_info "$prompt"
            echo "Please choose: [y]es / [n]o / [s]kip"
            
            local choice
            if ! read -r $timeout_arg choice; then
                echo # Newline after timeout
                log_warn "Timeout reached ($timeout s). Defaulting to '$default_response'."
                choice="$default_response"
            fi

            case "$choice" in
                [Yy]|[Yy][Ee][Ss])
                    break # Proceed to execution
                    ;;
                [Nn]|[Nn][Oo])
                    log_warn "Skipping: $prompt"
                    return 1
                    ;;
                [Ss]|[Ss][Kk][Ii][Pp])
                    log_warn "Skipping: $prompt"
                    return 255
                    ;;
                *)
                    log_error "Invalid choice. Please enter y, n, or s."
                    ;;
            esac
        done
    fi

    # Execute commands if provided
    if [[ ${#commands[@]} -gt 0 ]]; then
        log_info "Executing commands..."
        local command_failed=false

        for cmd in "${commands[@]}"; do
            log_info "Running: $cmd"

            # Create a backup before potentially destructive operations
            if [[ "$cmd" =~ (delete|destroy|rm) ]] && [[ -f "config.env" ]]; then
                backup_config "config.env"
            fi

            if ! bash -c "$cmd"; then
                log_error "Command failed: $cmd"
                command_failed=true
                
                # If interactive, ask to continue
                if [[ "${NON_INTERACTIVE:-false}" != "true" ]]; then
                    echo "Command failed. Continue anyway? [y/N]"
                    local continue_choice
                    read -r continue_choice
                    if [[ ! "$continue_choice" =~ ^[Yy] ]]; then
                        log_error "Aborting due to command failure"
                        return 1
                    fi
                else
                    log_error "Aborting due to command failure (non-interactive)"
                    return 1
                fi
            fi
        done
        
        if [[ "$command_failed" == "true" ]]; then
            log_warn "Some commands failed but execution continued."
        fi
    fi

    return 0
}

# Confirm destructive operation with explicit "DELETE" typing
confirm_destructive_operation() {
    local operation="$1"

    if [[ "${NON_INTERACTIVE:-false}" == "true" ]]; then
        log_warn "Non-interactive mode: Skipping destructive confirmation for: $operation"
        # In non-interactive mode, we might want to fail safe or allow if a flag is set.
        # For now, failing safe is better unless explicitly handled.
        return 1
    fi

    log_error "=== WARNING: DESTRUCTIVE OPERATION ==="
    log_error "$operation"
    echo
    log_warn "This action cannot be undone!"
    echo

    read -r -p "Type 'DELETE' to confirm: " confirmation
    if [[ "$confirmation" != "DELETE" ]]; then
        log_info "Operation cancelled by user"
        return 1
    fi

    return 0
}

# ==============================================================================
# Resource Management Functions
# ==============================================================================

# Check if a resource exists
# Usage: resource_exists "type" "name" [args...]
resource_exists() {
    local resource_type="$1"
    local resource_name="$2"
    shift 2
    local additional_args=("$@")

    case "$resource_type" in
        "project")
            gcloud projects describe "$resource_name" >/dev/null 2>&1
            ;;
        "org-policy")
            gcloud resource-manager org-policies describe "$resource_name" "${additional_args[@]}" >/dev/null 2>&1
            ;;
        "custom-constraint")
            # Use grep -w for exact match to avoid partial matches
            gcloud org-policies list-custom-constraints "${additional_args[@]}" --format="value(name)" | grep -w -q "$resource_name"
            ;;
        "storage-bucket")
            gcloud storage buckets describe "gs://$resource_name" >/dev/null 2>&1
            ;;
        "iam-role")
            gcloud iam roles describe "$resource_name" "${additional_args[@]}" >/dev/null 2>&1
            ;;
        *)
            log_error "Unknown resource type: $resource_type"
            return 1
            ;;
    esac
}

# Safely delete resources with existence check
# Usage: safe_delete "type" "name" [args...]
safe_delete() {
    local resource_type="$1"
    local resource_name="$2"
    shift 2
    local additional_args=("$@")

    if ! resource_exists "$resource_type" "$resource_name" "${additional_args[@]}"; then
        log_warn "Resource does not exist, skipping deletion: $resource_type $resource_name"
        return 0
    fi

    log_info "Deleting $resource_type: $resource_name"
    case "$resource_type" in
        "project")
            gcloud_safe projects delete "$resource_name" --quiet
            ;;
        "org-policy")
            gcloud_safe resource-manager org-policies delete "$resource_name" "${additional_args[@]}" --quiet
            ;;
        "custom-constraint")
            gcloud_safe org-policies delete-custom-constraint "$resource_name" "${additional_args[@]}" --quiet
            ;;
        "storage-bucket")
            gcloud_safe storage rm -r "gs://$resource_name"
            ;;
        "iam-role")
            gcloud_safe iam roles delete "$resource_name" "${additional_args[@]}" --quiet
            ;;
        *)
            log_error "Unknown resource type for deletion: $resource_type"
            return 1
            ;;
    esac
}