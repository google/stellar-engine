#!/bin/bash
set -e

# Ensure gem4gov can be found in the python path
export PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gem4gov-cli:$PYTHONPATH"

# --- Global Configuration ---
# These variables are used across multiple functions
PROJECT_ID=""
ORG_ID=""
PREFIX=""
REGION=""
DOMAIN=""
DEPLOYMENT_CHOICE=""
IS_BROWNFIELD="false"
IS_CUSTOM="false"
BUCKET_NAME=""
STATE_BUCKET=""
TENANT_IAC_PROJECT=""
KMS_KEY_ID=""
SKIP_PROMPTS="false"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Script Helper Functions ---

print_header() {
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}   Gemini Enterprise FedRAMP High Blueprint Manager         ${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
}

pause() {
    echo ""
    read -p "Press Enter to acknowledge and continue..."
}

normalize_environment() {
    # Capitalize first letter of Environment (e.g. prod -> Prod)
    if [[ -n "$ENVIRONMENT" ]]; then
        CAP_ENV=$(echo "$ENVIRONMENT" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
    fi
}

check_dependencies() {
    echo ""
    echo -e "${BLUE}--- Check Dependencies ---${NC}"
    echo "Validating required dependencies: tfenv, gcloud, terraform, pip3, python3, jq..."
    
    # Ensure ~/.tfenv/bin is in PATH early if it exists (resolves precedence issues)
    if [[ -d "$HOME/.tfenv/bin" ]] && [[ ":$PATH:" != *":$HOME/.tfenv/bin:"* ]]; then
        export PATH="$HOME/.tfenv/bin:$PATH"
        hash -r 2>/dev/null || true
    fi

    if command -v tfenv &> /dev/null; then
        echo -e "${GREEN}tfenv is installed. Setting Terraform version to 1.12.2...${NC}"
        tfenv install 1.12.2
        tfenv use 1.12.2
    else
        echo -e "${YELLOW}tfenv is not installed. Checking OS...${NC}"
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
            echo -e "${RED}Windows detected.${NC}"
            echo "Please manually install Terraform v1.12.2:"
            echo "1. Download the binary from: https://releases.hashicorp.com/terraform/1.12.2/terraform_1.12.2_windows_amd64.zip"
            echo "2. Extract the zip file."
            echo "3. Add the dir containing terraform.exe to your system's PATH environment variable."
            exit 1
        elif [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
            echo -e "${YELLOW}MacOS/Linux detected. Installing tfenv manually...${NC}"
            if [[ ! -d "$HOME/.tfenv" ]]; then
                git clone --depth=1 https://github.com/tfutils/tfenv.git ~/.tfenv
            else
                echo -e "${GREEN}tfenv directory already exists at $HOME/.tfenv. Skipping clone.${NC}"
            fi
            
            # Add to bashrc/bash_profile to ensure Linux/MacOS compat
            for PROFILE in ~/.bash_profile ~/.bashrc; do
                if [[ -f "$PROFILE" ]] && ! grep -q 'export PATH="$HOME/.tfenv/bin:$PATH"' "$PROFILE" 2>/dev/null; then
                    echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> "$PROFILE"
                fi
            done
            # If neither file existed, just create .bashrc for Linux
            if [[ ! -f ~/.bash_profile && ! -f ~/.bashrc ]]; then
                echo 'export PATH="$HOME/.tfenv/bin:$PATH"' >> ~/.bashrc
            fi
            
            export PATH="$HOME/.tfenv/bin:$PATH"
            hash -r 2>/dev/null || true
            echo -e "${GREEN}tfenv installed. Setting Terraform version to 1.12.2...${NC}"
            tfenv install 1.12.2
            tfenv use 1.12.2
            
            if [[ "$CLOUD_SHELL" == "true" ]]; then
                echo -e "${YELLOW}IMPORTANT: You are running in Google Cloud Shell.${NC}"
                echo -e "${YELLOW}To use the 'tfenv' or 'terraform' commands in your terminal AFTER this script finishes, you MUST run: ${GREEN}source ~/.bashrc${NC}"
            fi
        else
            echo -e "${RED}Unsupported OS: $OSTYPE. Please install Terraform 1.12.2 manually before running this script.${NC}"
            exit 1
        fi
    fi

    local missing=0
    for cmd in gcloud terraform pip3 python3 jq; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}Error: Required command '$cmd' not found.${NC}"
            missing=1
        fi
    done
    if [[ $missing -eq 1 ]]; then
        echo "Please install missing dependencies and try again."
        exit 1
    fi
}

configure_data_stores() {
    # Expects GCS_LIST and BQ_LIST to be defined arrays in the calling scope
    
    # Clear existing import config to prevent duplicate import blocks on replay
    > gemini-stage-0/import.tf

    while true; do
        echo ""
        echo -e "${BLUE}--- Data Store Configuration ---${NC}"
        echo "1. Add Google Cloud Storage (GCS) Data Store"
        echo "2. Add BigQuery (BQ) Data Store"
        echo "3. Done"
        read -p "Select an option [1-3]: " DS_MENU_SEL
        
        case $DS_MENU_SEL in
            1)
                read -p "Does the GCS bucket already exist? [y/N]: " BUCKET_EXISTS
                
                if [[ "$BUCKET_EXISTS" =~ ^[Yy]$ ]]; then
                    read -p "Enter Bucket Name (exclude 'gs://' prefix, e.g., company-docs): " GCS_NAME
                    GCS_NAME=$(echo "$GCS_NAME" | tr -dc 'a-z0-9_.-') # Sanitize bucket name
                    read -p "Enter Display Name for the Data Store: " DISPLAY_NAME
                    
                    if [[ -n "$GCS_NAME" && -n "$DISPLAY_NAME" ]]; then
                        CREATE_BUCKET="false"
                        echo -e "${YELLOW}GCS Bucket '${GCS_NAME}' already exists. It will NOT be created by Terraform.${NC}"
                        
                        read -p "Would you like to import this bucket into Terraform state to be managed? [y/N]: " IMPORT_GCS
                        if [[ "$IMPORT_GCS" =~ ^[Yy]$ ]]; then
                            CREATE_BUCKET="true"
                            GCS_INDEX=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed 's/^-//;s/-$//')
                            cat <<EOF >> gemini-stage-0/import.tf
import {
  to = google_storage_bucket.gemini_enterprise_gcs_bucket["${GCS_INDEX}"]
  id = "${PROJECT_ID}/${GCS_NAME}"
}
EOF
                            echo -e "${GREEN}Import configuration generated for ${GCS_NAME}.${NC}"
                        fi

                        GCS_LIST+=("\"$GCS_INDEX\" = {name = \"$GCS_NAME\", create_bucket = $CREATE_BUCKET, display_name = \"$DISPLAY_NAME\"}")
                        echo -e "${GREEN}Added GCS Data Store: ${DISPLAY_NAME} (Bucket: ${GCS_NAME})${NC}"
                    else
                        echo -e "${RED}Invalid Bucket Name or Display Name.${NC}"
                    fi
                else
                    read -p "Enter Display Name for the new Data Store: " DISPLAY_NAME
                    
                    if [[ -n "$DISPLAY_NAME" ]]; then
                        # Clean display name: lowercase, replace spaces/special chars with hyphens
                        CLEAN_NAME=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed 's/^-//;s/-$//')
                        
                        # Terraform appends project ID and '-data' to the key.
                        # Total length: len(PROJECT_ID) + 1 (hyphen) + len(KEY) + 5 ('-data') <= 63
                        PREFIX_LEN=$((${#PROJECT_ID} + 6))
                        MAX_LEN=$((63 - PREFIX_LEN))
                        
                        if [[ $MAX_LEN -le 0 ]]; then
                            echo -e "${RED}Project ID is too long to automatically generate a valid bucket name. Please use an existing bucket.${NC}"
                        else
                            # Truncate and ensure it doesn't start/end with hyphen
                            CLEAN_NAME=$(echo "${CLEAN_NAME:0:$MAX_LEN}" | sed 's/^-//;s/-$//')
                            GCS_NAME="${PROJECT_ID}-${CLEAN_NAME}-data"
                            
                            CREATE_BUCKET="true"
                            echo -e "${GREEN}Data Store '${DISPLAY_NAME}' will generate Terraform Bucket key: '${GCS_NAME}'${NC}"
                            
                            GCS_LIST+=("\"$CLEAN_NAME\" = {name = \"$GCS_NAME\", create_bucket = $CREATE_BUCKET, display_name = \"$DISPLAY_NAME\"}")
                            echo -e "${GREEN}Added GCS Data Store: ${DISPLAY_NAME}${NC}"
                        fi
                    else
                        echo -e "${RED}Invalid Display Name.${NC}"
                    fi
                fi
                ;;
            2)
                read -p "Does the BigQuery dataset already exist? [y/N]: " DATASET_EXISTS
                
                if [[ "$DATASET_EXISTS" =~ ^[Yy]$ ]]; then
                    read -p "Enter Dataset ID (e.g., my_dataset): " BQ_DATASET
                    BQ_DATASET=$(echo "$BQ_DATASET" | tr -dc 'a-zA-Z0-9_') # Sanitize dataset ID
                    read -p "Enter Table ID (e.g., my_table): " BQ_TABLE
                    BQ_TABLE=$(echo "$BQ_TABLE" | tr -dc 'a-zA-Z0-9_-') # Sanitize table ID
                    read -p "Enter Display Name for the Data Store: " DISPLAY_NAME
                    
                    if [[ -n "$BQ_DATASET" && -n "$BQ_TABLE" && -n "$DISPLAY_NAME" ]]; then
                        CREATE_DATASET="false"
                        echo -e "${YELLOW}BigQuery Dataset '${BQ_DATASET}' already exists. It will NOT be created by Terraform.${NC}"
                        
                        read -p "Would you like to import this dataset into Terraform state to be managed? [y/N]: " IMPORT_BQ
                        if [[ "$IMPORT_BQ" =~ ^[Yy]$ ]]; then
                            CREATE_DATASET="true"
                            BQ_INDEX=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed 's/^-//;s/-$//')
                            cat <<EOF >> gemini-stage-0/import.tf
import {
  to = google_bigquery_dataset.gemini_enterprise_bq_dataset["${BQ_INDEX}"]
  id = "projects/${PROJECT_ID}/datasets/${BQ_DATASET}"
}
EOF
                            echo -e "${GREEN}Import configuration generated for ${BQ_DATASET}.${NC}"
                        fi

                        BQ_INDEX=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed 's/^-//;s/-$//')
                        BQ_LIST+=("\"$BQ_INDEX\" = {dataset_id = \"$BQ_DATASET\", table_id = \"$BQ_TABLE\", create_dataset = $CREATE_DATASET, display_name = \"$DISPLAY_NAME\"}")
                        echo -e "${GREEN}Added BigQuery Data Store: ${DISPLAY_NAME} (Table: ${BQ_DATASET}.${BQ_TABLE})${NC}"
                    else
                         echo -e "${RED}Invalid Dataset ID, Table ID, or Display Name.${NC}"
                    fi
                else
                    read -p "Enter Display Name for the new Data Store: " DISPLAY_NAME
                    
                    if [[ -n "$DISPLAY_NAME" ]]; then
                        # Clean display name for BQ Dataset: underscores and alphanumeric only
                        BQ_DATASET=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g' | sed 's/^_//;s/_$//')
                        read -p "Enter Table ID for the new Data Store (e.g., my_table): " BQ_TABLE
                        BQ_TABLE=$(echo "$BQ_TABLE" | tr -dc 'a-zA-Z0-9_-') # Sanitize table ID
                        
                        if [[ -n "$BQ_TABLE" ]]; then
                            CREATE_DATASET="true"
                            echo -e "${GREEN}Data Store '${DISPLAY_NAME}' will generate Terraform Dataset ID: '${BQ_DATASET}'${NC}"
                            
                            BQ_INDEX=$(echo "$DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed 's/^-//;s/-$//')
                            BQ_LIST+=("\"$BQ_INDEX\" = {dataset_id = \"$BQ_DATASET\", table_id = \"$BQ_TABLE\", create_dataset = $CREATE_DATASET, display_name = \"$DISPLAY_NAME\"}")
                            echo -e "${GREEN}Added BigQuery Data Store: ${DISPLAY_NAME} (Table: ${BQ_DATASET}.${BQ_TABLE})${NC}"
                        else
                             echo -e "${RED}Invalid Table ID.${NC}"
                        fi
                    else
                         echo -e "${RED}Invalid Display Name.${NC}"
                    fi
                fi
                ;;
            3)
                break
                ;;
            *)
                echo "Invalid option."
                ;;
        esac
    done

    # Clean up empty import.tf if no existing resources were imported
    if [[ ! -s "gemini-stage-0/import.tf" ]]; then
        rm -f gemini-stage-0/import.tf
    fi
}

# --- Authentication & Setup ---

auth_and_project_setup() {
    echo ""
    echo -e "${BLUE}--- Authentication & Project Selection ---${NC}"
    
    # 1. Google Account Check
    CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
    echo -e "Current Google Account: ${YELLOW}${CURRENT_ACCOUNT}${NC}"
    read -p "Is this the correct account? (y/N): " CONFIRM_ACCOUNT
    if [[ "$CONFIRM_ACCOUNT" != "y" && "$CONFIRM_ACCOUNT" != "Y" ]]; then
        echo "Starting authentication flow..."
        gcloud auth login
        CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
        echo -e "Now authenticated as: ${YELLOW}${CURRENT_ACCOUNT}${NC}"
    fi

    # 2. Project ID Selection
    CURRENT_PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [[ -n "$CURRENT_PROJECT_ID" ]]; then
        echo -e "Current Project ID: ${YELLOW}${CURRENT_PROJECT_ID}${NC}"
        read -p "Is this the correct Project ID for Gemini Enterprise? (y/N): " CONFIRM_PROJECT
        if [[ "$CONFIRM_PROJECT" == "y" || "$CONFIRM_PROJECT" == "Y" ]]; then
            PROJECT_ID=$CURRENT_PROJECT_ID
        else
            read -p "Enter the Google Cloud Project ID: " PROJECT_ID
            PROJECT_ID=$(echo "$PROJECT_ID" | tr -dc 'a-z0-9-')
            if [[ -n "$PROJECT_ID" ]]; then
                gcloud config set project "${PROJECT_ID}"
            fi
        fi
    fi

    if [[ -z "$PROJECT_ID" ]]; then
        read -p "Enter the Google Cloud Project ID: " PROJECT_ID
        PROJECT_ID=$(echo "$PROJECT_ID" | tr -dc 'a-z0-9-')
        if [[ -n "$PROJECT_ID" ]]; then
            gcloud config set project "${PROJECT_ID}"
        fi
    fi

    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Project ID is required.${NC}"
        return 1
    fi

    # Set billing quota project
    CURRENT_QUOTA_PROJ=$(gcloud config get-value billing/quota_project 2>/dev/null || echo "")
    if [[ "$CURRENT_QUOTA_PROJ" != "$PROJECT_ID" ]]; then
        echo "Setting billing quota project..."
        if ! gcloud config set billing/quota_project "${PROJECT_ID}" --quiet 2>/dev/null; then
            echo -e "${YELLOW}Notice: Could not set billing/quota_project. Access may be restricted.${NC}"
        fi
    fi

    # Enable Service Usage API (Required for quota project validation)
    if ! gcloud services list --enabled --project "${PROJECT_ID}" --filter="config.name:serviceusage.googleapis.com" --format="value(config.name)" 2>/dev/null | grep -q "serviceusage.googleapis.com"; then
        echo "Ensuring Service Usage API is enabled..."
        if ! gcloud --quiet services enable serviceusage.googleapis.com --project "${PROJECT_ID}" 2>/dev/null; then
             echo -e "${YELLOW}Notice: Could not verify/enable Service Usage API. Proceeding...${NC}"
        fi
    fi

    # Set application default quota project
    ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"
    CURRENT_ADC_QUOTA=""
    if [[ -f "$ADC_FILE" ]]; then
        CURRENT_ADC_QUOTA=$(jq -r '.quota_project_id // empty' "$ADC_FILE" 2>/dev/null || echo "")
    fi
    
    if [[ "$CURRENT_ADC_QUOTA" != "$PROJECT_ID" ]]; then
        echo "Setting application default quota project..."
        if ! gcloud --quiet auth application-default set-quota-project "${PROJECT_ID}" 2>/dev/null; then
            echo -e "${YELLOW}Notice: ADC Quota project not set to '${PROJECT_ID}'. (Missing 'serviceusage.services.use'?)${NC}"
            
            if [[ "$SKIP_PROMPTS" != "true" ]]; then
                 echo -e "${BLUE}Please enter a project ID where you have 'serviceusage.services.use' permission to use for quota.${NC}"
                 read -p "Fallback Quota Project ID (leave blank to skip): " FALLBACK_PROJECT_ID
                 if [[ -n "$FALLBACK_PROJECT_ID" ]]; then
                      if gcloud --quiet auth application-default set-quota-project "${FALLBACK_PROJECT_ID}" &>/dev/null; then
                           echo -e "${GREEN}Quota project set to '${FALLBACK_PROJECT_ID}'.${NC}"
                      else
                           echo -e "${YELLOW}Notice: Failed to set fallback quota project.${NC}"
                      fi
                 fi
            fi
        fi
    fi

    # 3. ADC Check
    echo "Checking Application Default Credentials (ADC)..."
    if [[ "$CLOUD_SHELL" == "true" ]]; then
        echo -e "${YELLOW}Google Cloud Shell detected. Forcing interactive Application Default Credentials setup for Terraform compatibility...${NC}"
        gcloud auth application-default login
    elif gcloud auth application-default print-access-token &>/dev/null; then
        echo -e "${GREEN}ADC is configured.${NC}"
        
        # Optional: Check if ADC matches current account (Best Effort)
        # Note: We can't easily extract the account from the token without an API call, 
        # but we can ask the user if they want to be sure.
        echo -e "${YELLOW}Note: Ensure your ADC matches the current account: ${CURRENT_ACCOUNT}${NC}"
        if [[ "$SKIP_PROMPTS" != "true" ]]; then
             read -p "Do you want to force refresh ADC credentials? (y/N): " REFRESH_ADC
             if [[ "$REFRESH_ADC" =~ ^[Yy]$ ]]; then
                  gcloud auth application-default login
             fi
        fi
    else
        echo -e "${YELLOW}Application Default Credentials not found.${NC}"
        read -p "Do you want to authenticate ADC now? (y/N): " DO_AUTH
        if [[ "$DO_AUTH" == "y" || "$DO_AUTH" == "Y" ]]; then
            gcloud auth application-default login
        else
            echo -e "${RED}WARNING: Proceeding without ADC. Terraform might fail.${NC}"
        fi
    fi

    # Discover Org ID
    echo "Discovering Organization ID..."
    ANCESTORS_INFO=$(gcloud projects get-ancestors "${PROJECT_ID}" --format="json" 2>/dev/null || echo "[]")
    ORG_ID=$(echo "$ANCESTORS_INFO" | jq -r 'last(.[] | select(.type == "organization")) | .id // empty')
    
    if [[ -z "$ORG_ID" ]]; then
        echo -e "${RED}WARNING: This project is not part of a GCP Organization ancestry chain.${NC}"
        echo -e "${YELLOW}Discovery Engine AclConfig applied via Terraform will likely fail with 'Organization not associated with Cloud Identity' error.${NC}"
    else
        echo -e "Found Organization ID: ${YELLOW}${ORG_ID}${NC}"
    fi

    # Discover Domain
    echo "Discovering Organization Domain..."
    ORG_DOMAIN=$(gcloud organizations list --filter="name:organizations/${ORG_ID}" --format="value(displayName)" 2>/dev/null)
    if [[ -n "$ORG_DOMAIN" ]]; then
        DOMAIN="${ORG_DOMAIN}"
        echo -e "Found Organization Domain: ${YELLOW}${DOMAIN}${NC}"
    else
        echo -e "${RED}WARNING: Could not auto-discover Organization Domain.${NC}"
    fi
    
    return 0
}

enable_apis() {
    echo ""
    echo -e "${BLUE}--- Enabling Required APIs ---${NC}"
    echo "Enabling: Assured Workloads, Access Context Manager, Org Policy, KMS, Storage, IAM, Service Usage..."
    if ! gcloud services enable \
        assuredworkloads.googleapis.com \
        accesscontextmanager.googleapis.com \
        compute.googleapis.com \
        orgpolicy.googleapis.com \
        cloudkms.googleapis.com \
        storage.googleapis.com \
        iam.googleapis.com \
        cloudresourcemanager.googleapis.com \
        serviceusage.googleapis.com \
        --project "${PROJECT_ID}"; then
        echo -e "${RED}Error: Failed to enable required APIs. Check your permissions.${NC}"
        return 1
    fi
    echo -e "${GREEN}APIs enabled successfully.${NC}"
    return 0
}

# --- Deployment Configuration ---

select_deployment_type() {
    echo ""
    echo -e "${BLUE}--- Deployment Topology Selection ---${NC}"
    echo "1. Greenfield (New GCP Project Deployment)"
    echo "2. Brownfield (Stellar Engine Integration)"
    echo "3. Custom Brownfield (Manual Configuration)"
    read -p "Select an option [1-3]: " DEPLOYMENT_CHOICE

    if [[ ! "$DEPLOYMENT_CHOICE" =~ ^[1-3]$ ]]; then
        echo -e "${RED}Invalid selection.${NC}"
        return 1
    fi

    if [[ "$DEPLOYMENT_CHOICE" == "1" ]]; then # Greenfield
        DEPLOYMENT_TYPE_TEXT="Greenfield (New GCP Project Deployment)"
        IS_BROWNFIELD="false"
        IS_CUSTOM="false"
    elif [[ "$DEPLOYMENT_CHOICE" == "2" ]]; then # Brownfield
        DEPLOYMENT_TYPE_TEXT="Brownfield (Stellar Engine Integration)"
        IS_BROWNFIELD="true"
        IS_CUSTOM="false"
    elif [[ "$DEPLOYMENT_CHOICE" == "3" ]]; then # Custom Brownfield
        DEPLOYMENT_TYPE_TEXT="Custom Brownfield (Manual Configuration)"
        IS_BROWNFIELD="false"
        IS_CUSTOM="true"
    fi
    
    return 0
}

