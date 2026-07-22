<!--
Copyright 2026 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Stellar Engine Experimental Tools

This directory contains a suite of powerful automation scripts designed to streamline the deployment, management, and destruction of Stellar Engine environments. These tools are built to be robust, resumable, and transparent.

## Core Scripts

### `common-functions.sh`
A shared library providing consistent logging, error handling, and utility functions across all scripts.


### `deploy.sh`
The main entry point for deploying the Stellar Engine environment.
- **Interactive Configuration**: Guides you through setting up your `config.env`.
- **Stage-Based Deployment**: Executes Terraform stages in the correct order (0-bootstrap -> 1-resman -> 2-networking -> 3-project-factory).
- **Persistent Logging**: Automatically captures all output to timestamped files in `logs/deploy/`.
- **Robust Error Handling**: Includes checks for common configuration issues and cloud resource states.

### `destroy.sh`
A safe and reliable script for tearing down the environment.
- **Resumable Operations**: Tracks progress in `state/last_operation_${PREFIX}.env`. If the script is interrupted, it can resume from the last successful stage.
- **State Archiving**: Automatically archives previous destroy states to `logs/destroy/` to prevent conflicts.
- **Reverse State Migration**: Handles the complex logic of reverting Terraform backend configurations to ensure clean destruction.
- **State Pull Safety Net**: Automatically pulls remote state to local if the GCS backend is detected but the bucket might be at risk, ensuring destruction can proceed even if the bucket is deleted.
- **Final Sweep**: Optionally performs a deep clean of all local Terraform state (`terraform.tfstate`, `.terraform/`) and configuration (`*-providers.tf`, `*.auto.tfvars.json`) across all stages to ensure a pristine environment for redeployment.
- **Parallel Execution**: Utilizes parallel processing to delete projects and folders simultaneously, significantly reducing destruction time.
- **Portability**: Compatible with both GNU/Linux and macOS (BSD) environments.
- **Safety Checks**: Verifies prefixes and prompts for confirmation before destructive actions.

## Utilities

### `clean.sh`
**WARNING: DESTRUCTIVE.** A utility for cleaning up **organization-level resources** such as Tags, Custom Roles, Log Sinks, and Org Policies.
- **Prefix-Aware**: Only deletes resources matching the configured `PREFIX` to avoid affecting other deployments.
- **Local Cleanup**: Includes the same "Final Sweep" logic as `destroy.sh` to clean up local state and config files.

### `restore.sh` (Experimental)
A helper script to assist in restoring an environment where the prefix has not changed. It can undelete projects, re-enable billing, and import Terraform state. **Use with caution.**

### `allow_bq.sh`
A targeted fix for BigQuery permission issues (`gcp.restrictServiceUsage`) that can occur during deployment.

## Configuration

The `config.env` file is the single source of truth for your deployment configuration.
- **Creation**: `deploy.sh` will help you create this file interactively.
- **Variables**: Contains critical settings like `PREFIX`, `ORGANIZATION_ID`, `BILLING_ACCOUNT`, and region preferences.

## Logging

All script executions are logged to the `logs/` directory, organized by script name.
- Format: `logs/<script_name>/<script_name>_<YYYYMMDD_HHMMSS>.txt`
- These logs contain the full output of the terminal session, making them ideal for debugging and review.

## Usage

1.  **Setup**: Ensure you have the required permissions and dependencies (gcloud, terraform).
2.  **Deploy**: Run `./deploy.sh` and follow the prompts.
3.  **Destroy**: Run `./destroy.sh` when you need to tear down the environment.

---
**Disclaimer**: These tools perform powerful operations on your Google Cloud environment. Always verify your configuration and backups before running destructive commands.
