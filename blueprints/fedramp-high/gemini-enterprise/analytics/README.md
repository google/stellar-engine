# Gemini Enterprise Usage Analytics Dashboard

This directory contains a Streamlit application designed to visualize usage analytics for Gemini Enterprise (via Discovery Engine) by querying audit logs stored in BigQuery.

## Overview

The dashboard provides insights into:
- **High-Level Metrics**: Total unique users, total sessions, search vs. answer counts.
- **User Activity & Retention**: Daily/Weekly/Monthly Active Users (DAU/WAU/MAU) trends.
- **Sessions**: Daily sessions trend.
- **Agent Activity**: Popularity of different agents based on unique users.

## Prerequisites

Before running the dashboard, ensure you have:
1.  **BigQuery Views**: The views `vw_discovery_engine_user_activity`, `vw_discovery_engine_sessions`, and `vw_discovery_engine_agent_activity` must exist in your BigQuery dataset. You can create them using the helper function in the main `deploy.sh` script (Option 6 under Helper Functions).
2.  **GCP Authentication**: You need permissions to query the BigQuery dataset.

---

## Local Development & Testing

You can run the Streamlit app locally on your machine to test changes or explore data.

### 1. Setup Virtual Environment
It is recommended to use a Python virtual environment to isolate dependencies.

```bash
# Navigate to this directory
cd blueprints/fedramp-high/gemini-enterprise/analytics

# Create a virtual environment
python3 -m venv .venv

# Activate the environment
source .venv/bin/activate
```

### 2. Install Dependencies
Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
The application reads the target Project ID and BigQuery Dataset ID from environment variables. Set them in your terminal:

```bash
export PROJECT_ID="your-gcp-project-id"
export DATASET_ID="your_dataset_id"
```

### 4. Authenticate with GCP
To allow the local app to access BigQuery, authenticate using Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

### 5. Run the App
Start the Streamlit server:

```bash
streamlit run app.py
```
The app will open in your default browser at `http://localhost:8501`.

---

## Running with Docker Locally

To test the container behavior locally before deploying to Cloud Run:

1.  **Build the image**:
    ```bash
    docker build -t gemini-analytics .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 8501:8080 gemini-analytics
    ```
    *Note: The container listens on port `8080` as required by Cloud Run, but we map it to `8501` locally for convenience.*

---

## Deployment to Cloud Run

The deployment is orchestrated by the `deploy.sh` script in the parent directory.

1.  Run `deploy.sh`.
2.  Navigate to **Helper Functions**.
3.  Select **Usage Analytics: Deploy Streamlit Dashboard (Cloud Run)**.

The script will automatically:
- Build the image (locally or via Cloud Build).
- Push it to Artifact Registry.
- Deploy to Cloud Run with restricted ingress (`internal-and-cloud-load-balancing`) and no public unauthenticated access.
- Inject the `PROJECT_ID` and `DATASET_ID` environment variables.

---

## Accessing the Internal Dashboard (Local Machine)

Since the Cloud Run service is deployed with internal ingress, you cannot access it directly over the public internet. You must use a bastion host in the VPC to tunnel traffic.

### Method 1: Using the Helper Script (Recommended)

The `deploy.sh` script includes a helper function to automate this process.

1.  Run `deploy.sh`.
2.  Navigate to **Helper Functions**.
3.  Select **Usage Analytics: Connect to Streamlit Dashboard (Local)**.
4.  Follow the prompts. The script will handle creating the bastion VM, starting the proxy, and setting up the SSH tunnel.
5.  Access the dashboard at `http://localhost:<port>` (default is 8888).

### Method 2: Manual Steps

If you prefer to set it up manually, follow these steps:

#### 1. Create Service Account and Grant Roles
```bash
# Create SA
gcloud iam service-accounts create analytics-bastion-sa \
    --display-name="Analytics Bastion Service Account" \
    --project=your-gcp-project-id

# Grant Invoker
gcloud run services add-iam-policy-binding gemini-analytics-dashboard \
    --member="serviceAccount:analytics-bastion-sa@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --project=your-gcp-project-id \
    --region=us-east4

# Grant Viewer
gcloud run services add-iam-policy-binding gemini-analytics-dashboard \
    --member="serviceAccount:analytics-bastion-sa@your-gcp-project-id.iam.gserviceaccount.com" \
    --role="roles/run.viewer" \
    --project=your-gcp-project-id \
    --region=us-east4
```

#### 2. Create Bastion VM
```bash
gcloud compute instances create analytics-bastion \
    --project=your-gcp-project-id \
    --zone=us-east4-a \
    --machine-type=e2-micro \
    --network=your-vpc-network \
    --subnet=your-vpc-subnet \
    --service-account=analytics-bastion-sa@your-gcp-project-id.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --no-address \
    --shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --metadata="startup-script=#!/bin/bash
apt-get update
apt-get install -y google-cloud-cli-cloud-run-proxy
gcloud run services proxy gemini-analytics-dashboard --project=your-gcp-project-id --region=us-east4 --port=8080 > /var/log/cloud-run-proxy.log 2>&1 &"
```

#### 3. Set up SSH Tunnel from your local machine
```bash
gcloud compute ssh analytics-bastion \
    --project=your-gcp-project-id \
    --zone=us-east4-a \
    --tunnel-through-iap \
    -- -L 8888:localhost:8080
```

Now you can access the dashboard at `http://localhost:8888`.