discover_infrastructure() {
    # Initialize variables
    ENVIRONMENT=""
    TENANT="g4g"
    TENANT_IAC_PROJECT=""
    CMEK_PROJECT_ID=""
    CMEK_US_KEYRING=""
    CMEK_STATE_KEY=""
    CMEK_US_RESOURCES_KEY=""

    echo ""
    echo -e "${BLUE}--- Infrastructure Discovery ---${NC}"

    # 0. Prefix Discovery
    if [[ "$IS_BROWNFIELD" == "true" ]]; then
        PREFIX=$(echo "$PROJECT_ID" | cut -d'-' -f1 | cut -d'-' -f1-6)
        echo -e "Derived Prefix: ${YELLOW}${PREFIX}${NC}"
    elif [[ "$IS_CUSTOM" == "true" ]]; then
        read -p "Enter a prefix for your resources (<= 6 characters): " INPUT_PREFIX
        PREFIX=${INPUT_PREFIX:-"sedev"}
    else 
        # Greenfield
        read -p "Enter a prefix for your resources (<= 6 characters): " PREFIX
    fi

    if [[ "$IS_BROWNFIELD" == "true" ]]; then
        # 1. Extract Environment and Tenant
        # Format: prefix-env-tenant-main-0
        ENVIRONMENT=$(echo "$PROJECT_ID" | cut -d'-' -f2)
        TENANT_VAL=$(echo "$PROJECT_ID" | cut -d'-' -f3)
        
        # Validate extraction (basic check)
        if [[ -z "$ENVIRONMENT" || -z "$TENANT_VAL" ]]; then
             echo -e "${RED}Error: Could not derive Environment or Tenant from Project ID.${NC}"
             echo -e "${YELLOW}Standard Pattern: prefix-env-tenant-main-0${NC}"
             read -p "Switch to Custom Brownfield? (y/n): " SWITCH
             if [[ "$SWITCH" == "y" || "$SWITCH" == "Y" ]]; then
                 IS_BROWNFIELD="false"
                 IS_CUSTOM="true"
                 discover_infrastructure
                 return
             else
                 return 1
             fi
        fi
        
        # If tenant was extracted, use it (though default is g4g, usually it matches)
        if [[ -n "$TENANT_VAL" ]]; then
            TENANT="$TENANT_VAL"
        fi
        
        normalize_environment
        
        # 2. Check Tenant IaC Project
        POTENTIAL_IAC_PROJECT="${PREFIX}-${ENVIRONMENT}-${TENANT}-iac-core-0"
        echo "Checking for Tenant IaC Project: ${POTENTIAL_IAC_PROJECT}..."
        
        if gcloud projects describe "${POTENTIAL_IAC_PROJECT}" &>/dev/null; then
            TENANT_IAC_PROJECT="${POTENTIAL_IAC_PROJECT}"
            echo -e "Found Tenant IaC Project: ${GREEN}${TENANT_IAC_PROJECT}${NC}"
        else
            echo -e "${YELLOW}Tenant IaC Project not found.${NC}"
            echo -e "${YELLOW}Standard Stellar Engine Landing Zone framework not detected.${NC}"
            read -p "Switch to Custom Brownfield? (y/n): " SWITCH
             if [[ "$SWITCH" == "y" || "$SWITCH" == "Y" ]]; then
                 IS_BROWNFIELD="false"
                 IS_CUSTOM="true"
                 discover_infrastructure
                 return
             else
                 return 1
             fi
        fi

        # 3. Check State Bucket
        POTENTIAL_BUCKET="${PREFIX}-${ENVIRONMENT}-${TENANT}-iac-0"
        echo "Checking for Terraform State Bucket: ${POTENTIAL_BUCKET}..."
        if gcloud storage buckets describe "gs://${POTENTIAL_BUCKET}" &>/dev/null; then
            STATE_BUCKET="${POTENTIAL_BUCKET}"
            echo -e "Found Terraform State Bucket: ${GREEN}${STATE_BUCKET}${NC}"
        else
             echo -e "${YELLOW}Terraform State Bucket not found (Will be created).${NC}"
             STATE_BUCKET=""
        fi

        # 4. Check Keyrings and Keys
        # Prioritize US Multi-Region for CMEK_US_KEYRING
        echo "Searching for CMEK Keyring in the US multi-region..."
        
        # Determine the target project for CMEK
        if [[ "$IS_BROWNFIELD" == "true" ]]; then
            echo "Searching for 'cmek-*' project under 'StellarEngine-*' Assured Workloads folder..."
            STELLAR_FOLDER_ID=$(gcloud resource-manager folders list --organization="${ORG_ID}" --filter="displayName~^StellarEngine-" --format="value(name)" 2>/dev/null | head -n 1)
            
            if [[ -n "$STELLAR_FOLDER_ID" ]]; then
                STELLAR_FOLDER_ID=$(basename "$STELLAR_FOLDER_ID")
                FOUND_CMEK_PROJECT=$(gcloud projects list --filter="name:cmek-* AND parent.id:${STELLAR_FOLDER_ID}" --format="value(projectId)" 2>/dev/null | head -n 1)
                
                if [[ -n "$FOUND_CMEK_PROJECT" ]]; then
                    echo -e "Found CMEK Project: ${GREEN}${FOUND_CMEK_PROJECT}${NC}"
                    CMEK_PROJECT_ID="${FOUND_CMEK_PROJECT}"
                else
                    echo -e "${YELLOW}Could not find 'cmek-*' project under StellarEngine folder. Defaulting to ${TENANT_IAC_PROJECT}.${NC}"
                    CMEK_PROJECT_ID="${TENANT_IAC_PROJECT}"
                fi
            else
                echo -e "${YELLOW}Could not find 'StellarEngine-*' folder. Defaulting to ${TENANT_IAC_PROJECT}.${NC}"
                CMEK_PROJECT_ID="${TENANT_IAC_PROJECT}"
            fi
        else
            CMEK_PROJECT_ID="${TENANT_IAC_PROJECT}"
        fi
        # Capitalize first letter of Environment for KeyRing name (e.g. prod -> Prod)
        US_KEYRING_NAME="${CAP_ENV}-${TENANT}-keyring"
        US_KEYRING_ID="projects/${CMEK_PROJECT_ID}/locations/us/keyRings/${US_KEYRING_NAME}"
        
        # Check US Keyring
        if gcloud kms keyrings describe "${US_KEYRING_ID}" &>/dev/null; then
            echo -e "Found US Keyring: ${GREEN}${US_KEYRING_NAME}${NC}"
            CMEK_US_KEYRING="${US_KEYRING_ID}"
            
            # Check 'gcs' key in US Keyring
            GCS_KEY_ID="${CMEK_US_KEYRING}/cryptoKeys/gcs"
            if gcloud kms keys describe "${GCS_KEY_ID}" &>/dev/null; then
                 echo -e "Found US GCS Crypto Key: ${GREEN}gcs${NC}"
                 CMEK_STATE_KEY="${GCS_KEY_ID}"
            fi
            
            # Check 'gemini-enterprise' key in US Keyring
            GEMINI_KEY_ID="${CMEK_US_KEYRING}/cryptoKeys/gemini-enterprise"
            if gcloud kms keys describe "${GEMINI_KEY_ID}" &>/dev/null; then
                 echo -e "Found US Gemini Enterprise Crypto Key: ${GREEN}gemini-enterprise${NC}"
                 CMEK_US_RESOURCES_KEY="${GEMINI_KEY_ID}"
            fi
        else
            echo -e "${YELLOW}US Keyring not found.${NC}"
            CMEK_US_KEYRING=""
        fi

        # 5. Fallback for State Key (Regional) if US GCS Key not found
        if [[ -z "$CMEK_STATE_KEY" ]]; then
             # If state bucket exists, check what key protects it
             if [[ -n "$STATE_BUCKET" ]]; then
                  echo "Checking Terraform State Bucket encryption..."
                  BUCKET_JSON=$(gcloud storage buckets describe "gs://${STATE_BUCKET}" --format="json" 2>/dev/null || echo "{}")
                  BUCKET_KEY=$(echo "$BUCKET_JSON" | jq -r '.default_kms_key // .default_kms_key_name // .encryption.defaultKmsKeyName // empty')
                  if [[ -n "$BUCKET_KEY" ]]; then
                       CMEK_STATE_KEY="${BUCKET_KEY}"
                       echo -e "Using Existing Terraform State Bucket Crypto Key: ${YELLOW}${CMEK_STATE_KEY}${NC}"
                  fi
             fi
             
             # If still no key, check regional keyring
              if [[ -z "$CMEK_STATE_KEY" ]]; then
                   REGIONAL_KEYRING_ID="projects/${CMEK_PROJECT_ID}/locations/${REGION}/keyRings/${CAP_ENV}-${TENANT}-keyring"
                  echo "Checking Regional Keyring: ${REGIONAL_KEYRING_ID}..."
                  if gcloud kms keyrings describe "${REGIONAL_KEYRING_ID}" &>/dev/null; then
                        REGIONAL_GCS_KEY="${REGIONAL_KEYRING_ID}/cryptoKeys/gcs"
                        if gcloud kms keys describe "${REGIONAL_GCS_KEY}" &>/dev/null; then
                             CMEK_STATE_KEY="${REGIONAL_GCS_KEY}"
                             echo -e "Found Regional GCS Crypto Key: ${YELLOW}${CMEK_STATE_KEY}${NC}"
                        fi
                  fi
             fi
        fi

        # Ensure correct outputs
        echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
        echo -e "Tenant: ${YELLOW}${TENANT}${NC}"

    elif [[ "$IS_CUSTOM" == "true" ]]; then
        read -p "Enter Environment identifier (e.g., prod): " ENVIRONMENT
        normalize_environment
        read -p "Enter Tenant IaC Project ID [${TENANT_IAC_PROJECT}]: " INPUT_TENANT_IAC_PROJECT
        TENANT_IAC_PROJECT=${INPUT_TENANT_IAC_PROJECT:-$TENANT_IAC_PROJECT}
        
        # State Bucket
        read -p "Enter Terraform State Bucket Name (leave blank to create) [${STATE_BUCKET}]: " INPUT_STATE_BUCKET
        STATE_BUCKET=${INPUT_STATE_BUCKET:-$STATE_BUCKET}
        if [[ -n "$STATE_BUCKET" ]]; then
             # Validate Encryption
             BUCKET_JSON=$(gcloud storage buckets describe "gs://${STATE_BUCKET}" --format="json" 2>/dev/null || echo "{}")
             BUCKET_KEY=$(echo "$BUCKET_JSON" | jq -r '.default_kms_key // .default_kms_key_name // .encryption.defaultKmsKeyName // empty')
             if [[ -z "$BUCKET_KEY" ]]; then
                  echo -e "${RED}WARNING: State Bucket '${STATE_BUCKET}' is NOT encrypted with CMEK.${NC}"
                  echo -e "Compliance requires CMEK. A new bucket will be created."
                  STATE_BUCKET=""
                  CMEK_STATE_KEY=""
             else
                  CMEK_STATE_KEY="${BUCKET_KEY}"
                  echo -e "Using Existing Terraform State Bucket Crypto Key: ${YELLOW}${CMEK_STATE_KEY}${NC}"
             fi
        fi
        
        read -p "Enter CMEK Project ID [${CMEK_PROJECT_ID}]: " INPUT_CMEK_PROJECT
        CMEK_PROJECT_ID=${INPUT_CMEK_PROJECT:-$CMEK_PROJECT_ID}
        
        read -p "Enter US Multi-Region Keyring ID (optional) [${CMEK_US_KEYRING}]: " INPUT_CMEK_KEYRING
        CMEK_US_KEYRING=${INPUT_CMEK_KEYRING:-$CMEK_US_KEYRING}
        
        read -p "Enter US Gemini Resources Key ID (optional) [${CMEK_US_RESOURCES_KEY}]: " INPUT_CMEK_GEMINI_KEY
        CMEK_US_RESOURCES_KEY=${INPUT_CMEK_GEMINI_KEY:-$CMEK_US_RESOURCES_KEY}

    else 
        # Greenfield
        # Greenfield (No Landing Zone)
        read -p "Enter Environment identifier (e.g., prod): " ENVIRONMENT
        normalize_environment
        TENANT_IAC_PROJECT=""
        STATE_BUCKET="${PREFIX}-${ENVIRONMENT}-${TENANT}-tfstate-0"
        CMEK_PROJECT_ID="${PROJECT_ID}"
        CMEK_STATE_KEY=""
        CMEK_US_KEYRING=""
        CMEK_US_RESOURCES_KEY=""
    fi
    return 0
}

# --- State Hydration ---

hydrate_from_state() {
    # Check if we have a bucket to read from (either BUCKET_NAME or derived from STATE_BUCKET)
    local bucket=""
    if [[ -n "$BUCKET_NAME" ]]; then
        bucket="$BUCKET_NAME"
    elif [[ -n "$STATE_BUCKET" ]]; then
        bucket=$(echo "$STATE_BUCKET" | sed 's#gs://##' | sed 's/\/$//')
        export BUCKET_NAME="$bucket"
    fi

    if [[ -z "$bucket" ]]; then
        return 0
    fi

    echo "Checking for existing state in gs://${bucket}..."
    STATE_CONTENT=$(gcloud storage cat "gs://${bucket}/terraform/state/stage-0/default.tfstate" 2>/dev/null || echo "{}")
    
    # Project ID
    if [[ -z "$PROJECT_ID" ]]; then
        VAL=$(echo "$STATE_CONTENT" | jq -r '.outputs.main_project_id.value // empty')
        if [[ -n "$VAL" ]]; then
            PROJECT_ID="$VAL"
            echo -e "Hydrated Project ID from state: ${YELLOW}${PROJECT_ID}${NC}"
        fi
    fi

    # Region
    if [[ -z "$REGION" ]]; then
        VAL=$(echo "$STATE_CONTENT" | jq -r '.outputs.region.value // empty')
        if [[ -n "$VAL" ]]; then
            REGION="$VAL"
            echo -e "Hydrated Region from state: ${YELLOW}${REGION}${NC}"
        fi
    fi

    # Load Balancer IP (Useful for later steps)
    VAL=$(echo "$STATE_CONTENT" | jq -r '.outputs.gemini_enterprise_ip.value // empty')
    if [[ -n "$VAL" ]]; then
         export GEMINI_IP="$VAL"
    fi
}

ensure_prerequisites() {
    echo ""
    echo -e "${BLUE}--- Ensuring Prerequisites ---${NC}"
    
    # Defaults
    ENVIRONMENT=${ENVIRONMENT:-"prod"}
    normalize_environment
    
    # 1. State Key Creation (if missing)
    if [[ -z "$CMEK_STATE_KEY" ]]; then
        echo -e "${YELLOW}Searching for CMEK State Key in the US multi-region...${NC}"
        
        KEYRING_NAME="${CAP_ENV}-${TENANT}-keyring"
        KEY_NAME="gcs"
        LOCATION="us"
        
        # Identify Target Project
        TARGET_KMS_PROJECT="${CMEK_PROJECT_ID}"
        
        # Create Keyring if not exists
        if ! gcloud kms keyrings describe "${KEYRING_NAME}" --location="${LOCATION}" --project="${TARGET_KMS_PROJECT}" &>/dev/null; then
             echo "Creating Keyring '${KEYRING_NAME}' in ${LOCATION}..."
             gcloud kms keyrings create "${KEYRING_NAME}" --location="${LOCATION}" --project="${TARGET_KMS_PROJECT}"
        fi
        
        CMEK_US_KEYRING="projects/${TARGET_KMS_PROJECT}/locations/${LOCATION}/keyRings/${KEYRING_NAME}"
        
        # Create Key if not exists
        FULL_KEY_NAME="${CMEK_US_KEYRING}/cryptoKeys/${KEY_NAME}"
        if ! gcloud kms keys describe "${FULL_KEY_NAME}" &>/dev/null; then
             echo "Creating Key '${KEY_NAME}'..."
             gcloud kms keys create "${KEY_NAME}" \
                 --keyring="${KEYRING_NAME}" \
                 --location="${LOCATION}" \
                 --project="${TARGET_KMS_PROJECT}" \
                 --purpose="encryption" \
                 --protection-level="hsm" \
                 --rotation-period="7776000s" \
                 --next-rotation-time="$(date -v+90d -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '+90 days' +%Y-%m-%dT%H:%M:%SZ)"
        fi
        
        CMEK_STATE_KEY="${FULL_KEY_NAME}"
        echo -e "Using CMEK State Key: ${GREEN}${CMEK_STATE_KEY}${NC}"
        
        # Grant Permissions
        echo -e "${YELLOW}Granting permissions on CMEK State Key...${NC}"
        CURRENT_USER=$(gcloud config get-value account 2>/dev/null)
        
        # User
        gcloud kms keys add-iam-policy-binding "${CMEK_STATE_KEY}" \
            --member="user:${CURRENT_USER}" \
            --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" --quiet
            
        # Storage Service Account (for the project where the bucket will live)
        # Verify if TENANT_IAC_PROJECT is set, use that, else use PROJECT_ID
        BUCKET_PROJECT="${TENANT_IAC_PROJECT}"
        if [[ -z "$BUCKET_PROJECT" ]]; then
             BUCKET_PROJECT="${PROJECT_ID}"
        fi
        
        # Ensure Storage Service Agent exists
        gcloud beta services identity create --service=storage.googleapis.com --project="${BUCKET_PROJECT}" &>/dev/null || true

        BUCKET_PROJECT_NUMBER=$(gcloud projects describe "${BUCKET_PROJECT}" --format="value(projectNumber)")
        STORAGE_SA="service-${BUCKET_PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"
               if gcloud kms keys add-iam-policy-binding "${CMEK_STATE_KEY}" \
             --member="serviceAccount:${STORAGE_SA}" \
             --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" --quiet &>/dev/null; then
             echo -e "${GREEN}Granted Storage SA (${STORAGE_SA}) access to CMEK State Key.${NC}"
        else
             echo -e "${RED}WARNING: Could not grant Storage SA access. Check permissions.${NC}"
        fi
    fi
    
    # 2. State Bucket Creation (Greenfield only)
    echo -e "${YELLOW}Searching for Terraform State Bucket...${NC}"
    if [[ "$IS_BROWNFIELD" == "false" && "$IS_CUSTOM" == "false" ]]; then
         # Ensure BUCKET_NAME is set from STATE_BUCKET if not already
        if [[ -z "$BUCKET_NAME" && -n "$STATE_BUCKET" ]]; then
            BUCKET_NAME=$(echo "$STATE_BUCKET" | sed 's/gs:\/\/ //' | sed 's/\/$//')
        fi
        
        # Use CMEK_STATE_KEY if available (derived above)
        KMS_KEY_ID="${CMEK_STATE_KEY}"

        if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
            echo "Creating state bucket gs://${BUCKET_NAME}..."
            
            local create_output
            local create_status=0

            # Grant Storage Service Agent access to CMEK if used (Double Check / Re-grant just in case)
            if [[ -n "$KMS_KEY_ID" ]]; then
                # Ensure Storage Service Agent exists
                gcloud beta services identity create --service=storage.googleapis.com --project="${PROJECT_ID}" &>/dev/null || true

                PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
                STORAGE_SA="service-${PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com"
                
                echo "Ensuring Storage Service Agent (${STORAGE_SA}) has access to ${KMS_KEY_ID}..."
                gcloud kms keys add-iam-policy-binding "${KMS_KEY_ID}" \
                    --member="serviceAccount:${STORAGE_SA}" \
                    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" \
                    --project="${CMEK_PROJECT_ID}" &>/dev/null || echo -e "${RED}WARNING: Failed to grant IAM binding on key.${NC}"
                
                create_output=$(gcloud storage buckets create "gs://${BUCKET_NAME}" --project "${PROJECT_ID}" --location "us" --uniform-bucket-level-access --default-encryption-key="${KMS_KEY_ID}" 2>&1) || create_status=$?
            else
                create_output=$(gcloud storage buckets create "gs://${BUCKET_NAME}" --project "${PROJECT_ID}" --location "us" --uniform-bucket-level-access 2>&1) || create_status=$?
            fi

            if [[ $create_status -eq 0 ]]; then
                echo -e "${GREEN}Bucket created successfully!${NC}"
            elif [[ "$create_output" == *"409"* && "$create_output" == *"namespace"* ]]; then
                echo -e "${RED}${create_output}${NC}"
                echo -e "${RED}The bucket name '${BUCKET_NAME}' is already taken globally.${NC}"
                echo -e "${YELLOW}Please restart the script and select a new, unique PREFIX and/or ENVIRONMENT identifier to ensure clean infrastructure alignment.${NC}"
                exit 1
            else
                echo -e "${RED}Failed to create state bucket:${NC}"
                echo "$create_output"
                exit 1
            fi
        else
            echo -e "Using Terraform State Bucket: ${GREEN}${BUCKET_NAME}${NC}"
        fi
    fi

    # 2. State Bucket Creation (if missing)
    if [[ -z "$STATE_BUCKET" ]]; then
        echo -e "${YELLOW}Terraform State Bucket not found. Creating...${NC}"
        
        if [[ -n "$TENANT_IAC_PROJECT" ]]; then
             BUCKET_PROJECT="${TENANT_IAC_PROJECT}"
        else
             BUCKET_PROJECT="${PROJECT_ID}"
        fi
        
        # Construct Initial Name
        NEW_BUCKET_NAME="${PREFIX}-${ENVIRONMENT}-${TENANT}-iac-0"
        
        echo "Creating Bucket '${NEW_BUCKET_NAME}' in ${REGION}..."
        
        # Note: If REGION != 'us' and Key is 'us', this might fail if not dual-region. 
        # Capture output and exit status
        local create_output
        local create_status=0
        
        if [[ -n "$CMEK_STATE_KEY" ]]; then
            create_output=$(gcloud storage buckets create "gs://${NEW_BUCKET_NAME}" \
                --project="${BUCKET_PROJECT}" \
                --location="${REGION}" \
                --default-encryption-key="${CMEK_STATE_KEY}" \
                --uniform-bucket-level-access 2>&1) || create_status=$?

            # Fallback logic if region mismatch suspected
            if [[ $create_status -ne 0 && "$create_output" != *"409"* && "$CMEK_STATE_KEY" == *"/locations/us/"* ]]; then
                echo -e "${RED}Failed to create bucket with CMEK in ${REGION}. Retrying with 'US' location...${NC}"
                create_output=$(gcloud storage buckets create "gs://${NEW_BUCKET_NAME}" \
                    --project="${BUCKET_PROJECT}" \
                    --location="us" \
                    --default-encryption-key="${CMEK_STATE_KEY}" \
                    --uniform-bucket-level-access 2>&1) || create_status=$?
            fi
        else
            create_output=$(gcloud storage buckets create "gs://${NEW_BUCKET_NAME}" \
                --project="${BUCKET_PROJECT}" \
                --location="${REGION}" \
                --uniform-bucket-level-access 2>&1) || create_status=$?
        fi

        if [[ $create_status -eq 0 ]]; then
            # Success
            echo -e "${GREEN}Bucket created successfully!${NC}"
            STATE_BUCKET="${NEW_BUCKET_NAME}"
            echo -e "Using Terraform State Bucket: ${GREEN}${STATE_BUCKET}${NC}"
        elif [[ "$create_output" == *"409"* && "$create_output" == *"namespace"* ]]; then
            # Conflict on globally unique name
            echo -e "${RED}${create_output}${NC}"
            echo -e "${RED}The bucket name '${NEW_BUCKET_NAME}' is already taken globally.${NC}"
            echo -e "${YELLOW}Please restart the script and select a new, unique PREFIX and/or ENVIRONMENT identifier to ensure clean infrastructure alignment.${NC}"
            exit 1
        else
            # Other error
            echo -e "${RED}Failed to create bucket:${NC}"
            echo "$create_output"
            exit 1
        fi
    fi

    echo -e "${GREEN}Prerequisites met successfully${NC}"
    
    return 0
}

