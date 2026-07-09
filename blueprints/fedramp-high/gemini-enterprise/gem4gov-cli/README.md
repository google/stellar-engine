# gem4gov

`gem4gov` is a command-line tool designed to streamline the onboarding process for government customers to Gemini for Government. This tool automates the setup and configuration of the necessary Google Cloud components, ensuring a smooth and efficient deployment.

## Overview

The tool guides the user through a series of steps to configure their Google Cloud project for Gemini for Government. It handles authentication, role and API validation, identity provider setup, and the creation of Discovery Engine data stores and search engines.

## Prerequisites

Before using this tool, you must have the following:

- **Python 3.6+**
- **Google Cloud SDK (`gcloud`)**: Installed and authenticated.
- **Google Cloud Project**: Created with billing enabled.
- **IAM Roles**: The user running the tool must have the following IAM roles on the project:
    - `roles/discoveryengine.admin`
    - `roles/aiplatform.admin`
    - `roles/serviceusage.serviceUsageAdmin`
    - `roles/storage.admin`
    - `roles/bigquery.admin`
    - `roles/cloudkms.admin` (Required for granting CMEK permissions)
    - `roles/resourcemanager.projectIamAdmin` (Recommended for general IAM management)

- **APIs**: The tool will check for and attempt to enable the following APIs:
    - `aiplatform.googleapis.com`
    - `discoveryengine.googleapis.com`
    - `cloudresourcemanager.googleapis.com`
    - `cloudkms.googleapis.com`
    - `iam.googleapis.com`
    - `serviceusage.googleapis.com`
    - `storage.googleapis.com`
    - `bigquery.googleapis.com`

## Installation

Follow these steps to install the `gem4gov` command-line tool.

### 1. Install the Package

From the root of the project directory (`gemini-enterprise/gem4gov-cli`), install the package in editable mode:

```bash
pip3 install -e .
```

### 2. Add to PATH

To run `gem4gov` from any directory, add the installation directory to your PATH.

Find the installation path:
```bash
which pip3
```
*Example output: `/Users/username/Library/Python/3.9/bin/pip3`*

Add the directory (e.g., `/Users/username/Library/Python/3.9/bin`) to your shell configuration (`~/.zshrc` or `~/.bash_profile`):

```bash
export PATH="<your_python_bin_directory>:$PATH"
```

Reload your shell:
```bash
source ~/.zshrc  # or ~/.bash_profile
```

### 3. Verify Installation

```bash
gem4gov --help
```

## Commands

### `gem4gov init`

Initializes the CLI and sets the active Google Cloud project.

```bash
gem4gov init
```
**Usage:**
1.  Clears existing project/billing configurations.
2.  Forces re-authentication.
3.  Prompts for the **GCP Project ID**.
4.  Sets the project as the default for `gcloud` and Application Default Credentials (ADC).

### `gem4gov onboard`

Initiates the interactive onboarding process.

```bash
gem4gov onboard
```

**Step-by-Step Guide:**

1.  **Compliance Regime Selection**: Choose the regulatory boundary (`FedRAMP High`, `FedRAMP Moderate`, `IL4`, `IL5`, or `None`).
2.  **Project Confirmation**: Confirm the GCP Project ID and ensure it resides in the appropriate Assured Workloads folder.
3.  **IAM Role Check**: Verifies required IAM roles.
4.  **API Check**: Verifies and enables required APIs.
5.  **Identity Provider Setup**:
    *   **Google Identity**: For Google Workspace users.
    *   **Third-Party (Workforce Identity)**: Requires `Workforce Pool ID` and `Provider ID`.
6.  **CMEK Configuration**:
    *   Checks for existing CMEK in `us` region.
    *   Options: Use existing key, create new key (instructions provided), or continue without CMEK (not recommended for production).
    *   **Note**: Grants `cloudkms.cryptoKeyEncrypterDecrypter` to Discovery Engine and Storage service accounts.
7.  **Application Type Selection**:
    *   **Default**: Chat only.
    *   **Search Engine**: Chat + 1 Data Store.
    *   **Blended Search**: Chat + 2+ Data Stores.
8.  **Data Store Configuration** (if applicable):
    *   **Existing**: Provide IDs of existing data stores.
    *   **New**: Create new **Cloud Storage** or **BigQuery** data stores.
        *   **GCS**: Requires Bucket Name and optional Path Prefix.
        *   **BigQuery**: Requires Dataset, Table, and Schema Mapping (Title, Description, etc.).
9.  **Engine Creation**: Creates the Gemini Enterprise application (Engine).
10. **Compliance Configuration**: Automatically disables features not authorized for the selected compliance regime (e.g., Image Gen, Personalization).
11. **Completion**: Outputs IDs and URLs for the created resources.

### `gem4gov app create`

Creates a Gemini Enterprise application non-interactively (mostly).

```bash
gem4gov app create --project-id <PROJECT_ID> [OPTIONS]
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--data-stores`: Comma-separated list of existing Data Store IDs.
*   `--workforce-pool-id`: Workforce Identity Pool ID (if using 3rd party IdP).
*   `--workforce-provider-id`: Workforce Identity Provider ID (if using 3rd party IdP).
*   `--compliance-regime`: `FEDRAMP_HIGH`, `FEDRAMP_MODERATE`, `IL4`, `IL5`, or `NONE`. 

### `gem4gov app update-compliance`

Updates an existing Gemini Enterprise application to comply with a specific regime.

```bash
gem4gov app update-compliance --project-id <PROJECT_ID> --engine-id <ENGINE_ID> --compliance-regime <REGIME>
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--engine-id`: (Required) The ID of the Gemini Enterprise Engine.
*   `--compliance-regime`: (Required) `FEDRAMP_HIGH`, `FEDRAMP_MODERATE`, `IL4`, `IL5`, or `NONE`.

**Actions:**
*   Disables unauthorized features (e.g., Private Knowledge Graph, Location Context).
*   Updates the Default Search Widget to disable user event collection.
*   Disables Implicit Model Caching for the project.

### `gem4gov app update-idp`

Configures the Identity Provider for a Gemini Enterprise application widget.

```bash
gem4gov app update-idp --project-id <PROJECT_ID> --engine-id <ENGINE_ID> --workforce-pool-id <POOL_ID> --workforce-provider-id <PROVIDER_ID>
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--engine-id`: (Required) The ID of the Gemini Enterprise Engine.
*   `--workforce-pool-id`: (Required) Workforce Identity Pool ID.
*   `--workforce-provider-id`: (Required) Workforce Identity Provider ID.

### `gem4gov datastore import`

Import documents into a Gemini Enterprise data store.

```bash
gem4gov datastore import --project-id <PROJECT_ID> --source-type <SOURCE_TYPE> [OPTIONS]
```

**Options:**
*   `--project-id`: (Required) GCP Project ID.
*   `--source-type`: (Required) Source of documents. Values: `gcs`, `bigquery`.
*   `--data-store-id`: (Optional) The ID of the data store. If not provided, you will be prompted to select one.

**Behavior:**
*   **GCS**: Prompts for the GCS URI (`gs://bucket/path`) and imports documents.
*   **BigQuery**: Not currently supported via this command (use `onboard`).
