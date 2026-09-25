# Stellar Engine Experimental Tools

This directory contains a suite of powerful automation scripts designed to streamline the deployment, management, and destruction of Stellar Engine environments. These tools are built to be robust, resumable, and transparent.

## Core Scripts

### common-functions.sh
A shared library providing consistent logging, error handling, and utility functions across all scripts.


### deploy.sh
The main entry point for deploying the Stellar Engine environment.
- Guides you interactively through setting up your `config.env`.
- Executes Terraform stages in the correct order (`0-bootstrap` -> `1-resman` -> `2-networking` -> `3-project-factory`).
- Captures all output automatically to timestamped files in `logs/deploy/`.
- Checks for common configuration issues and cloud resource states.

### destroy.sh
A safe and reliable script for tearing down the environment.
- Tracks progress in `state/last_operation_${PREFIX}.env` so interrupted runs can resume from the last successful stage.
- Archives previous destroy states to `logs/destroy/` to prevent conflicts.
- Reverts Terraform backend configurations to ensure clean destruction.
- Pulls remote state to local automatically if the GCS backend is detected and the bucket might be at risk, ensuring destruction can proceed even if the bucket is deleted.
- Performs an optional deep clean of all local Terraform state (`terraform.tfstate`, `.terraform/`) and configuration (`*-providers.tf`, `*.auto.tfvars.json`) across all stages to leave a clean environment for redeployment.
- Deletes projects and folders in parallel to reduce destruction time.
- Supports both GNU/Linux and macOS (BSD) environments.
- Verifies prefixes and prompts for confirmation before destructive actions.

## Utilities

### clean.sh
WARNING: DESTRUCTIVE. A utility for cleaning up organization-level resources such as Tags, Custom Roles, Log Sinks, and Org Policies.
- Deletes only resources matching the configured `PREFIX` to avoid affecting other deployments.
- Includes the same final cleanup logic as `destroy.sh` to remove local state and config files.

### restore.sh (Experimental)
A helper script to assist in restoring an environment where the prefix has not changed. It can undelete projects, re-enable billing, and import Terraform state. Use with caution.

### allow_bq.sh
A targeted fix for BigQuery permission issues (`gcp.restrictServiceUsage`) that can occur during deployment.

## Configuration

The `config.env` file is the single source of truth for your deployment configuration.
- `deploy.sh` can generate this file interactively.
- Contains settings such as `PREFIX`, `ORGANIZATION_ID`, `BILLING_ACCOUNT`, and region preferences.

## Logging

All script executions are logged to the `logs/` directory, organized by script name.
- Log files use the path format `logs/<script_name>/<script_name>_<YYYYMMDD_HHMMSS>.txt`.
- These logs contain the full output of the terminal session for debugging and review.

## Supported Shell Environments

These scripts rely on POSIX path resolution, symbolic links, and standard GNU/BSD utilities (`bash`, `sed`, `awk`, `grep`, `jq`). The following environments are supported:

- Linux
- macOS
- Google Cloud Shell
- WSL2 (Windows Subsystem for Linux) on Windows workstations

### Native Windows Limitations Note

Running these scripts directly from PowerShell, Command Prompt (`cmd.exe`), Git Bash (`MINGW64`/`MSYS`), or Cygwin is not supported and is blocked by the pre-flight check (`check_os_environment`) in `common-functions.sh`. Native Windows terminals can encounter the following issues:

- Path separator translation issues (`\` vs `/`) when generating Terraform stage links and backend paths.
- Symbolic link creation failures (`ln -s`) unless Windows Developer Mode or elevated privileges are enabled.
- Line-ending (`CRLF` vs `LF`) and file permission incompatibilities in generated configuration files.

## Usage

1. Ensure you are running in a supported shell environment (Linux, macOS, Cloud Shell, or WSL2) and have the required permissions and dependencies (`gcloud`, `terraform`, `jq`).
2. Run `./deploy.sh` and follow the prompts.
3. Run `./destroy.sh` when you need to tear down the environment.

Disclaimer: These tools perform powerful operations on your Google Cloud environment. Always verify your configuration and backups before running destructive commands.