# --- Stage 0 Functions ---

check_org_policies() {
    echo "Checking Organization Policies..."
    local failed=0

    # 1. compute.disableInternetNetworkEndpointGroup
    echo -n "Checking compute.disableInternetNetworkEndpointGroup... "
    POLICY_JSON=$(gcloud org-policies describe compute.disableInternetNetworkEndpointGroup --project="${PROJECT_ID}" --effective --format="json" 2>/dev/null || true)
    
    if [[ -z "$POLICY_JSON" ]]; then
        echo -e "${YELLOW}Unable to verify (Check Manually)${NC}"
    else
        # Check both v1 (booleanPolicy) and v2 (spec.rules) formats
        # If any rule enforces it, we consider it enforced.
        IS_ENFORCED=$(echo "$POLICY_JSON" | jq -r '(.booleanPolicy.enforced == true) or (try (.spec.rules[] | .enforce == true) catch false)' 2>/dev/null | grep "true" || true)
        
        if [[ -n "$IS_ENFORCED" ]]; then
            echo -e "${RED}Enforced (FAIL) - Internet NEGs are disabled${NC}"
            failed=1
        else
            echo -e "${GREEN}Disabled (OK)${NC}"
        fi
    fi

    # 2. compute.restrictLoadBalancerCreationForTypes (Only if External)
    if [[ "$DEPLOYMENT_TYPE" == "external" ]]; then
        echo -n "Checking compute.restrictLoadBalancerCreationForTypes... "
        POLICY_JSON=$(gcloud org-policies describe compute.restrictLoadBalancerCreationForTypes --project="${PROJECT_ID}" --effective --format="json" 2>/dev/null || true)
        
        if [[ -z "$POLICY_JSON" ]]; then
            echo -e "${YELLOW}Unable to verify (Check Manually)${NC}"
        else
            # Extract v1 and v2 values
            ALL_VALUES=$(echo "$POLICY_JSON" | jq -r '.listPolicy.allValues // "Unspecified"' 2>/dev/null || echo "Error")
            V2_ALLOW_ALL=$(echo "$POLICY_JSON" | jq -r 'try (.spec.rules[] | select(.allowAll == true) | "true") catch empty' 2>/dev/null | head -n1)
            V2_DENY_ALL=$(echo "$POLICY_JSON" | jq -r 'try (.spec.rules[] | select(.denyAll == true) | "true") catch empty' 2>/dev/null | head -n1)
            
            HAS_ALLOWED_VALUES=$(echo "$POLICY_JSON" | jq -r 'if (.listPolicy? | has("allowedValues")) or (try any(.spec.rules[]?; .values? | has("allowedValues")) catch false) then "true" else "false" end' 2>/dev/null)
            
            ALLOWED_VALUES=$(echo "$POLICY_JSON" | jq -r '.listPolicy.allowedValues[]?, .spec.rules[].values.allowedValues[]?' 2>/dev/null || true)
            DENIED_VALUES=$(echo "$POLICY_JSON" | jq -r '.listPolicy.deniedValues[]?, .spec.rules[].values.deniedValues[]?' 2>/dev/null || true)
            
            if [[ "$ALL_VALUES" == "Error" ]]; then
                 echo -e "${YELLOW}Error parsing policy (Check Manually)${NC}"
            elif [[ "$ALL_VALUES" == "ALLOW" || "$V2_ALLOW_ALL" == "true" ]]; then
                 echo -e "${GREEN}Allowed (OK)${NC}"
            elif [[ "$ALL_VALUES" == "DENY" || "$V2_DENY_ALL" == "true" ]]; then
                 echo -e "${RED}Denied (FAIL) - Policy Enforces DENY ALL${NC}"
                 failed=1
            else
                 # Check allowed/denied lists
                 IS_ALLOWED="true" # Default to true if not explicitly restricted
                 
                 # If allowed_values is present (key exists), we MUST be in it
                 if [[ "$HAS_ALLOWED_VALUES" == "true" ]]; then
                     IS_ALLOWED="false"
                     if [[ -n "$ALLOWED_VALUES" ]]; then
                         if echo "$ALLOWED_VALUES" | grep -qE "EXTERNAL_HTTP_HTTPS|EXTERNAL_MANAGED_HTTP_HTTPS"; then
                             IS_ALLOWED="true"
                         fi
                     fi
                 fi
                 
                 # If denied_values is present, we MUST NOT be in it
                 if [[ -n "$DENIED_VALUES" ]]; then
                     if echo "$DENIED_VALUES" | grep -qE "EXTERNAL_HTTP_HTTPS|EXTERNAL_MANAGED_HTTP_HTTPS"; then
                         IS_ALLOWED="false"
                     fi
                 fi
                 
                 if [[ "$IS_ALLOWED" == "true" ]]; then
                     echo -e "${GREEN}Allowed (OK)${NC}"
                 else
                     echo -e "${RED}Denied (FAIL) - Policy restricts External Load Balancers${NC}"
                     failed=1
                 fi
            fi
        fi
    fi

    if [[ "$failed" -eq 1 ]]; then
        echo -e "${RED}WARNING: One or more Organization Policies may prevent deployment.${NC}"
        read -p "Do you want to proceed anyway? (y/N): " PROCEED
        if [[ "$PROCEED" != "y" && "$PROCEED" != "Y" ]]; then
            return 1
        fi
    fi
    return 0
}

configure_access_policies() {
    
    # Initialize Defaults
    CREATE_IP_BASED_ACCESS="true"
    CREATE_US_ACCESS="true"
    CREATE_TIME_ACCESS="true"
    CREATE_EXPIRE_ACCESS="true"
    CREATE_LENIENT_DEVICE_ACCESS="true"
    CREATE_MODERATE_DEVICE_ACCESS="true"
    CREATE_STRICT_DEVICE_ACCESS="true"
    ENABLE_CEP_BOOL="false"
    
    # Existing Access Levels Check
    echo "Checking for existing Access Levels in Policy ${ACCESS_POLICY_NUMBER}..."
    EXISTING_LEVELS=$(gcloud access-context-manager levels list --policy="${ACCESS_POLICY_NUMBER}" --format="value(name)" || echo "")
    
    # 1. IP Based Access
    echo ""
    echo -e "--- IP Based Access ---"
    EXISTING_IP_ACCESS=$(echo "$EXISTING_LEVELS" | grep -E "(/|^)ip_based_access$" || true)
    
    if [[ -n "$EXISTING_IP_ACCESS" ]]; then
        # Check if managed by Terraform
        if [[ "$MANAGED_ACCESS_LEVELS" == *"ip_based_access"* ]]; then
             echo -e "${GREEN}Found existing MANAGED Access Level 'ip_based_access'. Preserving/Updating.${NC}"
             CREATE_IP_BASED_ACCESS="true"
             # Still offer to add IPs
             read -p "Do you want to add additional IP ranges? (y/N): " ADD_IPS
        else
             echo -e "${YELLOW}Access Level 'ip_based_access' already exists (Unmanaged).${NC}"
             echo "Current Configuration:"
             gcloud access-context-manager levels describe ip_based_access --policy="${ACCESS_POLICY_NUMBER}" --format="value(basic.conditions.ipSubnetworks)" 2>/dev/null || echo "Error fetching IPs"
             
             read -p "Do you want to add additional IP ranges? (y/N): " ADD_IPS
             if [[ "$ADD_IPS" == "y" || "$ADD_IPS" == "Y" ]]; then
                 CREATE_IP_BASED_ACCESS="true"
             else
                 echo "Skipping update of 'ip_based_access'."
                 CREATE_IP_BASED_ACCESS="false"
             fi
        fi
    else
        echo "Access Level 'ip_based_access' does not exist."
        CREATE_IP_BASED_ACCESS="true"
    fi
    
    # Prompt for IPs if we are creating or updating
    ALLOWED_IPS="[]"
    if [[ "$CREATE_IP_BASED_ACCESS" == "true" ]]; then
        echo ""
        echo "Enter IP ranges allowed to access the Load Balancer (CIDR format)."
        echo "RECOMMENDED: Set this to the IP range of the agency's corporate gateway."
        read -p "Enter IP Ranges (comma-separated, e.g., 203.0.113.0/24) (leave blank if not required): " IP_RANGES_INPUT
        
        if [[ -n "$IP_RANGES_INPUT" ]]; then
            IFS=',' read -ra IP_ADDRS <<< "$IP_RANGES_INPUT"
            JSON_IPS=""
            for ip in "${IP_ADDRS[@]}"; do
                ip=$(echo "$ip" | xargs)
                if [[ -n "$JSON_IPS" ]]; then
                    JSON_IPS="$JSON_IPS, \"$ip\""
                else
                    JSON_IPS="\"$ip\""
                fi
            done
            ALLOWED_IPS="[$JSON_IPS]"
        else
            echo "No IPs provided. Updating configuration to disable IP based access."
            CREATE_IP_BASED_ACCESS="false"
        fi
    fi

    # 2. US Region Access
    echo ""
    echo -e "--- US Region Access ---"
    if echo "$EXISTING_LEVELS" | grep -qE "(/|^)us$"; then
        if [[ "$MANAGED_ACCESS_LEVELS" == *"us"* ]]; then
             echo -e "${GREEN}Found existing MANAGED Access Level 'us'. Preserving.${NC}"
             CREATE_US_ACCESS="true"
        else
             echo -e "${YELLOW}Access Level 'us' already exists (Unmanaged). Skipping.${NC}"
             CREATE_US_ACCESS="false"
        fi
    else
        read -p "Restrict incoming traffic to only originate from the 'US'? (y/N): " US_CHOICE
        if [[ "$US_CHOICE" == "y" || "$US_CHOICE" == "Y" ]]; then
            CREATE_US_ACCESS="true"
        else
            CREATE_US_ACCESS="false"
        fi
    fi

    # 3. Time Based Access
    echo ""
    echo -e "--- Time Based Access ---"
    if echo "$EXISTING_LEVELS" | grep -qE "(/|^)time$"; then
        if [[ "$MANAGED_ACCESS_LEVELS" == *"time"* ]]; then
             echo -e "${GREEN}Found existing MANAGED Access Level 'time'. Preserving.${NC}"
             CREATE_TIME_ACCESS="true"
        else
             echo -e "${YELLOW}Access Level 'time' already exists (Unmanaged). Skipping.${NC}"
             CREATE_TIME_ACCESS="false"
        fi
    else
        read -p "Restrict incoming traffic based on a specific time schedule (Business Hours)? (y/N): " TIME_CHOICE
        if [[ "$TIME_CHOICE" == "y" || "$TIME_CHOICE" == "Y" ]]; then
            CREATE_TIME_ACCESS="true"
            read -p "Enter Start Day (1=Mon, 7=Sun) [1]: " ACCESS_START_DAY
            ACCESS_START_DAY=${ACCESS_START_DAY:-1}
            read -p "Enter End Day (1=Mon, 7=Sun) [5]: " ACCESS_END_DAY
            ACCESS_END_DAY=${ACCESS_END_DAY:-5}
            read -p "Enter Start Hour (0-23) [7]: " ACCESS_START_HOUR
            ACCESS_START_HOUR=${ACCESS_START_HOUR:-7}
            read -p "Enter End Hour (0-23) [21]: " ACCESS_END_HOUR
            ACCESS_END_HOUR=${ACCESS_END_HOUR:-21}
            read -p "Enter Time Zone (e.g. America/New_York) [America/New_York]: " ACCESS_TIME_ZONE
            ACCESS_TIME_ZONE=${ACCESS_TIME_ZONE:-"America/New_York"}
        else
            CREATE_TIME_ACCESS="false"
        fi
    fi

    # 4. Expiration Access
    echo ""
    echo -e "--- Expiration Access ---"
    if echo "$EXISTING_LEVELS" | grep -qE "(/|^)expire$"; then
        if [[ "$MANAGED_ACCESS_LEVELS" == *"expire"* ]]; then
             echo -e "${GREEN}Found existing MANAGED Access Level 'expire'. Preserving.${NC}"
             CREATE_EXPIRE_ACCESS="true"
        else
             echo -e "${YELLOW}Access Level 'expire' already exists (Unmanaged). Skipping.${NC}"
             CREATE_EXPIRE_ACCESS="false"
        fi
    else
        read -p "Block incoming traffic after a certain expiration date? (y/N): " EXPIRE_CHOICE
        if [[ "$EXPIRE_CHOICE" == "y" || "$EXPIRE_CHOICE" == "Y" ]]; then
            CREATE_EXPIRE_ACCESS="true"
            read -p "Enter Expiration Timestamp (RFC 3339 format, e.g. 2028-01-01T00:00:00Z) [2028-01-01T00:00:00Z]: " ACCESS_EXPIRATION_TIMESTAMP
            ACCESS_EXPIRATION_TIMESTAMP=${ACCESS_EXPIRATION_TIMESTAMP:-"2028-01-01T00:00:00Z"}
        else
            CREATE_EXPIRE_ACCESS="false"
        fi
    fi

    # 5. Chrome Enterprise Premium
    echo ""
    echo -e "--- Chrome Enterprise Premium ---"
    read -p "Enable Chrome Enterprise Premium (Zero Trust) to access device-level attributes? (y/N): " CEP_CHOICE
    if [[ "$CEP_CHOICE" == "y" || "$CEP_CHOICE" == "Y" ]]; then
        ENABLE_CEP_BOOL="true"
        echo -e "${YELLOW}Note: This requires an additional subscription.${NC}"
        echo -e "Subscribe here: https://console.cloud.google.com/security/cep"
    else
        ENABLE_CEP_BOOL="false"
    fi

    # 6. Derived Device Policies
    echo ""
    echo -e "--- Device Policy Access Levels (Lenient / Moderate / Strict) ---"
    
    # Lenient Device
    if echo "$EXISTING_LEVELS" | grep -qE "(/|^)lenient_device$"; then
        if [[ "$MANAGED_ACCESS_LEVELS" == *"lenient_device"* ]]; then
             CREATE_LENIENT_DEVICE_ACCESS="true"
        else
             CREATE_LENIENT_DEVICE_ACCESS="false"
        fi
    else
        if [[ "$CREATE_US_ACCESS" == "true" || "$CREATE_IP_BASED_ACCESS" == "true" ]]; then
            CREATE_LENIENT_DEVICE_ACCESS="true"
        else
            CREATE_LENIENT_DEVICE_ACCESS="false"
        fi
    fi
    
    # Moderate Device
    if echo "$EXISTING_LEVELS" | grep -qE "(/|^)moderate_device$"; then
        if [[ "$MANAGED_ACCESS_LEVELS" == *"moderate_device"* ]]; then
             CREATE_MODERATE_DEVICE_ACCESS="true"
        else
             CREATE_MODERATE_DEVICE_ACCESS="false"
        fi
    else
        if [[ "$CREATE_US_ACCESS" == "true" || "$CREATE_TIME_ACCESS" == "true" || "$CREATE_EXPIRE_ACCESS" == "true" || "$CREATE_IP_BASED_ACCESS" == "true" ]]; then
            CREATE_MODERATE_DEVICE_ACCESS="true"
        else
            CREATE_MODERATE_DEVICE_ACCESS="false"
        fi
    fi
    
    # Strict Device
    if echo "$EXISTING_LEVELS" | grep -qE "(/|^)strict_device$"; then
        if [[ "$MANAGED_ACCESS_LEVELS" == *"strict_device"* ]]; then
             CREATE_STRICT_DEVICE_ACCESS="true"
        else
             CREATE_STRICT_DEVICE_ACCESS="false"
        fi
    else
        if [[ "$ENABLE_CEP_BOOL" == "true" ]]; then
            CREATE_STRICT_DEVICE_ACCESS="true"
        else
            CREATE_STRICT_DEVICE_ACCESS="false"
        fi
    fi

    echo -e "${GREEN}Access Policy Configuration Complete.${NC}"
}

configure_stage_0() {
    echo ""
    echo -e "${BLUE}--- Configure Stage 0 (Infrastructure) ---${NC}"
    mkdir -p gemini-stage-0
    
    # Check if we can reuse existing config
    if [[ -f "gemini-stage-0/terraform.tfvars" ]]; then
        echo -e "${YELLOW}Found existing configuration.${NC}"
        echo -e "${RED}WARNING: Answering 'n' will OVERWRITE existing gemini-stage-0/terraform.tfvars${NC}"
        read -p "Reuse existing configuration? (Y/n): " REUSE_CONFIG
        if [[ "$REUSE_CONFIG" != "n" && "$REUSE_CONFIG" != "N" ]]; then
            echo -e "${GREEN}Using existing configuration.${NC}"
            
            # Extract CREATE_DS_BOOL from existing tfvars for "Action Required" message logic
            echo -e "Using configuration to populate important environment variables..."
            if grep -q "create_data_stores" gemini-stage-0/terraform.tfvars; then
                EXISTING_DS_BOOL=$(grep "create_data_stores" gemini-stage-0/terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
                if [[ "$EXISTING_DS_BOOL" == "true" ]]; then
                    CREATE_DS_BOOL="true"
                fi
            fi
            
            # Even when reusing, check if Terraform State dictates we should suppress CMEK variables
            # This handles cases where resources were created, but tfvars still points to "new" logic
            echo -e "Checking configuration against existing resources in Terraform State..."
            cd gemini-stage-0
            
            # We need BUCKET_NAME. Try to grab it from deploy vars or tfvars
            if [[ -z "$BUCKET_NAME" ]]; then
                 # Try to extract from tfvars if not in env
                 BUCKET_NAME=$(grep 'terraform_state_bucket' terraform.tfvars | cut -d'=' -f2 | tr -d ' "')
                 # Clean up gs:// prefix if present in tfvars
                 BUCKET_NAME=$(echo "$BUCKET_NAME" | sed 's/gs:\/\/ //' | sed 's/\/$//')
            fi
            
            if [[ -n "$BUCKET_NAME" ]]; then
                # Ensure the tfvars file is updated with the sanitized bucket name
                sed -i '' "s/terraform_state_bucket *= *\".*\"/terraform_state_bucket = \"${BUCKET_NAME}\"/" terraform.tfvars 2>/dev/null || sed -i "s/terraform_state_bucket *= *\".*\"/terraform_state_bucket = \"${BUCKET_NAME}\"/" terraform.tfvars
                
                if terraform init -migrate-state -backend-config="bucket=${BUCKET_NAME}" -backend-config="prefix=terraform/state/stage-0" &>/dev/null; then
                     if terraform state list | grep -q "google_kms_key_ring.created"; then
                         echo -e "${YELLOW}KeyRing found in Terraform State. Updating existing config to use managed resource.${NC}"
                         # Update tfvars to clear us_keyring_name
                         # Use strict matching or regex to avoid partial matches
                         # Assuming standard format: us_keyring_name = "..."
                         sed -i '' 's/us_keyring_name *= *".*"/us_keyring_name = ""/' terraform.tfvars 2>/dev/null || sed -i 's/us_keyring_name *= *".*"/us_keyring_name = ""/' terraform.tfvars
                     fi
                     
                     if terraform state list | grep -q "google_kms_crypto_key.gemini_enterprise"; then
                         echo -e "${YELLOW}gemini-enterprise Key found in Terraform State. Updating existing config to use managed resource.${NC}"
                         sed -i '' 's/kms_key_id *= *".*"/kms_key_id = ""/' terraform.tfvars 2>/dev/null || sed -i 's/kms_key_id *= *".*"/kms_key_id = ""/' terraform.tfvars
                     fi
                     
                     if terraform state list | grep -q "google_access_context_manager_access_level"; then
                         echo -e "${YELLOW}Access Levels found in Terraform State. Setting flags to preserve resources.${NC}"
                     fi
                fi
            fi
            
            if [[ -n "$ENVIRONMENT" ]]; then
                sed -i '' "s/environment *= *\".*\"/environment = \"${ENVIRONMENT}\"/" terraform.tfvars 2>/dev/null || sed -i "s/environment *= *\".*\"/environment = \"${ENVIRONMENT}\"/" terraform.tfvars
            fi
            
            if [[ -n "$PREFIX" ]]; then
                sed -i '' "s/prefix *= *\".*\"/prefix = \"${PREFIX}\"/" terraform.tfvars 2>/dev/null || sed -i "s/prefix *= *\".*\"/prefix = \"${PREFIX}\"/" terraform.tfvars
            fi
            
            cd ..
            
            return 0
        fi
    fi

    # Run Discovery (Only if not already done)
    # If ENVIRONMENT is set, we assume discovery ran successfully at startup or was manually set.
    if [[ -z "$ENVIRONMENT" ]]; then
        if ! discover_infrastructure; then
            echo -e "${RED}Infrastructure Discovery Failed.${NC}"
            pause
            return
        fi
    fi
    
    # Ensure Prerequisites (Bucket, CMEK)
    if ! ensure_prerequisites; then
        echo -e "${RED}Prerequisite check failed.${NC}"
        pause
        return
    fi

    # 1. Assured Workloads Check
    echo ""
    echo -e "${BLUE}--- Compliance Regime (Assured Workloads) ---${NC}"
    echo "1. FedRAMP High (Default)"
    echo "2. IL4"
    echo "3. IL5"
    echo "4. None"
    read -p "What compliance regime will you be using? [1]: " REGIME_CHOICE
    REGIME_CHOICE=${REGIME_CHOICE:-1}

    COMPLIANCE_REGIME=""
    REGIME_DISPLAY=""

    case $REGIME_CHOICE in
        1)
            COMPLIANCE_REGIME="FEDRAMP_HIGH"
            REGIME_DISPLAY="FedRAMP High"
            ;;
        2)
            COMPLIANCE_REGIME="IL4"
            REGIME_DISPLAY="IL4"
            ;;
        3)
            COMPLIANCE_REGIME="IL5"
            REGIME_DISPLAY="IL5"
            ;;
        4)
            echo -e "${RED}WARNING: Gemini for Government currently only supports deployment within FedRAMP High / IL4 Assured Workloads folders.${NC}"
            echo -e "${RED}Proceed at your own risk.${NC}"
            echo ""
            read -p "Press Enter to acknowledge and continue..."
            ;;
        *)
            echo -e "${RED}Invalid selection. Defaulting to FedRAMP High.${NC}"
            COMPLIANCE_REGIME="FEDRAMP_HIGH"
            REGIME_DISPLAY="FedRAMP High"
            ;;
    esac

    # Enable APIs based on compliance regime
    if [[ "$COMPLIANCE_REGIME" == "IL5" ]]; then
        echo ""
        echo -e "${YELLOW}WARNING: Discovery Engine API is not currently included in the Assured Workloads Service Usage Allowlist Org Policy for IL5.${NC}"
        echo -e "${YELLOW}Gemini for Government can only be used by creating an exception and adding discoveryengine.googleapis.com to the allowlist.${NC}"
        read -p "Do you want to attempt to enable Discovery Engine and Certificate Manager APIs? [y/N]: " ENABLE_APIS_NOW
        if [[ "$ENABLE_APIS_NOW" =~ ^[Yy]$ ]]; then
            echo "Attempting to enable APIs..."
            if ! gcloud services enable discoveryengine.googleapis.com certificatemanager.googleapis.com --project "${PROJECT_ID}"; then
                echo -e "${RED}Warning: Failed to enable Discovery Engine or Certificate Manager APIs.${NC}"
                echo -e "${YELLOW}This is expected if the APIs are not in your allowlist and you have not created an exception.${NC}"
            fi
        else
            echo -e "${YELLOW}Skipping API enablement. You may need to enable them manually after configuring exceptions.${NC}"
        fi
    else
        echo -e "${GREEN}Enabling Discovery Engine and Certificate Manager APIs automatically...${NC}"
        if ! gcloud services enable discoveryengine.googleapis.com certificatemanager.googleapis.com --project "${PROJECT_ID}"; then
            echo -e "${RED}Warning: Failed to enable Discovery Engine or Certificate Manager APIs.${NC}"
            echo -e "${YELLOW}Please ensure you have permissions to enable these APIs or they are allowed by your Org Policy.${NC}"
        fi
    fi

    if [[ -n "$COMPLIANCE_REGIME" ]]; then
        read -p "Is this project deployed in a ${REGIME_DISPLAY} Assured Workloads folder? (y/N): " IS_ASSURED
        if [[ "$IS_ASSURED" == "y" || "$IS_ASSURED" == "Y" ]]; then
            read -p "Enter the region (e.g., us-east4): " WORKLOAD_REGION
            if [[ -n "$WORKLOAD_REGION" ]]; then
                echo -n "Fetching ${REGIME_DISPLAY} Assured Workload folders in ${WORKLOAD_REGION}..."
                WORKLOAD_NAME=$(gcloud assured workloads list --location="${WORKLOAD_REGION}" --organization="${ORG_ID}" --filter="complianceRegime=${COMPLIANCE_REGIME}" --format="value(displayName)" 2>/dev/null | head -n 1 || true)
                
                if [[ -z "$WORKLOAD_NAME" ]]; then
                    echo -e "\n${RED}WARNING: Could not find ${REGIME_DISPLAY} Assured Workload folder in ${WORKLOAD_REGION}.${NC}"
                    echo -e "${YELLOW}Skipping automated Assured Workloads updates.${NC}"
                else
                    echo -e " [${GREEN}OK${NC}]"
                    echo -e "Found: ${GREEN}${WORKLOAD_NAME}${NC}"
                    echo ""
                    echo -e "${YELLOW}ACTION REQUIRED: Please update your Assured Workload environment manually.${NC}"
                    echo -e "1. Navigate to the following URL in your browser:"
                    echo -e "${BLUE}https://console.cloud.google.com/compliance/assuredworkloads?organizationId=${ORG_ID}${NC}"
                    echo -e "2. Click on the ${REGIME_DISPLAY} Assured Workload named: ${GREEN}${WORKLOAD_NAME}${NC}"
                    echo -e "3. Click on the button to ${GREEN}\"Review available updates\"${NC} and apply them."
                    echo ""
                    read -p "Press Enter to acknowledge and continue..."
                    echo -e "${GREEN}Assured Workload folder ${WORKLOAD_NAME} validated / updated${NC}"
                fi
            fi
        fi
    fi
    # 2. Access Transparency (Conditional on Compliance Regime)
    if [[ "$COMPLIANCE_REGIME" == "FEDRAMP_HIGH" || "$COMPLIANCE_REGIME" == "IL4" || "$COMPLIANCE_REGIME" == "IL5" ]]; then
        echo ""
        echo -e "${BLUE}--- Access Transparency ---${NC}"
        echo -e "${YELLOW}Access Transparency is highly recommended/required for this compliance regime.${NC}"
        echo -e "1. Navigate to the following URL in your browser:"
        echo -e "${BLUE}https://console.cloud.google.com/iam-admin/settings?organizationId=${ORG_ID}${NC}"
        echo -e "2. Under 'Access Transparency', ensure it is enabled."
        echo ""
        read -p "Press Enter to acknowledge and continue..."
    fi

    # 2. Shared VPC
    USE_SHARED_VPC="false"
    SHARED_VPC_HOST_PROJECT=""
    SHARED_VPC_NETWORK=""
    SHARED_VPC_SUBNET=""
    SHARED_VPC_PROXY_SUBNET=""
    echo ""
    echo -e "${BLUE}--- Networking ---${NC}"
    read -p "Do you want to use an existing Shared VPC? (y/N) [N]: " USE_SHARED_VPC_CHOICE
    if [[ "$USE_SHARED_VPC_CHOICE" == "y" || "$USE_SHARED_VPC_CHOICE" == "Y" ]]; then
        USE_SHARED_VPC="true"
        
        # 1. Determine Host Project & Verify Attachment
        SHARED_VPC_HOST_PROJECT=$(gcloud compute shared-vpc get-host-project "${PROJECT_ID}" --format="value(name)" 2>/dev/null || true)

        # If not attached, fail and advise user
        if [[ -z "$SHARED_VPC_HOST_PROJECT" ]]; then
            POTENTIAL_HOST_PROJECT=$(echo "$PROJECT_ID" | cut -d'-' -f1-2 | sed 's/$/-net-host/')
            
            echo -e "${RED}ERROR: Project '${PROJECT_ID}' is not attached to a Shared VPC Host.${NC}"
            echo -e "${YELLOW}To proceed, you must:${NC}"
            echo -e "1. Attach this project to the Shared VPC Host Project."
            echo -e "   (Command: gcloud compute shared-vpc associated-projects add ${PROJECT_ID} --host-project ${POTENTIAL_HOST_PROJECT})"
            echo -e "2. Share the VPC Host Project subnets with this Service Project."
            echo -e "${YELLOW}Please configure this and rerun deploy.sh.${NC}"
            return 1
        fi
        
        echo -e "Using Shared VPC: ${GREEN}Yes${NC}"
        echo -e "Using Network Host Project: ${YELLOW}${SHARED_VPC_HOST_PROJECT}${NC}"

        # 2. Auto-discover Network and Subnets
        if [[ -z "$SHARED_VPC_NETWORK" ]]; then
            echo "Scanning for subnets shared from ${SHARED_VPC_HOST_PROJECT} to ${PROJECT_ID}..."
            
            # Get all subnets from the Host Project directly in JSON format
            USABLE_SUBNETS_JSON=$(gcloud compute networks subnets list --project "${SHARED_VPC_HOST_PROJECT}" --format="json" 2>/dev/null)
            
            if [[ -z "$USABLE_SUBNETS_JSON" || "$USABLE_SUBNETS_JSON" == "[]" ]]; then
                 echo -e "${RED}ERROR: No subnets found in Host Project '${SHARED_VPC_HOST_PROJECT}' or permission denied.${NC}"
                 echo -e "${YELLOW}Please ensure that:${NC}"
                 echo -e "1. The Host Project exists and you have permissions to list subnets."
                 echo -e "2. You have shared the necessary subnets with this Service Project."
                 echo -e "3. You are authenticated correctly."
                 return 1
            fi

            # 1. Discover Private Subnet & Network (Atomic operation to ensure consistency)
            # We pick the first usable PRIVATE subnet in the Host Project AND in the correct Region (defaulting to us-east4 if not set)
            DISCOVERY_REGION=$(gcloud config get-value compute/region 2>/dev/null)
            DISCOVERY_REGION=${DISCOVERY_REGION:-"us-east4"}
            
            # We also normalize 'selfLink' to 'subnetwork' to handle both 'list-usable' and 'list' output formats
            FIRST_USABLE_SUBNET_JSON=$(echo "$USABLE_SUBNETS_JSON" | jq -r ".[] | .subnetwork = (.subnetwork // .selfLink) | select(.network | contains(\"projects/${SHARED_VPC_HOST_PROJECT}/\")) | select(.subnetwork | contains(\"/${DISCOVERY_REGION}/\")) | select(.purpose == \"PRIVATE\" or .purpose == null) | {network: .network, subnetwork: .subnetwork} | tojson" | head -n 1)
            
            if [[ -n "$FIRST_USABLE_SUBNET_JSON" ]]; then
                SHARED_VPC_NETWORK_URL=$(echo "$FIRST_USABLE_SUBNET_JSON" | jq -r .network)
                SHARED_VPC_NETWORK=$(basename "$SHARED_VPC_NETWORK_URL")
                
                SHARED_VPC_SUBNET_URL=$(echo "$FIRST_USABLE_SUBNET_JSON" | jq -r .subnetwork)
                SHARED_VPC_SUBNET=$(basename "$SHARED_VPC_SUBNET_URL")
                
                # Extract Region from Subnet URL to ensure consistency
                # URL format: .../regions/REGION/subnetworks/SUBNET
                REGION=$(echo "$SHARED_VPC_SUBNET_URL" | sed -E 's/.*\/regions\/([^\/]+)\/.*/\1/')
            fi

            # 2. Discover Proxy Subnet (purpose=REGIONAL_MANAGED_PROXY, in the SAME Network and Region)
            if [[ -n "$SHARED_VPC_NETWORK_URL" ]]; then
                SHARED_VPC_PROXY_SUBNET_URL=$(echo "$USABLE_SUBNETS_JSON" | jq -r ".[] | .subnetwork = (.subnetwork // .selfLink) | select(.network == \"$SHARED_VPC_NETWORK_URL\") | select(.subnetwork | contains(\"/${REGION}/\")) | select(.purpose == \"REGIONAL_MANAGED_PROXY\") | .subnetwork" | head -n 1)
                SHARED_VPC_PROXY_SUBNET=$(basename "$SHARED_VPC_PROXY_SUBNET_URL")
            fi
        fi

        # Fallbacks if discovery fails
        if [[ -z "$SHARED_VPC_NETWORK" ]]; then
            read -p "Enter Shared VPC Network Name: " INPUT_NETWORK
            SHARED_VPC_NETWORK=${INPUT_NETWORK}
        fi
        if [[ -z "$SHARED_VPC_SUBNET" ]]; then
            read -p "Enter Shared VPC Subnet Name: " INPUT_SUBNET
            SHARED_VPC_SUBNET=${INPUT_SUBNET}
        fi
        if [[ -z "$SHARED_VPC_PROXY_SUBNET" ]]; then
            read -p "Enter Shared VPC Proxy Subnet Name: " INPUT_PROXY_SUBNET
            SHARED_VPC_PROXY_SUBNET=${INPUT_PROXY_SUBNET}
        fi
        
        echo -e "Network: ${YELLOW}${SHARED_VPC_NETWORK}${NC}"
        echo -e "Subnet: ${YELLOW}${SHARED_VPC_SUBNET}${NC}"
        echo -e "Proxy Subnet: ${YELLOW}${SHARED_VPC_PROXY_SUBNET}${NC}"
    fi

    # 3. Region
    if [[ -z "$REGION" ]]; then
        echo ""
        echo -e "Select Network Region:"
        echo "1) us-central1"
        echo "2) us-central2"
        echo "3) us-east1"
        echo "4) us-east4 (Default)"
        echo "5) us-east5"
        echo "6) us-south1"
        echo "7) us-west1"
        echo "8) us-west2"
        echo "9) us-west3"
        echo "10) us-west4"
        read -p "Enter selection [4]: " REGION_SEL
        
        case $REGION_SEL in
            1) REGION="us-central1" ;;
            2) REGION="us-central2" ;;
            3) REGION="us-east1" ;;
            4|"") REGION="us-east4" ;;
            5) REGION="us-east5" ;;
            6) REGION="us-south1" ;;
            7) REGION="us-west1" ;;
            8) REGION="us-west2" ;;
            9) REGION="us-west3" ;;
            10) REGION="us-west4" ;;
            *)
                echo -e "${YELLOW}Invalid selection. Defaulting to us-east4.${NC}"
                REGION="us-east4"
                ;;
        esac
    fi
    echo -e "Using Network Region: ${YELLOW}${REGION}${NC}"

    # 4. Load Balancer Type
    echo ""
    echo -e "Select Load Balancer Type:"
    echo "1) Regional External (Internet facing)"
    echo "2) Regional Internal (VPN / Interconnect)"
    echo "3) None (Gemini Enterprise App Only)"
    read -p "Enter selection [1]: " LB_SEL
    
    CERT_MANAGEMENT_CHOICE="self_managed"
    CUSTOM_DOMAIN=""

    if [[ "$LB_SEL" == "3" ]]; then
        DEPLOYMENT_TYPE="none"
    elif [[ "$LB_SEL" == "2" ]]; then
        DEPLOYMENT_TYPE="internal"
    else
        DEPLOYMENT_TYPE="external"
        
        if [[ "$COMPLIANCE_REGIME" != "IL4" && "$COMPLIANCE_REGIME" != "IL5" ]]; then
            echo ""
            echo -e "Select Certificate Management:"
            echo "1) Regional Google-managed SSL Certificate"
            echo "   - Benefits: Automatically provisions and renews SSL certificate, less operational overhead"
            echo "2) Regional Self-Managed Certificate (Default)"
            echo "   - Benefits: Full control over certificate lifecycle, allows use of custom/existing CA"
            read -p "Enter selection [2]: " CERT_SEL
            
            if [[ "$CERT_SEL" == "1" ]]; then
                CERT_MANAGEMENT_CHOICE="google_managed"
                read -p "Enter Gemini Enterprise FQDN for the Certificate (e.g., gemini.example.com): " CUSTOM_DOMAIN
                # Pre-set DOMAIN if empty to match CUSTOM_DOMAIN base
                if [[ -z "$DOMAIN" ]]; then
                    DOMAIN=$(echo "$CUSTOM_DOMAIN" | awk -F. '{print $(NF-1)"."$NF}')
                fi
            fi
        else
            echo -e "${GREEN}${COMPLIANCE_REGIME} Regime active. Automatically enforcing Self-Managed Certificate.${NC}"
        fi
    fi

    # 5. Domain
    if [[ -z "$DOMAIN" ]]; then
        ORG_DOMAIN=$(gcloud organizations list --filter="name:organizations/${ORG_ID}" --format="value(displayName)" 2>/dev/null)
        DOMAIN=${ORG_DOMAIN}
    fi

    if [[ -z "$DOMAIN" ]]; then
        read -p "Enter Domain (e.g., example.com): " DOMAIN
    else
        echo -e "Using Domain: ${YELLOW}${DOMAIN}${NC}"
    fi

    # 6. Identity Provider
    echo ""
    echo -e "${BLUE}--- Identity and Access ---${NC}"
    echo "Select Gemini Enterprise Identity Provider:"
    echo "----------------------------------------------------------------"
    echo "1) GOOGLE CLOUD IDENTITY (Default)"
    echo "   - Best for users with Google Workspace accounts."
    echo "   - Uses standard Google Groups (e.g., gcp-gemini-enterprise-admins@${DOMAIN})."
    echo "   - Simple setup, requires Cloud Identity or Google Workspace."
    echo ""
    echo "2) THIRD_PARTY (Workforce Identity Federation)"
    echo "   - Best for external identity providers (Okta, Azure AD, etc.)."
    echo "   - Syncless: No need to sync users to Google Cloud."
    echo "   - Uses Attribute-Based Access Control (ABAC)."
    echo "   - Requires a configured Workforce Identity Pool."
    echo "----------------------------------------------------------------"
    read -p "Enter selection [1]: " ACL_SELECTION
    
    ACL_IDP_TYPE="GOOGLE_CLOUD_IDENTITY"
    ACL_POOL_NAME=""
    ACL_PROVIDER_ID=""
    
    if [[ "$ACL_SELECTION" == "2" ]]; then
        ACL_IDP_TYPE="THIRD_PARTY"
        
        # Auto-discover Workforce Pools
        echo ""
        echo "Discovering Workforce Identity Pools..."
        POOLS_JSON=$(gcloud iam workforce-pools list --organization="${ORG_ID}" --location="global" --format="json" 2>/dev/null)
        
        if [[ -n "$POOLS_JSON" && "$POOLS_JSON" != "[]" ]]; then
            echo ""
            echo "Available Workforce Pools:"
            echo "$POOLS_JSON" | jq -r '.[] | "\(.name) (\(.displayName))"' | nl -w2 -s") "
            
            read -p "Select a Workforce Pool [1]: " POOL_SEL
            POOL_SEL=${POOL_SEL:-1}
            
            # Extract selected pool name (full resource name)
            ACL_POOL_NAME=$(echo "$POOLS_JSON" | jq -r ".[$((POOL_SEL-1))].name")
        fi
        
        if [[ -z "$ACL_POOL_NAME" ]]; then
            echo -e "${YELLOW}No pools found or invalid selection. Switching to manual entry.${NC}"
            read -p "Enter Workforce Pool ID: " ACL_POOL_ID
            ACL_POOL_NAME="locations/global/workforcePools/${ACL_POOL_ID}"
        else
            echo -e "Selected Pool: ${YELLOW}${ACL_POOL_NAME}${NC}"
        fi
        
        # Auto-discover Providers
        echo ""
        echo "Discovering Providers in ${ACL_POOL_NAME}..."
        PROVIDERS_JSON=$(gcloud iam workforce-pools providers list --workforce-pool="${ACL_POOL_NAME}" --location="global" --format="json" 2>/dev/null)
        
        if [[ -n "$PROVIDERS_JSON" && "$PROVIDERS_JSON" != "[]" ]]; then
            echo "Available Providers:"
            echo "$PROVIDERS_JSON" | jq -r '.[] | "\(.name) (\(.displayName))"' | nl -w2 -s") "
            
            read -p "Select a Provider [1]: " PROV_SEL
            PROV_SEL=${PROV_SEL:-1}
            
            # Extract selected provider ID (last part of name)
            FULL_PROV_NAME=$(echo "$PROVIDERS_JSON" | jq -r ".[$((PROV_SEL-1))].name")
            ACL_PROVIDER_ID=$(basename "$FULL_PROV_NAME")
        fi
        
        if [[ -z "$ACL_PROVIDER_ID" ]]; then
            echo -e "${YELLOW}No providers found or invalid selection. Switching to manual entry.${NC}"
            read -p "Enter Workforce Provider ID: " ACL_PROVIDER_ID
        else
            echo -e "Selected Provider: ${YELLOW}${ACL_PROVIDER_ID}${NC}"
        fi
        
        # Extract Pool ID for display/verification if needed (though we have full name now)
        ACL_POOL_ID=$(basename "$ACL_POOL_NAME")
        
        echo ""
        echo -e "${YELLOW}ACTION REQUIRED: Please verify the attribute mapping for your provider.${NC}"
        echo -e "1. Navigate to the Workforce Identity Pools page:"
        echo -e "${BLUE}https://console.cloud.google.com/iam-admin/workforce-identity-pools?orgonly=true&organizationId=${ORG_ID}&supportedpurview=organizationId${NC}"
        echo -e "2. Select the pool: ${GREEN}${ACL_POOL_ID}${NC}"
        echo -e "3. Go to the ${GREEN}Providers${NC} tab and select your provider: ${GREEN}${ACL_PROVIDER_ID}${NC}"
        echo -e "4. Click ${GREEN}EDIT${NC} and go to the ${GREEN}Attribute Mapping${NC} section."
        echo -e "5. Ensure that the attribute ${YELLOW}google.email${NC} is mapped from your identity provider's email attribute."
        echo -e "   (Example mapping: ${YELLOW}assertion.email${NC} or ${YELLOW}assertion.sub${NC})"
        echo ""
        read -p "Press Enter to acknowledge and continue..."
    fi

    # 7. Groups
    if [[ "$ACL_IDP_TYPE" == "GOOGLE_CLOUD_IDENTITY" ]]; then
        DEFAULT_ADMIN="gcp-gemini-enterprise-admins@${DOMAIN}"
        DEFAULT_USER="gcp-gemini-enterprise-users@${DOMAIN}"
        read -p "Enter Admin Group [${DEFAULT_ADMIN}]: " ADMIN_GROUP
        ADMIN_GROUP=${ADMIN_GROUP:-$DEFAULT_ADMIN}
        read -p "Enter User Group [${DEFAULT_USER}]: " USER_GROUP
        USER_GROUP=${USER_GROUP:-$DEFAULT_USER}
        
        # Add group: prefix
        [[ "$ADMIN_GROUP" != *":"* ]] && ADMIN_GROUP="group:${ADMIN_GROUP}"
        [[ "$USER_GROUP" != *":"* ]] && USER_GROUP="group:${USER_GROUP}"

        # Validate Groups
        echo "Validating group existence and directory access..."
        ADMIN_EMAIL="${ADMIN_GROUP#group:}"
        USER_EMAIL="${USER_GROUP#group:}"
        
        if ! gcloud --quiet identity groups describe "$ADMIN_EMAIL" &>/dev/null; then
            echo -e "${RED}WARNING: Cannot access or find Admin Group: ${ADMIN_EMAIL}${NC}"
            echo -e "${YELLOW}Ensure the group exists and your account has directory read access.${NC}"
        else
            echo -e "${GREEN}Validated Admin Group access.${NC}"
        fi
        
        if ! gcloud --quiet identity groups describe "$USER_EMAIL" &>/dev/null; then
            echo -e "${RED}WARNING: Cannot access or find User Group: ${USER_EMAIL}${NC}"
            echo -e "${YELLOW}Ensure the group exists and your account has directory read access.${NC}"
        else
            echo -e "${GREEN}Validated User Group access.${NC}"
        fi
    else
        echo ""
        echo -e "${YELLOW}For Workforce Identity, please enter the full Principal / Principal Set.${NC}"
        echo "This allows you to map groups, users, or attributes from your IdP to IAM roles."
        echo ""
        echo "Examples:"
        echo " - Single user in a workforce identity pool:"
        echo -e "   principal://iam.googleapis.com/${ACL_POOL_NAME}/subject/${YELLOW}SUBJECT_ATTRIBUTE_VALUE${NC}"
        echo ""
        echo " - All users in a workforce identity pool group:"
        echo -e "   principalSet://iam.googleapis.com/${ACL_POOL_NAME}/group/${YELLOW}GROUP_ID${NC}"
        echo ""
        echo " - All users with a specific attribute (e.g., department=engineering):"
        echo -e "   principalSet://iam.googleapis.com/${ACL_POOL_NAME}/${YELLOW}attribute.department${NC}/${YELLOW}engineering${NC}"
        echo ""
        echo " - All users in the pool (Use with caution):"
        echo -e "   principalSet://iam.googleapis.com/${ACL_POOL_NAME}/${YELLOW}*${NC}"
        echo ""
        
        read -p "Enter Admin Principal/Principal Set: " ADMIN_GROUP
        read -p "Enter User Principal/Principal Set: " USER_GROUP
    fi
    # 8. Implicit Model Data Caching
    echo ""
    echo -e "${BLUE}--- Vertex AI Configuration ---${NC}"
    echo "Disabling Implicit Model Data Caching for project: ${PROJECT_ID}..."
    local ACCESS_TOKEN
    if ACCESS_TOKEN=$(gcloud auth print-access-token 2>/dev/null); then
        local CACHE_CONFIG_URL="https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/cacheConfig"
        local CACHE_PAYLOAD=$(jq -n --arg pid "$PROJECT_ID" '{name: "projects/\($pid)/cacheConfig", disableCache: true}')
        
        local CACHE_RESPONSE
        CACHE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "${CACHE_PAYLOAD}" \
            "${CACHE_CONFIG_URL}")
            
        local CACHE_HTTP_CODE=$(echo "$CACHE_RESPONSE" | tail -n 1)
        if [[ "$CACHE_HTTP_CODE" == "200" || "$CACHE_HTTP_CODE" == "204" ]]; then
            echo -e "${GREEN}Successfully disabled Implicit Model Data Caching.${NC}"
        else
            echo -e "${YELLOW}Failed to disable Implicit Model Data Caching (HTTP ${CACHE_HTTP_CODE}). Please verify Vertex AI permissions.${NC}"
        fi
    else
        echo -e "${RED}WARNING: Could not get gcloud access token. Skipping caching check.${NC}"
    fi

    # 9. Access Policy
    echo ""
    echo -e "${BLUE}--- Access Policies ---${NC}"
    echo "Discovering Access Policy..."
    ACCESS_POLICY_NUMBER=$(gcloud access-context-manager policies list --organization "${ORG_ID}" --format="value(name)" --quiet 2>/dev/null | head -n 1)
    if [ -z "$ACCESS_POLICY_NUMBER" ]; then
        echo -e "${RED}WARNING: Could not auto-discover Access Policy Number.${NC}"
        read -p "Enter Access Policy Number: " ACCESS_POLICY_NUMBER
    else
        ACCESS_POLICY_NUMBER=$(basename "${ACCESS_POLICY_NUMBER}")
        echo -e "Found Access Policy Number: ${YELLOW}${ACCESS_POLICY_NUMBER}${NC}"
    fi

    if [[ -z "$ACCESS_POLICY_NUMBER" ]]; then
        echo -e "${RED}Error: Access Policy Number is required.${NC}"
        return 1
    fi
    
    # Pre-check Terraform State for managed Access Levels
    # This requires determining BUCKET_NAME and running terraform init early
    echo "Checking Terraform State for managed resources..."
    cd gemini-stage-0
    
    # Resolve Bucket Name Logic (Duplicates logic from deploy_stage_0/configure_stage_0 reuse block)
    # If using existing tfvars, use it. If not, use derived STATE_BUCKET.
    TEMP_BUCKET_NAME="${BUCKET_NAME}"
    if [[ -z "$TEMP_BUCKET_NAME" ]]; then
         if [[ -f "terraform.tfvars" ]]; then
             TEMP_BUCKET_NAME=$(grep 'terraform_state_bucket' terraform.tfvars | cut -d'=' -f2 | tr -d ' "')
             TEMP_BUCKET_NAME=$(echo "$TEMP_BUCKET_NAME" | sed 's/gs:\/\/ //' | sed 's/\/$//')
         fi
    fi
    # If still empty, fall back to global STATE_BUCKET
    if [[ -z "$TEMP_BUCKET_NAME" && -n "$STATE_BUCKET" ]]; then
        TEMP_BUCKET_NAME=$(echo "$STATE_BUCKET" | sed 's/gs:\/\/ //' | sed 's/\/$//')
    fi
    
    MANAGED_ACCESS_LEVELS=""
    if [[ -n "$TEMP_BUCKET_NAME" ]]; then
        echo "Initializing Terraform (Read-Only) to check state in ${TEMP_BUCKET_NAME}..."
        # We suppress output to keep UI clean, but allow errors to show if critical
        if terraform init -migrate-state -backend-config="bucket=${TEMP_BUCKET_NAME}" -backend-config="prefix=terraform/state/stage-0" &>/dev/null; then
             MANAGED_ACCESS_LEVELS=$(terraform state list | grep "google_access_context_manager_access_level" || true)
             if [[ -n "$MANAGED_ACCESS_LEVELS" ]]; then
                 echo -e "${GREEN}Found managed Access Levels in state.${NC}"
             fi
        else
             echo -e "${RED}WARNING: Could not initialize Terraform state check. Proceeding as fresh deployment.${NC}"
        fi
    else
        echo "State bucket not determined. Skipping managed resource check."
    fi
    cd ..

    configure_access_policies

    # Cloud Armor WAF Information
    echo ""
    echo -e "${BLUE}--- Cloud Armor (WAF) ---${NC}"
    echo -e "${YELLOW}Cloud Armor will act as a Web Application Firewall (WAF) for your Gemini Enterprise application.${NC}"
    echo -e "It will be deployed with predefined rules and sensitivity levels."
    echo ""
    echo -e "Please review the configuration in: ${BLUE}blueprints/fedramp-high/gemini-enterprise/gemini-stage-0/data/cloudarmor.yaml${NC}"
    echo -e "For more information on predefined WAF rules, visit: ${BLUE}https://docs.cloud.google.com/armor/docs/waf-rules${NC}"
    echo ""
    read -p "Press Enter to acknowledge and continue..."

    # 9. Data Stores
    echo ""
    echo -e "${BLUE}--- Data Stores (Cloud Storage / BigQuery) ---${NC}"
    echo -e "${YELLOW}--- NOTE: Data Stores can be created and associated with a Gemini Enterprise application at a later time. ---${NC}"
    read -p "Create Data Stores? (y/N): " DS_CHOICE
    CREATE_DS_BOOL="false"
    ENABLE_DS_CMEK="true" # Default to true even if not creating, though irrelevant
    GCS_DATA_STORES="{}"
    BQ_DATA_STORES="{}"
    
    if [[ "$DS_CHOICE" == "y" || "$DS_CHOICE" == "Y" ]]; then
        CREATE_DS_BOOL="true"
        
        # Ask for CMEK preference for Data Stores
        ENABLE_DS_CMEK="true"
        if [[ "$COMPLIANCE_REGIME" == "IL4" || "$COMPLIANCE_REGIME" == "IL5" ]]; then
            echo -e "${GREEN}${COMPLIANCE_REGIME} Regime active. Automatically enforcing CMEK for Data Stores.${NC}"
        else
            read -p "Encrypt these Data Stores with Customer Managed Encryption Keys (CMEK)? (Y/n): " CMEK_CHOICE
            if [[ "$CMEK_CHOICE" == "n" || "$CMEK_CHOICE" == "N" ]]; then
                 ENABLE_DS_CMEK="false"
                 echo -e "${YELLOW}Data Stores will use Google-managed encryption keys.${NC}"
            else
                 echo -e "${GREEN}Data Stores will use CMEK.${NC}"
            fi
        fi

        if [[ "$ENABLE_DS_CMEK" == "true" ]]; then
            echo -e "${YELLOW}CMEK for Data Stores requested. Ensuring key exists...${NC}"
            
            # We need standard variables. discover_infrastructure should have set them.
            if [[ -z "$CAP_ENV" && -n "$ENVIRONMENT" ]]; then
                CAP_ENV=$(echo "$ENVIRONMENT" | awk '{print toupper(substr($0,1,1)) substr($0,2)}')
            fi
            CAP_ENV=${CAP_ENV:-"Prod"}
            TENANT=${TENANT:-"g4g"}
            
            _KEYRING_NAME="${CAP_ENV}-${TENANT}-keyring"
            _KEY_NAME="gemini-enterprise"
            _LOCATION="us"
            
            # Identify Target Project
            _TARGET_KMS_PROJECT="${CMEK_PROJECT_ID}"
            if [[ -z "$_TARGET_KMS_PROJECT" ]]; then
                _TARGET_KMS_PROJECT="${TENANT_IAC_PROJECT}"
            fi
            if [[ -z "$_TARGET_KMS_PROJECT" ]]; then
                _TARGET_KMS_PROJECT="${PROJECT_ID}"
            fi
            
            _CMEK_US_KEYRING="projects/${_TARGET_KMS_PROJECT}/locations/${_LOCATION}/keyRings/${_KEYRING_NAME}"
            _FULL_KEY_NAME="${_CMEK_US_KEYRING}/cryptoKeys/${_KEY_NAME}"
            
            if [[ -z "$CMEK_US_RESOURCES_KEY" ]]; then
                echo -e "Target Project: ${YELLOW}${_TARGET_KMS_PROJECT}${NC}"
                echo -e "Keyring: ${YELLOW}${_KEYRING_NAME}${NC}"
                
                if ! gcloud kms keys describe "${_FULL_KEY_NAME}" &>/dev/null; then
                     echo "Creating Key '${_KEY_NAME}'..."
                     gcloud kms keys create "${_KEY_NAME}" \
                         --keyring="${_KEYRING_NAME}" \
                         --location="${_LOCATION}" \
                         --project="${_TARGET_KMS_PROJECT}" \
                         --purpose="encryption" \
                         --protection-level="hsm" \
                         --rotation-period="7776000s" \
                         --next-rotation-time="$(date -v+90d -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '+90 days' +%Y-%m-%dT%H:%M:%SZ)"
                else
                     echo "Key '${_KEY_NAME}' already exists."
                fi
                CMEK_US_RESOURCES_KEY="${_FULL_KEY_NAME}"
            else
                echo -e "Using Existing CMEK Gemini Key: ${GREEN}${CMEK_US_RESOURCES_KEY}${NC}"
            fi
            
            # Register the key BEFORE Terraform
            echo -e "${YELLOW}Registering CMEK key for Gemini Enterprise in the US multi-region...${NC}"
            
            # --- Prerequisite: Grant IAM permissions to Discovery Engine service account ---
            echo "Checking if Discovery Engine service account has access to the key..."
            _PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)" 2>/dev/null)
            if [[ -n "$_PROJECT_NUMBER" ]]; then
                _SERVICES_SA="service-${_PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
                echo "Granting roles/cloudkms.cryptoKeyEncrypterDecrypter to ${_SERVICES_SA} on key ${_KEY_NAME}..."
                if ! gcloud kms keys add-iam-policy-binding "${_KEY_NAME}" \
                    --location="${_LOCATION}" \
                    --keyring="${_KEYRING_NAME}" \
                    --project="${_TARGET_KMS_PROJECT}" \
                    --member="serviceAccount:${_SERVICES_SA}" \
                    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter" 2>/dev/null; then
                    echo -e "${RED}WARNING: Failed to grant IAM binding to Discovery Engine service account.${NC}"
                    echo -e "${YELLOW}You might need 'roles/cloudkms.admin' on the key project.${NC}"
                fi
            else
                echo -e "${RED}WARNING: Could not determine project number. Skipping IAM grant for Discovery Engine.${NC}"
            fi
            
            _ACCESS_TOKEN=$(gcloud auth print-access-token)
        
            # --- Check if already registered ---
            echo "Checking if CMEK key is already registered..."
            _CONFIG_RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer ${_ACCESS_TOKEN}" \
                -H "x-goog-user-project: ${PROJECT_ID}" \
                "https://us-discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}/locations/us/cmekConfigs/default_cmek_config")
                
            _OP_HTTP_CODE=$(echo "$_CONFIG_RESPONSE" | tail -n1)
            _OP_BODY=$(echo "$_CONFIG_RESPONSE" | sed '$d')
            
            _CURRENT_KEY=$(echo "$_OP_BODY" | jq -r .kmsKey 2>/dev/null || echo "")
            
            _PROCEED_WITH_PATCH=true
            
            if [[ "$_OP_HTTP_CODE" -eq 200 ]]; then
                if [[ "$_CURRENT_KEY" == "${CMEK_US_RESOURCES_KEY}" ]]; then
                    echo -e "${GREEN}CMEK key is already registered and matches.${NC}"
                    _PROCEED_WITH_PATCH=false
                else
                    echo -e "${YELLOW}CMEK key is already registered with a different key: ${_CURRENT_KEY}${NC}"
                    echo -e "${YELLOW}Adopting the already registered key for infrastructure alignment.${NC}"
                    CMEK_US_RESOURCES_KEY="$_CURRENT_KEY"
                    _PROCEED_WITH_PATCH=false
                fi
            else
                echo "CMEK config not found or error. Proceeding with registration..."
            fi
            
            if [[ "$_PROCEED_WITH_PATCH" == "true" ]]; then
                echo "Sending registration request..."
                _API_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH \
                    -H "Authorization: Bearer ${_ACCESS_TOKEN}" \
                    -H "Content-Type: application/json" \
                    -H "x-goog-user-project: ${PROJECT_ID}" \
                    "https://us-discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}/locations/us/cmekConfigs/default_cmek_config?set_default=true" \
                    -d "{\"kmsKey\": \"${CMEK_US_RESOURCES_KEY}\"}")
                    
                _PATCH_HTTP_CODE=$(echo "$_API_RESPONSE" | tail -n1)
                _PATCH_BODY=$(echo "$_API_RESPONSE" | sed '$d')
                
                if [[ "$_PATCH_HTTP_CODE" -eq 200 || "$_PATCH_HTTP_CODE" -eq 409 ]]; then
                    echo -e "${GREEN}Successfully initiated CMEK key registration.${NC}"
                    
                    # --- Polling for Long Running Operation (LRO) ---
                    _OPERATION_ID=$(echo "$_PATCH_BODY" | jq -r .name 2>/dev/null || echo "")
                    if [[ -n "$_OPERATION_ID" && "$_OPERATION_ID" != "null" ]]; then
                        echo -e "${YELLOW}Long Running Operation ID: ${_OPERATION_ID}${NC}"
                        echo -e "${YELLOW}Polling for completion (this may take a few minutes)...${NC}"
                        
                        while true; do
                            _OP_RESPONSE=$(curl -s -H "Authorization: Bearer ${_ACCESS_TOKEN}" \
                                -H "x-goog-user-project: ${PROJECT_ID}" \
                                "https://us-discoveryengine.googleapis.com/v1/${_OPERATION_ID}")
                            
                            _IS_DONE=$(echo "$_OP_RESPONSE" | jq -r .done 2>/dev/null || echo "false")
                            _HAS_ERROR=$(echo "$_OP_RESPONSE" | jq -r .error 2>/dev/null || echo "")
                            
                            if [[ "$_IS_DONE" == "true" ]]; then
                                if [[ -n "$_HAS_ERROR" && "$_HAS_ERROR" != "null" ]]; then
                                    echo -e "${RED}CMEK registration failed in operation.${NC}"
                                    echo -e "Error: $_HAS_ERROR"
                                    break
                                fi
                                echo -e "\n${GREEN}CMEK registration completed successfully.${NC}"
                                break
                            fi
                            
                            echo -n "."
                            sleep 10
                        done
                        echo ""
                    else
                        echo -e "${RED}Warning: Could not extract operation name from response.${NC}"
                        echo -e "Response: $_PATCH_BODY"
                    fi
                else
                    echo -e "${RED}Failed to register CMEK key. HTTP Status: ${_PATCH_HTTP_CODE}${NC}"
                    echo -e "Response: $_PATCH_BODY"
                    echo -e "You may need to manually register the key."
                fi
            fi
        fi
        GCS_LIST=()
        BQ_LIST=()
        
        configure_data_stores
        
        if [[ ${#GCS_LIST[@]} -gt 0 ]]; then
            GCS_DATA_STORES="{ $(IFS=,; echo "${GCS_LIST[*]}") }"
        fi
        if [[ ${#BQ_LIST[@]} -gt 0 ]]; then
            BQ_DATA_STORES="{ $(IFS=,; echo "${BQ_LIST[*]}") }"
        fi
    fi

    # 10. Analytics (Discovery Engine Audit Logs)
    echo ""
    echo -e "${BLUE}--- Analytics (Discovery Engine Audit Logs) ---${NC}"
    read -p "Would you like to enable analytics for Gemini Enterprise (via Discovery Engine Audit Logs)? [y/N]: " ENABLE_ANALYTICS
    if [[ "$ENABLE_ANALYTICS" =~ ^[Yy]$ ]]; then
        ENABLE_ANALYTICS_FLAG="true"
    else
        ENABLE_ANALYTICS_FLAG="false"
    fi

    # 11. Organization Policy Check
    echo ""
    echo -e "${BLUE}--- Organization Policies (Project-Level) ---${NC}"
    check_org_policies
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    echo ""
    echo -e "${BLUE}--- Manual Steps ---${NC}"
    echo -e "${YELLOW}IMPORTANT: Before proceeding, ensure you have completed the following manual prerequisites:${NC}"
    echo "1. OAuth Consent Screen: Configured as Internal."
    echo -e "   Link: ${BLUE}https://console.cloud.google.com/auth/branding?orgonly=true&project=${PROJECT_ID}&supportedpurview=organizationId${NC}"
    echo "2. User Role Groups: Created admin/user groups in Cloud Identity / third-party identity provider (${ADMIN_GROUP}, ${USER_GROUP})."
    echo ""
    read -p "Have you completed these steps? (y/N): " CONFIRM_PRE
    if [[ "$CONFIRM_PRE" != "y" && "$CONFIRM_PRE" != "Y" ]]; then
        echo "Please complete the prerequisites and try again."
        return 1
    fi

    # Greenfield: Create KeyRing and Key if needed
    if [[ "$IS_BROWNFIELD" == "false" && "$IS_CUSTOM" == "false" && -z "$KMS_KEY_ID" ]]; then
        echo "Greenfield Deployment: Checking/Creating KMS KeyRing and Key..."
        KEYRING_NAME="gemini-enterprise-keyring"
        KEY_NAME="state-key"
        KEYRING_LOCATION="us"

        # Check/Create KeyRing
        if ! gcloud kms keyrings describe "$KEYRING_NAME" --location="$KEYRING_LOCATION" --project="$PROJECT_ID" &>/dev/null; then
            echo "Creating KeyRing ${KEYRING_NAME} in ${KEYRING_LOCATION}..."
            gcloud kms keyrings create "$KEYRING_NAME" --location="$KEYRING_LOCATION" --project="$PROJECT_ID"
        else
            echo "KeyRing ${KEYRING_NAME} already exists."
        fi

        # Check/Create Key
        if ! gcloud kms keys describe "$KEY_NAME" --keyring="$KEYRING_NAME" --location="$KEYRING_LOCATION" --project="$PROJECT_ID" &>/dev/null; then
            echo "Creating Key ${KEY_NAME} (HSM, 90-day rotation)..."
            # Calculate next rotation time (90 days from now) using Python for portability
            NEXT_ROTATION_TIME=$(python3 -c 'import datetime; print((datetime.datetime.utcnow() + datetime.timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ"))')
            
            gcloud kms keys create "$KEY_NAME" \
                --keyring="$KEYRING_NAME" \
                --location="$KEYRING_LOCATION" \
                --purpose="encryption" \
                --protection-level="hsm" \
                --rotation-period="7776000s" \
                --next-rotation-time="$NEXT_ROTATION_TIME" \
                --project="$PROJECT_ID"
        else
            echo "Key ${KEY_NAME} already exists."
        fi
        
        KMS_KEY_ID="projects/${PROJECT_ID}/locations/${KEYRING_LOCATION}/keyRings/${KEYRING_NAME}/cryptoKeys/${KEY_NAME}"
        echo -e "Using KMS Key: ${YELLOW}${KMS_KEY_ID}${NC}"
    fi

    # Initialize Terraform early to check state
    echo ""
    echo -e "${BLUE}--- Existing Terraform State Check ---${NC}"
    cd gemini-stage-0
    # Ensure BUCKET_NAME is set for backend init
    if [[ -z "$BUCKET_NAME" && -n "$STATE_BUCKET" ]]; then
        BUCKET_NAME=$(echo "$STATE_BUCKET" | sed 's/gs:\/\/ //' | sed 's/\/$//')
    fi
    rm -rf .terraform
    terraform init -migrate-state -backend-config="bucket=${BUCKET_NAME}" -backend-config="prefix=terraform/state/stage-0" || echo -e "${RED}WARNING: Init failed during state check.${NC}"

    # Check if KeyRing is in state
    if terraform state list | grep -q "google_kms_key_ring.created"; then
        echo -e "${YELLOW}CMEK Keyring found in Terraform State. Removing it from Terraform management...${NC}"
        terraform state rm google_kms_key_ring.created || true
    fi

    # Check if Key is in state
    if terraform state list | grep -q "google_kms_crypto_key.gemini_enterprise"; then
        echo -e "${YELLOW}gemini-enterprise Crypto Key found in Terraform State. Removing it from Terraform management...${NC}"
        terraform state rm google_kms_crypto_key.gemini_enterprise || true
    fi
    cd ..

    # Generate terraform.tfvars
    cat > gemini-stage-0/terraform.tfvars <<EOF
main_project_id             = "${PROJECT_ID}"
environment                 = "${ENVIRONMENT}"
tenant                      = "${TENANT}"
compliance_regime           = "${COMPLIANCE_REGIME:-NONE}"
kms_project_id              = "${CMEK_PROJECT_ID}"
us_keyring_name             = "${CMEK_US_KEYRING}"
kms_key_id                  = "${CMEK_US_RESOURCES_KEY}"
terraform_state_bucket      = "${BUCKET_NAME}"
region                      = "${REGION}"
domain                      = "${DOMAIN}"
prefix                      = "${PREFIX}"
deployment_type             = "${DEPLOYMENT_TYPE}"
cert_management_choice      = "${CERT_MANAGEMENT_CHOICE:-self_managed}"
custom_domain               = "${CUSTOM_DOMAIN:-}"
access_policy_number        = ${ACCESS_POLICY_NUMBER}
admin_group                 = "${ADMIN_GROUP}"
user_groups                 = ["${USER_GROUP}"]
acl_idp_type                = "${ACL_IDP_TYPE}"
acl_workforce_pool_name     = "${ACL_POOL_NAME}"
acl_workforce_provider_id   = "${ACL_PROVIDER_ID}"
use_shared_vpc              = ${USE_SHARED_VPC}
network_project_id          = "${SHARED_VPC_HOST_PROJECT}"
shared_vpc_network_name     = "${SHARED_VPC_NETWORK}"
shared_vpc_subnet_name      = "${SHARED_VPC_SUBNET}"
shared_vpc_proxy_subnet_name = "${SHARED_VPC_PROXY_SUBNET}"
create_data_stores          = ${CREATE_DS_BOOL}
enable_analytics            = ${ENABLE_ANALYTICS_FLAG}
EOF

    
    # Add example data stores
    if [[ "$CREATE_DS_BOOL" == "true" ]]; then
        cat >> gemini-stage-0/terraform.tfvars <<EOF
enable_data_store_cmek = ${ENABLE_DS_CMEK}
gcs_data_store_configs = ${GCS_DATA_STORES}
bq_data_store_configs = ${BQ_DATA_STORES}
EOF
    fi

    # Construct Access Level Lists
    LENIENT_LIST=()
    MODERATE_LIST=()
    
    PREFIX_PATH="accessPolicies/${ACCESS_POLICY_NUMBER}/accessLevels"
    
    if [[ "$CREATE_US_ACCESS" == "true" ]]; then
        LENIENT_LIST+=("\"${PREFIX_PATH}/us\"")
        MODERATE_LIST+=("\"${PREFIX_PATH}/us\"")
    fi
    
    if [[ "$CREATE_IP_BASED_ACCESS" == "true" ]]; then
         LENIENT_LIST+=("\"${PREFIX_PATH}/ip_based_access\"")
         MODERATE_LIST+=("\"${PREFIX_PATH}/ip_based_access\"")
    fi
    
    if [[ "$CREATE_TIME_ACCESS" == "true" ]]; then
        MODERATE_LIST+=("\"${PREFIX_PATH}/time\"")
    fi
    
    if [[ "$CREATE_EXPIRE_ACCESS" == "true" ]]; then
        MODERATE_LIST+=("\"${PREFIX_PATH}/expire\"")
    fi
    
    LENIENT_STR="[$(IFS=,; echo "${LENIENT_LIST[*]}")]"
    MODERATE_STR="[$(IFS=,; echo "${MODERATE_LIST[*]}")]"

    # Add Access Policy Creation Flags
    cat >> gemini-stage-0/terraform.tfvars <<EOF
create_ip_based_access          = ${CREATE_IP_BASED_ACCESS}
create_us_access                = ${CREATE_US_ACCESS}
create_time_access              = ${CREATE_TIME_ACCESS}
create_expire_access            = ${CREATE_EXPIRE_ACCESS}
create_lenient_device_access    = ${CREATE_LENIENT_DEVICE_ACCESS}
create_moderate_device_access   = ${CREATE_MODERATE_DEVICE_ACCESS}
create_strict_device_access     = ${CREATE_STRICT_DEVICE_ACCESS}
enable_chrome_enterprise_premium = ${ENABLE_CEP_BOOL}
lenient_device_access_levels    = ${LENIENT_STR}
moderate_device_access_levels   = ${MODERATE_STR}
EOF
    
    # Add Time variables if set
    if [[ -n "$ACCESS_START_DAY" ]]; then
         echo "access_start_day = ${ACCESS_START_DAY}" >> gemini-stage-0/terraform.tfvars
    fi
    if [[ -n "$ACCESS_END_DAY" ]]; then
         echo "access_end_day = ${ACCESS_END_DAY}" >> gemini-stage-0/terraform.tfvars
    fi
    if [[ -n "$ACCESS_START_HOUR" ]]; then
         echo "access_start_hour = ${ACCESS_START_HOUR}" >> gemini-stage-0/terraform.tfvars
    fi
    if [[ -n "$ACCESS_END_HOUR" ]]; then
         echo "access_end_hour = ${ACCESS_END_HOUR}" >> gemini-stage-0/terraform.tfvars
    fi
    if [[ -n "$ACCESS_TIME_ZONE" ]]; then
         echo "access_time_zone = \"${ACCESS_TIME_ZONE}\"" >> gemini-stage-0/terraform.tfvars
    fi
    if [[ -n "$ACCESS_EXPIRATION_TIMESTAMP" ]]; then
         echo "access_expiration_timestamp = \"${ACCESS_EXPIRATION_TIMESTAMP}\"" >> gemini-stage-0/terraform.tfvars
    fi
    
    # Add Allowed IPs
    echo "allowed_ip_ranges = ${ALLOWED_IPS}" >> gemini-stage-0/terraform.tfvars

    echo -e "${GREEN}Configuration generated in gemini-stage-0/terraform.tfvars${NC}"

    return 0
}

deploy_stage_0() {
    echo ""
    echo -e "${BLUE}--- Deploying Stage 0 ---${NC}"
    
    cd gemini-stage-0
    rm -f backend.tf
    rm -rf .terraform
    
    echo "Initializing Terraform..."
    if ! terraform init -migrate-state -backend-config="bucket=${BUCKET_NAME}" -backend-config="prefix=terraform/state/stage-0"; then
        echo -e "${RED}Terraform Init failed! Please try resolving the error and running the Step again.${NC}"
        cd ..
        pause
        return 1
    fi
    
    echo ""
    echo "Applying Terraform..."
    if ! terraform apply -var-file="terraform.tfvars"; then
        echo -e "${RED}Terraform Apply failed! Please try resolving the error and running the Step again.${NC}"
        cd ..
        pause
        return 1
    fi
    
    GEMINI_IP=$(terraform output -raw gemini_enterprise_ip 2>/dev/null || echo "N/A")
    CMEK_KEY_ID=$(terraform output -raw cmek_key_id 2>/dev/null || echo "")
    cd ..
    echo -e "${GREEN}Stage 0 Deployment Complete!${NC}"
    # Optionally register the CMEK Key for US Multi-Region in Discovery Engine
    if [[ "$ENABLE_DS_CMEK" == "true" || "$COMPLIANCE_REGIME" == "IL4" || "$COMPLIANCE_REGIME" == "IL5" ]]; then
        # Check if key is managed by TF (Safety Check)
        if terraform -chdir=gemini-stage-0 state list | grep -q "google_kms_crypto_key.gemini_enterprise" 2>/dev/null; then
            echo -e "${YELLOW}CMEK Key is managed by Terraform. Registering it after creation...${NC}"
            
            CMEK_KEY_ID=$(terraform -chdir=gemini-stage-0 output -raw cmek_key_id 2>/dev/null || echo "")
            
            if [[ -n "$CMEK_KEY_ID" && "$CMEK_KEY_ID" != "null" ]]; then
                ACCESS_TOKEN=$(gcloud auth print-access-token)
                
                API_RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH \
                    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
                    -H "Content-Type: application/json" \
                    -H "x-goog-user-project: ${PROJECT_ID}" \
                    "https://us-discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}/locations/us/cmekConfigs/default_cmek_config?set_default=true" \
                    -d "{\"kmsKey\": \"${CMEK_KEY_ID}\"}")
                    
                HTTP_CODE=$(echo "$API_RESPONSE" | tail -n1)
                BODY=$(echo "$API_RESPONSE" | sed '$d')
                
                if [[ "$HTTP_CODE" -eq 200 || "$HTTP_CODE" -eq 409 ]]; then
                    echo -e "${GREEN}Successfully registered CMEK key for Gemini Enterprise.${NC}"
                else
                    echo -e "${RED}Failed to register CMEK key. HTTP Status: ${HTTP_CODE}${NC}"
                    echo -e "Response: $BODY"
                    echo -e "You may need to manually register the key."
                fi
            else
                echo -e "${RED}Warning: CMEK key was enabled but no key ID was found in terraform output. Skipping registration.${NC}"
            fi
        fi
    fi


    if [[ "$CREATE_DS_BOOL" == "true" ]]; then
        echo ""
        echo -e "${YELLOW}ACTION REQUIRED: Populate the created Data Stores with data.${NC}"
        echo ""
        echo -e "${BLUE}GCS${NC}: Upload your documents to the GCS bucket(s) created by Terraform (see output above \`gcs_data_stores\`)."
        echo -e "${BLUE}BigQuery${NC}: Populate the BigQuery dataset(s) created by Terraform (see output above \`bq_data_stores\`)"
        echo ""
        echo -e "After uploading documents into the bucket / dataset, navigate to:"
        echo -e "${YELLOW}Helper Functions${NC} > ${YELLOW}3. Import Documents to Gemini Enterprise Data Store (Cloud Storage / BigQuery)${NC}"
        echo -e "to import the data into the Gemini Enterprise Data Stores and begin the indexing process."
        echo ""
        read -p "Press Enter to acknowledge and continue..."
    fi
    
    CERT_CHOICE=$(grep "cert_management_choice" gemini-stage-0/terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
    DEPLOY_TYPE=$(grep "deployment_type" gemini-stage-0/terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')

    echo ""
    echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
    echo -e "1. From the Main Menu select ${BLUE}Step 2 - Create Gemini Enterprise App (gem4gov-cli)${NC}."
    
    if [[ "$DEPLOY_TYPE" != "none" ]]; then
        echo -e "2. Setup DNS A Record that points the desired Gemini Enterprise subdomain (i.e. gemini.yourdomain.com) to the provisioned Load Balancer IP address (${GEMINI_IP})."
        if [[ "$CERT_CHOICE" == "google_managed" ]]; then
            DNS_RECORDS=$(terraform -chdir=gemini-stage-0 output -json dns_auth_records 2>/dev/null)
            DNS_NAME=$(echo "$DNS_RECORDS" | jq -r '.[0].name // empty')
            DNS_TYPE=$(echo "$DNS_RECORDS" | jq -r '.[0].type // empty')
            DNS_DATA=$(echo "$DNS_RECORDS" | jq -r '.[0].data // empty')
            echo -e "3. ${YELLOW}ACTION REQUIRED: Add the following CNAME record to your DNS configuration for the Google-managed certificate authorization!${NC}"
            echo -e "   - ${BLUE}Name:${NC} ${DNS_NAME}"
            echo -e "   - ${BLUE}Type:${NC} ${DNS_TYPE}"
            echo -e "   - ${BLUE}Data:${NC} ${DNS_DATA}"
            echo -e "   The certificate will not provision until this CNAME is resolvable."
        else
            echo -e "3. Provision an SSL Certificate and upload it to Google Cloud Region (${YELLOW}Helper Functions > Upload SSL Certificate${NC})."
            echo -e "   - Requirements: The certificate must be valid for the domain you intend to use and include the full certificate chain."
        fi
        echo -e "4. From the Main Menu select ${BLUE}Step 3 - Configure & Deploy Load Balancer / Access Policies (gemini-stage-1)${NC}."
    fi
    pause
}

# --- Gem4Gov Functions ---

ensure_gem4gov_installed() {
    if ! command -v gem4gov &> /dev/null; then
        if [[ -d "gem4gov-cli" ]]; then
            echo "Installing gem4gov CLI..."
            pip3 install -e gem4gov-cli
            export PATH="$PATH:$(python3 -m site --user-base)/bin"
        else
            echo -e "${RED}gem4gov-cli directory not found.${NC}"
            return 1
        fi
    fi
    return 0
}

configure_gem4gov() {
    echo ""
    echo -e "${BLUE}--- Configure Gemini Enterprise App (gem4gov) ---${NC}"
    
    if ! ensure_gem4gov_installed; then
        return 1
    fi

    # Retrieve outputs from Stage 0 state
    # Ensure BUCKET_NAME is set from STATE_BUCKET if not already
    if [[ -z "$BUCKET_NAME" && -n "$STATE_BUCKET" ]]; then
        BUCKET_NAME=$(echo "$STATE_BUCKET" | sed 's/gs:\/\/ //' | sed 's/\/$//')
    fi
    
    echo "Retrieving state from gs://${BUCKET_NAME}/terraform/state/stage-0/default.tfstate..."
    STATE_CONTENT=$(gcloud storage cat "gs://${BUCKET_NAME}/terraform/state/stage-0/default.tfstate" 2>/dev/null || echo "{}")
    
    # Parse needed values
    PROJECT_ID_STATE=$(echo "$STATE_CONTENT" | jq -r '.outputs.main_project_id.value // empty')
    PROJECT_ID=${PROJECT_ID_STATE:-$PROJECT_ID}
    
    # Parse Compliance Regime
    COMPLIANCE_REGIME_STATE=$(echo "$STATE_CONTENT" | jq -r '.outputs.compliance_regime.value // empty')
    COMPLIANCE_REGIME=${COMPLIANCE_REGIME_STATE:-$COMPLIANCE_REGIME}
    
    # Parse Load Balancer IP for display
    GEMINI_IP=$(echo "$STATE_CONTENT" | jq -r '.outputs.gemini_enterprise_ip.value // "N/A"')
    
    # Parse Data Stores
    GCS_JSON_RAW=$(echo "$STATE_CONTENT" | jq -c '.outputs.gcs_data_stores.value // {} | to_entries | map(select(.value.data_store_id != null)) | map(.value)' 2>/dev/null)
    BQ_JSON_RAW=$(echo "$STATE_CONTENT" | jq -c '.outputs.bq_data_stores.value // {} | to_entries | map(select(.value.data_store_id != null)) | map(.value)' 2>/dev/null)
    
    if [[ "$GCS_JSON_RAW" == "[]" || -z "$GCS_JSON_RAW" ]]; then GCS_JSON_RAW=""; fi
    if [[ "$BQ_JSON_RAW" == "[]" || -z "$BQ_JSON_RAW" ]]; then BQ_JSON_RAW=""; fi

    DS_ID_ARRAY=()
    DS_DISPLAY_ARRAY=()
    
    if [[ -n "$GCS_JSON_RAW" ]]; then
        while IFS= read -r id; do [[ -n "$id" ]] && DS_ID_ARRAY+=("$id"); done < <(echo "$GCS_JSON_RAW" | jq -r '.[].data_store_id')
        while IFS= read -r disp; do [[ -n "$disp" ]] && DS_DISPLAY_ARRAY+=("$disp"); done < <(echo "$GCS_JSON_RAW" | jq -r '.[].display_name')
    fi
    if [[ -n "$BQ_JSON_RAW" ]]; then
        while IFS= read -r id; do [[ -n "$id" ]] && DS_ID_ARRAY+=("$id"); done < <(echo "$BQ_JSON_RAW" | jq -r '.[].data_store_id')
        while IFS= read -r disp; do [[ -n "$disp" ]] && DS_DISPLAY_ARRAY+=("$disp"); done < <(echo "$BQ_JSON_RAW" | jq -r '.[].display_name')
    fi

    echo ""
    echo -e "${BLUE}--- Application Details ---${NC}"
    echo -e "${YELLOW}Please provide details for the Gemini Enterprise Application.${NC}"
    APP_LIST=()
    
    while true; do
        APP_DISPLAY=""
        while [[ -z "$APP_DISPLAY" ]]; do
            read -p "Please enter a Display Name for the Application: " APP_DISPLAY
        done
        
        APP_COMPANY=""
        while [[ -z "$APP_COMPANY" ]]; do
            read -p "Please enter the Agency / Department Name (no abbreviations): " APP_COMPANY
        done
        
        echo ""
        echo -e "${YELLOW}WARNING: Enabling Gemini Enterprise Usage Audit logs will write user queries, model thinking, and model responses to Cloud Logging.${NC}"
        echo -e "${YELLOW}You must ensure that logging permissions are set to allow only necessary principals to access.${NC}"
        read -p "Would you like to enable Gemini Enterprise Usage Audit logs (conversation logging) for this application? [y/N]: " ENABLE_AUDIT_LOGS
        if [[ "$ENABLE_AUDIT_LOGS" =~ ^[Yy]$ ]]; then
            ENABLE_AUDIT_LOGS_FLAG="true"
        else
            ENABLE_AUDIT_LOGS_FLAG="false"
        fi

        echo ""
        echo -e "${YELLOW}Agent Sharing Feature:${NC}"
        echo -e "${YELLOW}When enabled, users can share agents with other users using the Gemini Enterprise app.${NC}"
        read -p "Would you like to enable the 'Agent Sharing' feature? [y/N]: " ENABLE_AGENT_SHARING
        if [[ "$ENABLE_AGENT_SHARING" =~ ^[Yy]$ ]]; then
            ENABLE_AGENT_SHARING_FLAG="true"
            sed -i '' 's/disable-agent-sharing:.*/disable-agent-sharing: "FEATURE_STATE_OFF"/' gem4gov-cli/engine_features.yaml 2>/dev/null || sed -i 's/disable-agent-sharing:.*/disable-agent-sharing: "FEATURE_STATE_OFF"/' gem4gov-cli/engine_features.yaml
        else
            ENABLE_AGENT_SHARING_FLAG="false"
            sed -i '' 's/disable-agent-sharing:.*/disable-agent-sharing: "FEATURE_STATE_ON"/' gem4gov-cli/engine_features.yaml 2>/dev/null || sed -i 's/disable-agent-sharing:.*/disable-agent-sharing: "FEATURE_STATE_ON"/' gem4gov-cli/engine_features.yaml
        fi

        echo ""
        echo -e "${YELLOW}Agent Sharing without Admin Approval Feature:${NC}"
        echo -e "${YELLOW}When enabled, users on your team can share and use agents without admin approval when using the Gemini Enterprise app.${NC}"
        read -p "Would you like to enable 'Agent Sharing without Admin Approval'? [y/N]: " ENABLE_AGENT_SHARING_NO_APPROVAL
        if [[ "$ENABLE_AGENT_SHARING_NO_APPROVAL" =~ ^[Yy]$ ]]; then
            ENABLE_AGENT_SHARING_NO_APPROVAL_FLAG="true"
            sed -i '' 's/agent-sharing-without-admin-approval:.*/agent-sharing-without-admin-approval: "FEATURE_STATE_ON"/' gem4gov-cli/engine_features.yaml 2>/dev/null || sed -i 's/agent-sharing-without-admin-approval:.*/agent-sharing-without-admin-approval: "FEATURE_STATE_ON"/' gem4gov-cli/engine_features.yaml
        else
            ENABLE_AGENT_SHARING_NO_APPROVAL_FLAG="false"
            sed -i '' 's/agent-sharing-without-admin-approval:.*/agent-sharing-without-admin-approval: "FEATURE_STATE_OFF"/' gem4gov-cli/engine_features.yaml 2>/dev/null || sed -i 's/agent-sharing-without-admin-approval:.*/agent-sharing-without-admin-approval: "FEATURE_STATE_OFF"/' gem4gov-cli/engine_features.yaml
        fi
        
        echo ""
        # Determine App Key
        APP_SUFFIX=$(python3 -c "import random, string; print(''.join(random.choices(string.ascii_lowercase + string.digits, k=4)))")
        ENG_ID="g4g-gem-ent-app-${APP_SUFFIX}"
        
        SELECTED_IDS=""
        if [[ ${#DS_ID_ARRAY[@]} -gt 0 ]]; then
            echo -e "${YELLOW}Available Data Stores for association:${NC}"
            i=1
            for idx in "${!DS_ID_ARRAY[@]}"; do
                echo "$i. ${DS_DISPLAY_ARRAY[$idx]} (${DS_ID_ARRAY[$idx]})"
                ((i++))
            done
            read -p "Select Data Stores to associate (comma-separated numbers, e.g. 1,3) [Enter to skip]: " APP_DS_SEL
            
            if [[ -n "$APP_DS_SEL" ]]; then
                IFS=',' read -ra SELECTED_INDICES <<< "$APP_DS_SEL"
                SELECTED_DS_LIST=()
                for index in "${SELECTED_INDICES[@]}"; do
                    index=$(echo "$index" | xargs)
                    if [[ "$index" =~ ^[0-9]+$ ]] && (( index >= 1 && index <= ${#DS_ID_ARRAY[@]} )); then
                        SELECTED_DS_LIST+=("${DS_ID_ARRAY[$((index-1))]}")
                    fi
                done
                if [[ ${#SELECTED_DS_LIST[@]} -gt 0 ]]; then
                    SELECTED_IDS=$(IFS=,; echo "${SELECTED_DS_LIST[*]}")
                fi
            fi
        fi
        
        APP_JSON=$(jq -n \
            --arg id "$ENG_ID" \
            --arg display "$APP_DISPLAY" \
            --arg company "$APP_COMPANY" \
            --arg ds "$SELECTED_IDS" \
            --arg audit_logs "$ENABLE_AUDIT_LOGS_FLAG" \
            '{engine_id: $id, display_name: $display, company_name: $company, data_stores: $ds, enable_audit_logs: $audit_logs}')
        APP_LIST+=("$APP_JSON")
        
        echo ""
        read -p "[PREVIEW] Do you want to create another Gemini Enterprise Application? [y/N]: " CREATE_APP
        if [[ ! "$CREATE_APP" =~ ^[Yy]$ ]]; then
            break
        fi
    done
    
    if [[ ${#APP_LIST[@]} -eq 0 ]]; then
         echo "No applications generated."
         pause
         return 0
    fi

    # 2. Extract Workforce Identity Details
    POOL_NAME=$(echo "$STATE_CONTENT" | jq -r '.outputs.acl_workforce_pool_name.value // empty')
    PROVIDER_ID=$(echo "$STATE_CONTENT" | jq -r '.outputs.acl_workforce_provider_id.value // empty')
    
    # Check IdP Type for debugging/validation
    IDP_TYPE=$(echo "$STATE_CONTENT" | jq -r '.outputs.acl_idp_type.value // empty')

    if [[ "$IDP_TYPE" == "THIRD_PARTY" ]]; then
        if [[ -z "$POOL_NAME" || -z "$PROVIDER_ID" ]]; then
             echo -e "${RED}Error: Third Party IdP selected but Pool/Provider details missing in state.${NC}"
             echo "Please ensure Stage 0 was deployed with Third Party configuration."
        fi
    fi
    
    WIF_ARGS=""
    if [[ -n "$POOL_NAME" && -n "$PROVIDER_ID" ]]; then
        # Extract Pool ID from full name (locations/global/workforcePools/POOL_ID)
        POOL_ID=$(basename "$POOL_NAME")
        WIF_ARGS="--workforce-pool-id $POOL_ID --workforce-provider-id $PROVIDER_ID"
    fi

    export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
    export GOOGLE_CLOUD_QUOTA_PROJECT="${PROJECT_ID}"

    echo ""
    echo "Executing Application Configurations..."
    
    # Iterate apps
    for APP_JSON in "${APP_LIST[@]}"; do
        
        ENG_ID=$(echo "$APP_JSON" | jq -r '.engine_id')
        DISP_NAME=$(echo "$APP_JSON" | jq -r '.display_name')
        COMP_NAME=$(echo "$APP_JSON" | jq -r '.company_name')
        DS_KEYS=$(echo "$APP_JSON" | jq -r '.data_stores // empty')
        
        CMD="gem4gov app create --project-id \"${PROJECT_ID}\" --engine-id \"${ENG_ID}\" --display-name \"${DISP_NAME}\" --company-name \"${COMP_NAME}\""
        
        ENABLE_AUDIT_LOGS=$(echo "$APP_JSON" | jq -r '.enable_audit_logs // "false"')
        if [[ "$ENABLE_AUDIT_LOGS" == "true" ]]; then
            CMD="$CMD --enable-audit-logs"
        fi
        
        if [[ -n "$COMPLIANCE_REGIME" && "$COMPLIANCE_REGIME" != "NONE" ]]; then
            CMD="$CMD --compliance-regime \"${COMPLIANCE_REGIME}\""
        fi
        
        if [[ -n "$DS_KEYS" && "$DS_KEYS" != "null" && "$DS_KEYS" != "\"\"" ]]; then
             CMD="$CMD --data-stores \"${DS_KEYS}\""
        fi
        
        if [[ -n "$WIF_ARGS" ]]; then
            CMD="$CMD $WIF_ARGS"
        fi
        
        echo -e "${BLUE}Creating Application: ${DISP_NAME} (${ENG_ID})...${NC}"
        echo "Running: $CMD"
        if ! eval "$CMD"; then
             echo -e "${RED}Error: Failed to create Application ${DISP_NAME}. Aborting.${NC}"
             pause
             return 1
        fi
        echo ""
    done
    
    echo -e "${GREEN}Gemini Enterprise Applications configured.${NC}"

    echo ""
    echo -e "${YELLOW}IMPORTANT NEXT STEPS:${NC}"
    echo -e "1. Take note of the ${GREEN}Gemini Enterprise Widget Config ID${NC} from the output above for the configuration of the Load Balancer.${NC}"
    echo -e "2. Setup DNS A Record that points the desired Gemini Enterprise subdomain (i.e. gemini.yourdomain.com) to the provisioned Load Balancer IP address (${GEMINI_IP})."
    echo -e "3. Provision an SSL Certificate and upload it to Google Cloud Certificate Manager (${YELLOW}Helper Functions > Upload SSL Certificate${NC})."
    echo -e "4. From the Main Menu select ${BLUE}Step 3 - Configure & Deploy Load Balancer / Access Policies (gemini-stage-1)${NC}."
    pause
}

update_app_compliance() {
    echo -e "${BLUE}--- Update Gemini Enterprise App Compliance ---${NC}"

    if ! ensure_gem4gov_installed; then
        return 1
    fi

    # Ensure Project ID is set
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Project ID is required. Please select a project first.${NC}"
        return 1
    fi

    read -p "Enter Gemini Enterprise Engine ID: " ENGINE_ID
    if [[ -z "$ENGINE_ID" ]]; then
        echo -e "${RED}Engine ID is required.${NC}"
        return 1
    fi

    echo "Select Compliance Regime:"
    echo "1. FedRAMP High"
    echo "2. IL4"
    read -p "Select an option [1-2]: " COMPLIANCE_SEL

    COMPLIANCE_REGIME=""
    if [[ "$COMPLIANCE_SEL" == "1" ]]; then
        COMPLIANCE_REGIME="FEDRAMP_HIGH"
    elif [[ "$COMPLIANCE_SEL" == "2" ]]; then
        COMPLIANCE_REGIME="IL4"
    else
        echo -e "${RED}Invalid selection.${NC}"
        return 1
    fi

    CMD="gem4gov app update-compliance --project-id ${PROJECT_ID} --engine-id ${ENGINE_ID} --compliance-regime ${COMPLIANCE_REGIME}"
    
    echo "Running: $CMD"
    export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
    export GOOGLE_CLOUD_QUOTA_PROJECT="${PROJECT_ID}"
    if ! $CMD; then
        echo -e "${RED}ERROR: Failed to update compliance regime.${NC}"
        return 1
    fi
    
    pause
}

# --- Helper Functions Menu ---

upload_ssl_certificate() {
    echo -e "${BLUE}--- Upload SSL Certificate ---${NC}"
    
    # Ensure Project ID is set
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Project ID is required. Please select a project first.${NC}"
        return 1
    fi

    echo -e "${YELLOW}Requirements for Self-Managed SSL Certificates:${NC}"
    echo -e "1. Certificate and Key must be in ${BLUE}PEM format${NC}."
    echo -e "2. Private Key must ${RED}NOT${NC} be protected by a passphrase."
    echo -e "3. Encryption algorithm must be either ${BLUE}RSA${NC} or ${BLUE}ECDSA${NC}."
    echo -e "   - RSA-2048 or ECDSA P-256 are recommended."
    echo ""
    echo -e "For more details, see: https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/self-managed-certs#create-key-and-cert"
    echo ""

    read -p "Enter Certificate Name (e.g., my-cert): " CERT_NAME
    if [[ -z "$CERT_NAME" ]]; then
        echo -e "${RED}Certificate Name is required.${NC}"
        return 1
    fi

    # Default region
    DEFAULT_REGION=${REGION:-"us-east4"}
    read -p "Enter Network Region [${DEFAULT_REGION}]: " INPUT_REGION
    CERT_REGION=${INPUT_REGION:-$DEFAULT_REGION}

    while true; do
        read -p "Enter path to Certificate File (.crt/.pem): " CERT_PATH
        # Expand tilde if present
        CERT_PATH="${CERT_PATH/#\~/$HOME}"
        if [[ -f "$CERT_PATH" ]]; then
            if grep -qE -e "-----BEGIN CERTIFICATE-----" "$CERT_PATH"; then
                break
            else
                echo -e "${RED}Error: File does not appear to be a PEM-formatted certificate (missing '-----BEGIN CERTIFICATE-----').${NC}"
            fi
        else
            echo -e "${RED}File not found: $CERT_PATH${NC}"
        fi
    done

    while true; do
        read -p "Enter path to Private Key File (.key/.pem): " KEY_PATH
        # Expand tilde if present
        KEY_PATH="${KEY_PATH/#\~/$HOME}"
        if [[ -f "$KEY_PATH" ]]; then
            if grep -qE -e "-----BEGIN .*PRIVATE KEY-----" "$KEY_PATH"; then
                break
            else
                echo -e "${RED}Error: File does not appear to be a PEM-formatted private key (missing '-----BEGIN ... PRIVATE KEY-----').${NC}"
            fi
        else
            echo -e "${RED}File not found: $KEY_PATH${NC}"
        fi
    done

    echo ""
    echo "Creating Regional SSL Certificate..."
    echo "Name: ${CERT_NAME}"
    echo "Region: ${CERT_REGION}"
    echo "Certificate: ${CERT_PATH}"
    echo "Key: ${KEY_PATH}"
    echo ""
    
    if gcloud compute ssl-certificates create "$CERT_NAME" \
        --certificate="$CERT_PATH" \
        --private-key="$KEY_PATH" \
        --region="$CERT_REGION" \
        --project="$PROJECT_ID"; then
        echo -e "${GREEN}SSL Certificate '${CERT_NAME}' created successfully!${NC}"
    else
        echo -e "${RED}Failed to create SSL Certificate.${NC}"
    fi
    
    pause
}

replace_gemini_app() {
    echo -e "${BLUE}--- Replace Gemini Enterprise Application / Load Balancer Routing ---${NC}"
    echo -e "${RED}WARNING: This will create a NEW Gemini Enterprise Application and update the Load Balancer to route traffic to it.${NC}"
    echo -e "${YELLOW}The old application will NOT be deleted automatically.${NC}"
    echo ""
    read -p "Are you sure you want to proceed? (y/N): " CONFIRM
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
        return 0
    fi

    # 1. Create new App
    configure_gem4gov || return 1

    # 2. Update Networking (Stage 1)
    echo ""
    echo -e "${YELLOW}IMPORTANT: When prompted to 'Reuse existing configuration' for Stage 1, answer 'n' (No).${NC}"
    echo -e "${YELLOW}You MUST enter the NEW Gemini Enterprise Widget Config ID from the previous step.${NC}"
    echo ""
    pause

    configure_stage_1 || return 1
    deploy_stage_1
}

import_documents_helper() {
    echo ""
    echo -e "${BLUE}--- Import Documents into Data Store ---${NC}"

    if ! ensure_gem4gov_installed; then
        return 1
    fi
    
    # Ensure Project ID is set
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Project ID is required. Please select a project first.${NC}"
        return 1
    fi

    # Hydrate state and populate STATE_CONTENT
    hydrate_from_state

    # Parse GCS Data Stores
    GCS_DS_MAP=$(echo "$STATE_CONTENT" | jq -c '
      .outputs.gcs_data_stores.value // {} | to_entries | map(select(.value.data_store_id != null)) | map(.value)
    ' 2>/dev/null)

    # Parse BigQuery Data Stores
    BQ_DS_MAP=$(echo "$STATE_CONTENT" | jq -c '
      .outputs.bq_data_stores.value // {} | to_entries | map(select(.value.data_store_id != null)) | map(.value)
    ' 2>/dev/null)

    echo ""
    echo "Available Data Stores:"
    
    # Create arrays to store options
    DS_IDS=()
    DS_TYPES=()
    DS_SOURCES=()
    
    COUNT=0
    
    # List GCS Data Stores
    if [[ "$GCS_DS_MAP" != "[]" && -n "$GCS_DS_MAP" ]]; then
        for i in $(jq -r 'keys[]' <<< "$GCS_DS_MAP"); do
            DS_ID=$(jq -r ".[$i].data_store_id" <<< "$GCS_DS_MAP")
            BUCKET=$(jq -r ".[$i].bucket_name" <<< "$GCS_DS_MAP")
            COUNT=$((COUNT+1))
            echo "${COUNT}. [GCS] ${DS_ID} (Bucket: ${BUCKET})"
            DS_IDS+=("$DS_ID")
            DS_TYPES+=("gcs")
            DS_SOURCES+=("$BUCKET")
        done
    fi

    # List BigQuery Data Stores
    if [[ "$BQ_DS_MAP" != "[]" && -n "$BQ_DS_MAP" ]]; then
        for i in $(jq -r 'keys[]' <<< "$BQ_DS_MAP"); do
            DS_ID=$(jq -r ".[$i].data_store_id" <<< "$BQ_DS_MAP")
            DATASET=$(jq -r ".[$i].dataset_id" <<< "$BQ_DS_MAP")
            TABLE=$(jq -r ".[$i].table_id" <<< "$BQ_DS_MAP")
            COUNT=$((COUNT+1))
            echo "${COUNT}. [BigQuery] ${DS_ID} (Table: ${DATASET}.${TABLE})"
            DS_IDS+=("$DS_ID")
            DS_TYPES+=("bigquery")
            DS_SOURCES+=("${DATASET}.${TABLE}")
        done
    fi

    if [[ "$COUNT" -eq 0 ]]; then
        echo -e "${YELLOW}No data stores found in Stage 0 state.${NC}"
        pause
        return 0
    fi

    echo ""
    RANGE_STR="[1]"
    if [[ "$COUNT" -gt 1 ]]; then
        RANGE_STR="[1-${COUNT}]"
    fi
    read -p "Select a Data Store to import into ${RANGE_STR}: " SELECTION

    if [[ ! "$SELECTION" =~ ^[0-9]+$ ]] || [[ "$SELECTION" -lt 1 ]] || [[ "$SELECTION" -gt "$COUNT" ]]; then
        echo -e "${RED}Invalid selection.${NC}"
        pause
        return 1
    fi

    # valid selection (0-indexed array)
    INDEX=$((SELECTION-1))
    SELECTED_ID="${DS_IDS[$INDEX]}"
    SELECTED_TYPE="${DS_TYPES[$INDEX]}"
    SELECTED_SOURCE="${DS_SOURCES[$INDEX]}"
    echo -e "${GREEN}Selected: ${SELECTED_ID} (${SELECTED_TYPE})${NC}"
    echo ""

    if [[ "$SELECTED_TYPE" == "gcs" ]]; then
        CMD_ARRAY=(gem4gov datastore import --project-id "${PROJECT_ID}" --data-store-id "${SELECTED_ID}" --source-type "${SELECTED_TYPE}" --gcs-bucket "${SELECTED_SOURCE}")
        if ! "${CMD_ARRAY[@]}"; then
            echo -e "${RED}Error: Failed to import documents from GCS.${NC}"
            return 1
        fi
        export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
        export GOOGLE_CLOUD_QUOTA_PROJECT="${PROJECT_ID}"
    elif [[ "$SELECTED_TYPE" == "bigquery" ]]; then
        echo -e "${YELLOW}--- BigQuery Document Import ---${NC}"
        
        # BQ_DS_MAP gives us dataset.table directly in SELECTED_SOURCE variable
        # Use tr to remove any lingering carriage returns from jq parsing
        CLEAN_SOURCE=$(echo "$SELECTED_SOURCE" | tr -d '\r\n ')
        SOURCE_PARTS=(${CLEAN_SOURCE//./ })
        DATASET=${SOURCE_PARTS[0]}
        TABLE=${SOURCE_PARTS[1]}
        
        USE_EXISTING="n"
        CUSTOM_SCHEMA_FILE=""
        
        echo "Detecting BigQuery Table Schema for ${PROJECT_ID}:${DATASET}.${TABLE}..."
        
        # Capture schema. We evaluate BQ_EXIT locally to prevent $? from being overwritten by echos.
        BQ_SCHEMA_JSON=$(PYTHONPATH="" bq show --schema --format=prettyjson "${PROJECT_ID}:${DATASET}.${TABLE}")
        BQ_EXIT=$?
        
        echo "## DEBUG bq exit code: $BQ_EXIT"
        
        if [ $BQ_EXIT -eq 0 ] && [ -n "$BQ_SCHEMA_JSON" ] && [ "$BQ_SCHEMA_JSON" != "null" ]; then
            echo ""
            echo "Successfully retrieved BigQuery Table schema:"
            echo "$BQ_SCHEMA_JSON" | jq '.'
            echo ""
            read -p "Would you like to use this schema for the bigquery data store? (y/N): " USE_EXISTING
        else
            echo -e "${RED}Failed to automatically detect BigQuery schema or table is empty.${NC}"
        fi
        
        if [[ "$USE_EXISTING" != "y" && "$USE_EXISTING" != "Y" ]]; then
            echo ""
            read -p "Enter the path to your custom JSON schema file: " CUSTOM_SCHEMA_FILE
            
            # 1. Check if the file exists and is a regular file
            if [[ ! -f "$CUSTOM_SCHEMA_FILE" ]]; then
                echo -e "${RED}Error: File '$CUSTOM_SCHEMA_FILE' not found or is not a regular file.${NC}"
                pause
                return 1
            fi

            # 2. Prevent explicit path traversal strings
            if [[ "$CUSTOM_SCHEMA_FILE" == *"../"* || "$CUSTOM_SCHEMA_FILE" == *".." ]]; then
                echo -e "${RED}Error: Invalid file path. Path traversal sequences ('../') are not allowed.${NC}"
                pause
                return 1
            fi
            
            # 3. Restrict execution to only files inside the project working directory
            BASE_DIR=$(pwd)
            ABS_PATH=$(realpath "$CUSTOM_SCHEMA_FILE" 2>/dev/null || echo "")
            
            if [[ -z "$ABS_PATH" || "$ABS_PATH" != "$BASE_DIR"* ]]; then
                 echo -e "${RED}Error: Custom schema file must be located within the project folder directory (${BASE_DIR}).${NC}"
                 pause
                 return 1
            fi
        fi
        
        echo ""
        echo -e "${YELLOW}--- Schema Property Mapping ---${NC}"
        echo "A Document ID field is required."
        echo "Optional Semantic Key Properties: title, description, category, uri"
        echo ""
        
        # Extract fields to show the user
        if [[ "$USE_EXISTING" == "y" || "$USE_EXISTING" == "Y" ]]; then
            # Show BQ fields
            FIELDS=$(echo "$BQ_SCHEMA_JSON" | jq -r '[.[].name] | join(", ")')
        else
            # Show fields from Custom JSON schema (assumes top level properties)
            FIELDS=$(cat "$CUSTOM_SCHEMA_FILE" | jq -r '[.properties | keys[]] | join(", ")')
        fi
        
        echo "Available Fields: $FIELDS"
        echo ""
        
        read -p "Enter the field you would like to use as the unique identifier (leave blank for Auto): " ID_FIELD
        read -p "Enter the field you would like to use for 'title' key property (leave blank for None): " TITLE_FIELD
        read -p "Enter the field you would like to use for 'description' key property (leave blank for None): " DESC_FIELD
        read -p "Enter the field you would like to use for 'category' key property (leave blank for None): " CAT_FIELD
        read -p "Enter the field you would like to use for 'uri' key property (leave blank for None): " URI_FIELD
        
        # Generate Discovery Engine JSON Schema using inline Python
        echo ""
        echo "Generating Discovery Engine Schema..."
        
        export PYTHONPATH=""
        export BQ_SCHEMA_JSON
        export CUSTOM_SCHEMA_FILE
        export TITLE_FIELD DESC_FIELD CAT_FIELD URI_FIELD
        DE_SCHEMA_JSON=$(python3 << 'EOF'
import json
import os

key_mappings = {
    "title": os.environ.get("TITLE_FIELD", ""),
    "description": os.environ.get("DESC_FIELD", ""),
    "category": os.environ.get("CAT_FIELD", ""),
    "uri": os.environ.get("URI_FIELD", "")
}
key_properties = {k: v for k, v in key_mappings.items() if v}

custom_file = os.environ.get("CUSTOM_SCHEMA_FILE", "")
if custom_file:
    with open(custom_file, "r") as f:
        schema = json.load(f)
    for key, val in key_properties.items():
        if val in schema.get("properties", {}):
            schema["properties"][val]["keyPropertyMapping"] = key
else:
    bq_schema = json.loads(os.environ.get("BQ_SCHEMA_JSON", "[]"))
    
    def get_json_type(bq_type):
        if bq_type in ["INTEGER", "INT64"]: return "integer"
        elif bq_type in ["FLOAT", "FLOAT64", "NUMERIC", "BIGNUMERIC"]: return "number"
        elif bq_type in ["BOOLEAN", "BOOL"]: return "boolean"
        return "string"

    def transform(fields):
        props = {}
        for f in fields:
            fname = f["name"]
            ftype = f.get("type", "STRING")
            if ftype in ["RECORD", "STRUCT"]:
                pdef = {"type": "object", "properties": transform(f.get("fields", []))}
            else:
                jtype = get_json_type(ftype)
                is_matched_key = fname in key_properties.values()
                
                pdef = {"type": jtype}
                if is_matched_key:
                    matched_key = [k for k,v in key_properties.items() if v == fname][0]
                    pdef["keyPropertyMapping"] = matched_key
                    pdef["retrievable"] = True if jtype in ["number", "string", "boolean", "integer", "datetime", "geolocation"] else False
                else:
                    pdef["searchable"] = True if jtype == "string" else False
                    pdef["indexable"] = True if jtype in ["number", "string", "boolean", "integer", "datetime", "geolocation"] else False
                    pdef["retrievable"] = True if jtype in ["number", "string", "boolean", "integer", "datetime", "geolocation"] else False

            if f.get("mode") == "REPEATED":
                props[fname] = {"type": "array", "items": pdef}
            else:
                props[fname] = pdef
        return props

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": transform(bq_schema)
    }

print(json.dumps(schema))
EOF
)
        
        echo "Retrieving access token..."
        ACCESS_TOKEN=$(gcloud auth print-access-token)
        
        # Patch Default Schema
        echo "Patching Data Store Default Schema..."
        SCHEMA_URL="https://us-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/us/collections/default_collection/dataStores/${SELECTED_ID}/schemas/default_schema"
        
        PATCH_BODY="{\"structSchema\": $DE_SCHEMA_JSON}"
        
        SCHEMA_RESPONSE=$(curl -s -X PATCH \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "x-goog-user-project: ${PROJECT_ID}" \
            -H "Content-Type: application/json" \
            -d "$PATCH_BODY" \
            "${SCHEMA_URL}")
            
        if echo "$SCHEMA_RESPONSE" | grep -q "\"error\""; then
             echo -e "${RED}Error patching schema:${NC}"
             echo "$SCHEMA_RESPONSE" | jq '.'
             echo "Aborting import."
             pause
             return 1
        fi
        
        echo -e "${GREEN}Default Schema patched successfully.${NC}"
        
        # Start Document Import
        echo "Starting BigQuery Document Import..."
        IMPORT_URL="https://us-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/us/collections/default_collection/dataStores/${SELECTED_ID}/branches/default_branch/documents:import"
        
        IMPORT_BODY="{\"reconciliationMode\": \"FULL\", \"bigquerySource\": {\"projectId\": \"${PROJECT_ID}\", \"datasetId\": \"${DATASET}\", \"tableId\": \"${TABLE}\", \"dataSchema\": \"custom\"}"
        if [[ -z "$ID_FIELD" ]]; then
             IMPORT_BODY="${IMPORT_BODY}, \"autoGenerateIds\": true}"
        else
             IMPORT_BODY="${IMPORT_BODY}, \"idField\": \"${ID_FIELD}\"}"
        fi
        
        IMPORT_RESPONSE=$(curl -s -X POST \
            -H "Authorization: Bearer ${ACCESS_TOKEN}" \
            -H "x-goog-user-project: ${PROJECT_ID}" \
            -H "Content-Type: application/json" \
            -d "$IMPORT_BODY" \
            "${IMPORT_URL}")
            
        if echo "$IMPORT_RESPONSE" | grep -q "\"error\""; then
             echo -e "${RED}Error starting import:${NC}"
             echo "$IMPORT_RESPONSE" | jq '.'
             pause
             return 1
        fi
        
        echo -e "${GREEN}Document import operation started successfully!${NC}"
        echo "Operation Details:"
        echo "$IMPORT_RESPONSE" | jq '.'
        
    fi
    
    pause
}

distribute_gemini_licenses() {
    echo -e "${BLUE}--- Distribute Gemini for Government Licenses ---${NC}"
    
    echo -e "${YELLOW}Prerequisites:${NC}"
    echo "1. You must have the 'Billing Account Administrator' role on the Billing Account."
    echo "2. You must have the 'Service Usage Consumer' role on the project used for API calls."
    echo ""
    read -p "Have you confirmed these prerequisites? (y/N): " PRE_CONFIRM
    if [[ "$PRE_CONFIRM" != "y" && "$PRE_CONFIRM" != "Y" ]]; then
        return 0
    fi

    # Ensure Project ID is set for API quota
    if [[ -z "$PROJECT_ID" ]]; then
        echo -e "${RED}Project ID is required for API quota. Please select a project first.${NC}"
        return 1
    fi

    # Setup gem4gov CLI path
    GEM4GOV_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gem4gov-cli/gem4gov.py"

    while true; do
        read -p "Enter Billing Account ID (e.g., 012345-6789AB-CDEFGH): " BILLING_ACCOUNT_ID
        if [[ -z "$BILLING_ACCOUNT_ID" ]]; then
            echo -e "${RED}Billing Account ID is required.${NC}"
            continue
        fi
        break
    done

    while true; do
        echo -e "${BLUE}Fetching available Gemini Enterprise subscriptions...${NC}"
        
        # Use new gem4gov command
        CONFIGS_JSON=$(python3 "$GEM4GOV_PATH" license list --billing-account "$BILLING_ACCOUNT_ID" --quota-project "$PROJECT_ID" --format json)

        if [[ $? -ne 0 ]] || [[ -z "$CONFIGS_JSON" ]] || [[ "$CONFIGS_JSON" == "[]" ]]; then
            echo -e "${RED}Failed to fetch license configurations or no configurations found.${NC}"
            echo "$CONFIGS_JSON"
            pause
            return 1
        fi

        COUNT=$(echo "$CONFIGS_JSON" | jq '. | length')

        echo "Available Subscriptions:"
        echo "-----------------------------------"
        for i in $(seq 0 $((COUNT-1))); do
            CONFIG=$(echo "$CONFIGS_JSON" | jq -c ".[$i]")
            NAME=$(echo "$CONFIG" | jq -r '.subscriptionDisplayName // .name')
            TOTAL=$(echo "$CONFIG" | jq -r '.licenseCount')
            CONFIG_ID=$(echo "$CONFIG" | jq -r '.name' | awk -F'/' '{print $NF}')
            
            # Calculate distributed licenses
            DISTRIBUTED=$(echo "$CONFIG" | jq -r '.licenseConfigDistributions | values | map(tonumber) | add // 0')
            AVAILABLE=$((TOTAL - DISTRIBUTED))
            
            echo "$((i+1)). ${NAME}"
            echo "   ID: ${CONFIG_ID}"
            echo "   Total Licenses: ${TOTAL}"
            echo "   Distributed: ${DISTRIBUTED}"
            echo "   Available: ${AVAILABLE}"
            echo "-----------------------------------"
        done

        read -p "Select a subscription to distribute from [1-${COUNT}, or 'q' to quit]: " SEL
        if [[ "$SEL" == "q" ]]; then
            return 0
        fi

        if [[ ! "$SEL" =~ ^[0-9]+$ ]] || [[ "$SEL" -lt 1 ]] || [[ "$SEL" -gt "$COUNT" ]]; then
            echo -e "${RED}Invalid selection.${NC}"
            continue
        fi

        SELECTED_CONFIG=$(echo "$CONFIGS_JSON" | jq -c ".[$((SEL-1))]")
        SELECTED_CONFIG_ID=$(echo "$SELECTED_CONFIG" | jq -r '.name' | awk -F'/' '{print $NF}')
        
        read -p "Enter Target Project ID (where licenses will be allocated): " TARGET_PROJECT_ID
        if [[ -z "$TARGET_PROJECT_ID" ]]; then
            echo -e "${RED}Target Project ID is required.${NC}"
            continue
        fi

        TARGET_PROJECT_NUMBER=$(gcloud projects describe "${TARGET_PROJECT_ID}" --format="value(projectNumber)" 2>/dev/null)
        if [[ -z "$TARGET_PROJECT_NUMBER" ]]; then
            echo -e "${RED}Could not find project: ${TARGET_PROJECT_ID}${NC}"
            continue
        fi

        echo "Select Location:"
        echo "1. global"
        echo "2. us"
        echo "3. eu"
        read -p "Select an option [1-3]: " LOC_SEL
        case "$LOC_SEL" in
            1) LOCATION="global" ;;
            2) LOCATION="us" ;;
            3) LOCATION="eu" ;;
            *) echo -e "${RED}Invalid location selection.${NC}"; continue ;;
        esac

        read -p "Number of licenses to distribute (Incremental): " LICENSE_COUNT
        if [[ ! "$LICENSE_COUNT" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}Invalid license count.${NC}"
            continue
        fi

        # Check for existing config
        EXISTING_LICENSE_CONFIG_ID=$(echo "$SELECTED_CONFIG" | jq -r --arg pn "$TARGET_PROJECT_NUMBER" --arg loc "$LOCATION" '
            .licenseConfigDistributions // {} | keys[] | select(contains("projects/\($pn)/locations/\($loc)")) | split("/") | last
        ' | head -n 1)

        echo ""
        echo "Distribution Summary:"
        echo "Subscription: ${SELECTED_CONFIG_ID}"
        echo "Target Project: ${TARGET_PROJECT_ID} (${TARGET_PROJECT_NUMBER})"
        echo "Location: ${LOCATION}"
        echo "Count: ${LICENSE_COUNT}"
        if [[ -n "$EXISTING_LICENSE_CONFIG_ID" ]]; then
            echo "Existing License Config ID Found: ${EXISTING_LICENSE_CONFIG_ID}"
        fi
        echo ""
        read -p "Confirm distribution? (y/N): " CONFIRM
        if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
            continue
        fi

        echo -e "${BLUE}Running API call via gem4gov CLI...${NC}"
        
        # Build command as an array to prevent injection
        CMD_ARRAY=(python3 "$GEM4GOV_PATH" license distribute --billing-account "$BILLING_ACCOUNT_ID" --config-id "$SELECTED_CONFIG_ID" --target-project-number "$TARGET_PROJECT_NUMBER" --location "$LOCATION" --count "$LICENSE_COUNT" --quota-project "$PROJECT_ID")
        if [[ -n "$EXISTING_LICENSE_CONFIG_ID" ]]; then
            CMD_ARRAY+=("--license-config-id" "$EXISTING_LICENSE_CONFIG_ID")
        fi
        
        "${CMD_ARRAY[@]}"

        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}Licenses distributed successfully!${NC}"
        else
            echo -e "${RED}Distribution failed.${NC}"
        fi
        
        echo ""
        read -p "Would you like to perform another distribution? (y/N): " ANOTHER
        if [[ "$ANOTHER" != "y" && "$ANOTHER" != "Y" ]]; then
            break
        fi
    done
}

helper_menu() {
    while true; do
        clear
        print_header
        echo -e "${BLUE}--- Helper Functions ---${NC}"
        echo "1. Update Gemini for Government Compliance"
        echo "2. Replace Gemini Enterprise Application / Load Balancer Routing"
        echo "3. Import Documents to Gemini Enterprise Data Store (Cloud Storage / BigQuery)"
        echo "4. Distribute Gemini for Government Licenses"
        echo "5. Upload SSL Certificate"
        echo "6. Back to Main Menu"
        echo "-----------------------------------"
        read -p "Select an option [1-6]: " OPTION

        case $OPTION in
            1)
                update_app_compliance
                ;;
            2)
                replace_gemini_app
                ;;
            3)  
                import_documents_helper
                ;;
            4)
                distribute_gemini_licenses
                ;;
            5)
                upload_ssl_certificate
                ;;
            6)
                return 0
                ;;
            *)
                echo "Invalid option."
                pause
                ;;
        esac
    done
}

# --- Stage 1 Functions ---

configure_stage_1() {
    echo ""
    echo -e "${BLUE}--- Configure Stage 1 (Load Balancer / Access Policies) ---${NC}"
    mkdir -p gemini-stage-1
    
    if [[ -f "gemini-stage-1/terraform.tfvars" ]]; then
        echo -e "${RED}WARNING: Answering 'n' will OVERWRITE existing gemini-stage-1/terraform.tfvars${NC}"
        read -p "Reuse existing configuration? (Y/n): " REUSE_CONFIG
        if [[ "$REUSE_CONFIG" != "n" && "$REUSE_CONFIG" != "N" ]]; then
            # Ensure stage_0_state_bucket is updated with sanitary BUCKET_NAME
            if [[ -n "$BUCKET_NAME" ]]; then
                sed -i '' "s/stage_0_state_bucket *= *\".*\"/stage_0_state_bucket = \"${BUCKET_NAME}\"/" gemini-stage-1/terraform.tfvars 2>/dev/null || sed -i "s/stage_0_state_bucket *= *\".*\"/stage_0_state_bucket = \"${BUCKET_NAME}\"/" gemini-stage-1/terraform.tfvars
            fi
            return 0
        fi
    fi

    # Retrieve Region from Stage 0 state if not set
    if [[ -z "$REGION" ]]; then
        echo "Retrieving region from state..."
        
        hydrate_from_state
        
        if [[ -z "$REGION" ]]; then
             # Try to get it from the bucket location or default
             REGION="us-central1"
             echo -e "${RED}WARNING: Could not retrieve region from state. Using default: ${REGION}${NC}"
        fi
    fi

    read -p "Enter Gemini Enterprise Domain (e.g., gemini.example.com): " GEMINI_DOMAIN
    
    # Validate DNS
    echo "Validating DNS for ${GEMINI_DOMAIN}..."
    if [[ -z "$STATE_CONTENT" ]]; then
        hydrate_from_state
    fi
    
    LB_IP=$(echo "$STATE_CONTENT" | jq -r '.outputs.gemini_enterprise_ip.value // empty')
    
    if [[ -n "$LB_IP" ]]; then
        CURRENT_IP=$(dig +short "$GEMINI_DOMAIN" | grep "$LB_IP")
        if [[ -n "$CURRENT_IP" ]]; then
             echo -e "${GREEN}DNS Validation Successful: ${GEMINI_DOMAIN} resolves to ${LB_IP}${NC}"
        else
             RESOLVED_IPS=$(dig +short "$GEMINI_DOMAIN" | tr '\n' ' ')
             echo -e "${RED}WARNING: DNS Validation Failed!${NC}"
             echo -e "Expected IP: ${LB_IP}"
             echo -e "Resolved IPs: ${RESOLVED_IPS:-None}"
             echo -e "${YELLOW}Please ensure your DNS A record is correctly pointing to ${LB_IP}.${NC}"
             read -p "Continue anyway? (y/N): " CONFIRM_DNS
             if [[ "$CONFIRM_DNS" != "y" && "$CONFIRM_DNS" != "Y" ]]; then
                 return 1
             fi
        fi
    else
        echo -e "${RED}WARNING: Could not retrieve Load Balancer IP from state. Skipping DNS validation.${NC}"
    fi
    
    if [[ -f "gemini-stage-0/terraform.tfvars" ]]; then
        CERT_MANAGEMENT_CHOICE=$(grep "cert_management_choice" gemini-stage-0/terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
        CUSTOM_DOMAIN=$(grep "custom_domain" gemini-stage-0/terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
    else
        CERT_MANAGEMENT_CHOICE="self_managed"
        CUSTOM_DOMAIN=""
    fi

    if [[ "$CERT_MANAGEMENT_CHOICE" == "google_managed" ]]; then
        echo ""
        echo -e "${YELLOW}Google-managed certificate selected in Stage 0. Skipping manual SSL certificate selection.${NC}"
        SSL_CERT_NAME=""
    else
        # Auto-discover SSL Certificates
        echo ""
        echo "Discovering SSL Certificates in Region ${REGION}..."
        CERTS_JSON=$(gcloud compute ssl-certificates list --filter="region:(${REGION})" --format="json" 2>/dev/null)
        
        if [[ -n "$CERTS_JSON" && "$CERTS_JSON" != "[]" ]]; then
            echo "Available SSL Certificates:"
            echo "$CERTS_JSON" | jq -r '.[] | "\(.name) (\(.type))"' | nl -w2 -s") "
            
            read -p "Select an SSL Certificate [1]: " CERT_SEL
            CERT_SEL=${CERT_SEL:-1}
            
            SSL_CERT_NAME=$(echo "$CERTS_JSON" | jq -r ".[$((CERT_SEL-1))].name")
            echo -e "Selected Certificate: ${YELLOW}${SSL_CERT_NAME}${NC}"
        else
            echo -e "${YELLOW}No SSL Certificates found in region ${REGION}.${NC}"
            read -p "Enter SSL Certificate Name (must exist in GCP): " SSL_CERT_NAME
        fi
    fi

    read -p "Enter Gemini Widget Config ID (from Step 2 output): " GEMINI_CONFIG_ID
    
    cat > gemini-stage-1/terraform.tfvars <<EOF
stage_0_state_bucket = "${BUCKET_NAME}"
gemini_enterprise_domain = "${GEMINI_DOMAIN}"
ssl_certificate_name = "${SSL_CERT_NAME}"
gemini_config_id = "${GEMINI_CONFIG_ID}"
cert_management_choice = "${CERT_MANAGEMENT_CHOICE}"
custom_domain = "${CUSTOM_DOMAIN}"
EOF

    # Add Shared VPC vars if needed (simple check)
    if [[ -n "$SHARED_VPC_NETWORK" ]]; then
        echo "network_name = \"${SHARED_VPC_NETWORK}\"" >> gemini-stage-1/terraform.tfvars
        echo "host_project_id = \"${SHARED_VPC_HOST_PROJECT}\"" >> gemini-stage-1/terraform.tfvars
    fi

    echo -e "${GREEN}Configuration generated in gemini-stage-1/terraform.tfvars${NC}"
    return 0
}

deploy_stage_1() {
    echo ""
    echo -e "${BLUE}--- Deploying Stage 1 ---${NC}"
    
    cd gemini-stage-1
    rm -f backend.tf
    rm -rf .terraform
    
    echo "Initializing Terraform..."
    if ! terraform init -migrate-state -backend-config="bucket=${BUCKET_NAME}" -backend-config="prefix=terraform/state/stage-1"; then
        echo -e "${RED}Terraform Init failed! Please try resolving the error and running the Step again.${NC}"
        cd ..
        pause
        return 1
    fi
    
    echo ""
    echo "Applying Terraform..."
    if ! terraform apply -var-file="terraform.tfvars"; then
        echo -e "${RED}Terraform Apply failed! Please try resolving the error and running the Step again.${NC}"
        cd ..
        pause
        return 1
    fi
    
    cd ..
    echo -e "${GREEN}Stage 1 Deployment Complete!${NC}"
    
    # Post-Deployment: Third Party OAuth Setup
    # We need to check ACL_IDP_TYPE, but it might not be set if we just ran Stage 1.
    # We can try to read it from Stage 0 state if missing.
    if [[ -z "$ACL_IDP_TYPE" ]]; then
         STATE_CONTENT=$(gcloud storage cat "gs://${BUCKET_NAME}/terraform/state/stage-0/default.tfstate" 2>/dev/null || echo "{}")
         ACL_IDP_TYPE=$(echo "$STATE_CONTENT" | jq -r '.outputs.acl_idp_type.value // empty')
         ACL_POOL_NAME=$(echo "$STATE_CONTENT" | jq -r '.outputs.acl_workforce_pool_name.value // empty')
    fi

    if [[ "$ACL_IDP_TYPE" == "THIRD_PARTY" ]]; then
        echo ""
        echo -e "${YELLOW}ACTION REQUIRED: Complete the Identity-Aware Proxy (IAP) configuration manually.${NC}"
        echo -e "Because you selected THIRD_PARTY (Workforce Identity Federation), you must configure the OAuth Client and IAP settings manually."
        
        BACKEND_SERVICE_NAME="${PREFIX}-backend-service"

        echo ""
        echo -e "${YELLOW}Step 1: Create an OAuth Client${NC}"
        echo -e "1. Navigate to APIs & Services > Credentials: ${BLUE}https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}${NC}"
        echo "2. Click 'Create Credentials' > 'OAuth client ID'."
        echo "3. Application type: 'Web application'."
        echo "4. Name: 'Gemini Enterprise IAP Client'."
        echo "5. Click 'Create'. (Do not add redirect URIs yet)."
        echo "6. Copy the 'Client ID' and 'Client Secret'."
        echo -e "${NC}"
        echo ""
        read -p "Press Enter to acknowledge and continue..."

        echo ""
        echo -e "${YELLOW}Step 2: Update Redirect URI${NC}"
        echo "1. Edit the newly created OAuth Client."
        echo -e "2. Add the following Authorized redirect URI (replace [CLIENT_ID] with the actual ID you just copied): ${BLUE}https://iap.googleapis.com/v1/oauth/clientIds/[CLIENT_ID]:handleRedirect${NC}"
        echo "3. Save the changes."
        echo -e "${NC}"
        echo ""
        read -p "Press Enter to acknowledge and continue..."

        echo ""
        echo -e "${YELLOW}Step 3: Configure IAP for Workforce Identity${NC}"
        echo -e "1. Navigate to IAP: ${BLUE}https://console.cloud.google.com/security/iap?project=${PROJECT_ID}${NC}"
        echo -e "2. Locate the Backend Service: ${GREEN}${BACKEND_SERVICE_NAME}${NC}"
        echo "3. Select the \"Settings\" in the 3-dots menu next to the backend service resource."
        echo "4. Select \"Custom OAuth (for specific control, branding, or external users)\" and configure the following:"
        echo "   - OAuth client ID: (Paste from Step 1)"
        echo "   - OAuth client secret: (Paste from Step 1)"
        echo "6. Click 'Save'."
        echo -e "${NC}"
        echo ""
        read -p "Press Enter to acknowledge and continue..."
        echo ""
        echo -e "${GREEN}OAuth and IAP Manual Configuration marked as complete.${NC}"
    fi
    
    echo ""
    echo -e "Welcome to your ${BLUE}G${RED}o${YELLOW}o${BLUE}g${GREEN}l${RED}e${NC} Cloud Gemini Enterprise App! Access your app at ${BLUE}https://${GEMINI_DOMAIN}${NC}"
    pause
}

# --- Main Menu ---

main_menu() {
    while true; do
        clear
        # Attempt to hydrate state to populate variables for menu display
        hydrate_from_state
        
        print_header
        echo -e "Current Project: ${YELLOW}${PROJECT_ID:-None}${NC}"
        echo -e "Deployment Topology: ${YELLOW}${DEPLOYMENT_TYPE_TEXT:-None}${NC}"
        echo "-----------------------------------"
        echo -e "1. ${BLUE}Step 1${NC} - Configure & Deploy Infrastructure (gemini-stage-0)"
        echo -e "2. ${BLUE}Step 2${NC} - Create Gemini Enterprise App (gem4gov-cli)"
        echo -e "3. ${BLUE}Step 3${NC} - Configure & Deploy Load Balancer / Access Policies (gemini-stage-1)"
        echo -e "4. ${YELLOW}Helper Functions${NC}"
        echo -e "5. ${YELLOW}Re-select Deployment Topology / Project${NC}"
        echo -e "6. ${RED}Exit${NC}"
        echo "-----------------------------------"
        read -p "Select an option [1-6]: " OPTION

        case $OPTION in
            1)
                if [[ -z "$PROJECT_ID" ]]; then
                    echo -e "${RED}Please select a project first (Option 5).${NC}"
                    pause
                    continue
                fi
                configure_stage_0 || continue
                deploy_stage_0 || continue
                ;;
            2)
                if [[ -z "$PROJECT_ID" ]]; then
                    echo -e "${RED}Please select a project first (Option 5).${NC}"
                    pause
                    continue
                fi
                configure_gem4gov || continue
                ;;
            3)
                if [[ -z "$PROJECT_ID" ]]; then
                    echo -e "${RED}Please select a project first (Option 5).${NC}"
                    pause
                    continue
                fi
                configure_stage_1 || continue
                deploy_stage_1 || continue
                ;;
            4)
                helper_menu || continue
                ;;
            5)
                auth_and_project_setup || continue
                enable_apis || continue
                select_deployment_type || continue
                discover_infrastructure || continue
                ;;
            6)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid option."
                pause
                ;;
        esac
    done
}
# --- Entry Point ---

check_dependencies
auth_and_project_setup
enable_apis
select_deployment_type
discover_infrastructure
main_menu
