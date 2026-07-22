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

#### Shared Services Deploy Script
#### Deploys shared-services stage resources (e.g., BCAP) independently of stellar-deploy.sh.
#### Prerequisites: Stages 0-5 must already be deployed via stellar-deploy.sh.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd "${SCRIPT_DIR}" || exit

# --- Helper Functions (from stellar-deploy.sh) ---

cleanup() {
  local resourceFile=${1}
  local statusFile=${2}
  if [[ -f $resourceFile ]]; then
    rm "$resourceFile"
  fi
  if [[ -f $statusFile ]]; then
    rm "$statusFile"
  fi
}

tfRun() {
  local tf_cmd="$1"
  local resources_file="$2"
  local status_file="$3"

  if [[ ! -d $SCRIPT_DIR/tmp ]]; then
    mkdir -p "${SCRIPT_DIR}"/tmp
  fi

  local cmd="terraform $tf_cmd"

  eval "$cmd" 2>&1| tee >(sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' >> "$resources_file")
  local tf_exit_code=${PIPESTATUS[0]}
  echo "$tf_exit_code" > "$status_file"
}

errorChecking() {
  local tf_cmd="$1"
  local resource_file="$2"
  local status_file="$3"

  local upper_cmd=""
  upper_cmd=$(upper "${tf_cmd%% *}")

  while [[ $(cat "$statusFile") -ne 0 ]]; do
    echo -e "\n--- ${upper_cmd} FAILED ---"
    if grep -q "BigQuery service account: googleapi: Error 403: Request is disallowed by organization's constraints/gcp.restrictServiceUsage constraint" "$resource_file"; then
      echo -e "\n--- ${upper_cmd} FAILED WITH BQ USAGE CONSTRAINT ERROR ---"
      if promptUser "Would you like to update the Assured Workloads folder to allow BigQuery and Cloud KMS?"; then
        ("${SCRIPT_DIR}/allow_bq.sh")
        sleep 120
      fi
      return 1
    fi
    if promptUser "Would you like to see what the terraform errors are?"; then
      awk '/[Ee]rror/{p=1;print;next} p' "$resource_file"
    fi
    if promptUser "Do you want to re-run 'terraform ${tf_cmd}' now?"; then
      echo "Initiating manual 'terraform ${tf_cmd}'..."
      tfRun "$tf_cmd" "$resource_file" "$status_file"
    else
      echo "Skipping 'terraform ${tf_cmd}'."
      return 1
    fi
  done
  cleanup "$resource_file" "$status_file"
}

runTerraformCommand() {
  local tf_cmd="$1"
  local resource_file="$2"
  local status_file="$3"

  tfRun "$tf_cmd" "$resource_file" "$status_file"

  if [[ -f "$status_file" ]] && [[ $(cat "$status_file") -ne 0 ]]; then
    errorChecking "$tf_cmd" "$resource_file" "$status_file"
  else
    cleanup "$resource_file" "$status_file"
  fi
}

upper() {
  if [[ -n "$1" ]]; then
    echo "${1}" | tr '[:lower:]' '[:upper:]'
  fi
  return 0
}

compliance_regime_mapping() {
  case "${1}" in
    "COMPLIANCE_REGIME_UNSPECIFIED")
      echo "cru"
      ;;
    "IL2")
      echo "il2"
      ;;
    "IL4")
      echo "il4"
      ;;
    "IL5")
      echo "il5"
      ;;
    "FEDRAMP_HIGH")
      echo "frh"
      ;;
    "FEDRAMP_MODERATE")
      echo "frm"
      ;;
    *)
      echo "${1}" | tr '[:upper:]' '[:lower:]'
      ;;
  esac
}

promptUser() {
  echo -e "\n${1} Type 's' to skip, or 'c' to continue'."
  read -r choice
  if [[ "$choice" == "s" ]]; then
    return 255 # Won't run command
  else
    shift
    for i in "$@"; do
      eval "$i"
    done
  fi
}

# --- Configuration ---

if [[ ! -f "${SCRIPT_DIR}/config.env" ]]; then
  echo "ERROR: config.env not found in ${SCRIPT_DIR}."
  echo "Please ensure stages 0-5 have been deployed via stellar-deploy.sh first."
  echo "Copy config.env.sample to config.env and configure it for your deployment."
  exit 1
fi

# shellcheck source=automation/config.env.sample
source "${SCRIPT_DIR}/config.env"
IFS=',' read -r -a REGIONS_ARRAY <<< "$REGIONS"

COMPLIANCE_REGIME_ABBREVIATION=$(compliance_regime_mapping "${COMPLIANCE_REGIME}")
GCS_BUCKET="gs://${PREFIX}-${COMPLIANCE_REGIME_ABBREVIATION}-prod-iac-core-outputs"
BCAP_DIR="${SCRIPT_DIR}/../fast/stages-aw/shared-services/bcap"
NTP_DIR="${SCRIPT_DIR}/../fast/stages-aw/shared-services/ntp"
DNS_DIR="${SCRIPT_DIR}/../fast/stages-aw/shared-services/dns"
SMTP_DIR="${SCRIPT_DIR}/../fast/stages-aw/shared-services/smtp"
AD_DIR="${SCRIPT_DIR}/../fast/stages-aw/shared-services/ad"

# --- Shared Services - BCAP Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - BCAP Deployment"
echo "#######################################################"
echo ""
echo "This script deploys the Boundary Cloud Access Point (BCAP) infrastructure."
echo "Prerequisites: Stages 0-2 must already be deployed via stellar-deploy.sh."

if promptUser "Shared Services - BCAP -"; then
  cd "${BCAP_DIR}" || exit

  resourceFile="${SCRIPT_DIR}/tmp/shared-services-bcap_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/shared-services-bcap_tf_status_$$"

  if promptUser "Would you like to pull the remote tfvars files created in Stage 3?" "${cmd[@]}"; then
    gcloud storage cp "${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json" ./
  fi

  if promptUser "Would you like to pull the shared-services providers file from GCS?"; then
    gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
  fi

  REGIONS_CONFIG=$(printf '%s", "' "${REGIONS_ARRAY[@]}" | sed 's/", "$//')
  REGIONS_CONFIG="[\"$REGIONS_CONFIG\"]"

  if promptUser "Would you to generate a new tfvars file?"; then
    yq -o=json '.' data/config.yml > terraform.tfvars.json
    jq '.bcap' 3-networking-shared-services.auto.tfvars.json > networking-bcap.auto.tfvars.json
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init -backend-config=prefix=bcap" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform a terraform plan?"; then
    runTerraformCommand "plan" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo ""
  echo "Congratulations, you have completed the BCAP deployment!"
  echo ""
  echo "Post-Apply Steps:"
  echo "  1. Retrieve pairing keys: terraform output -json pairing_keys"
  echo "  2. Provide pairing keys to the BCAP provider (DISA/Google BCAP Team)"
  echo "  3. Once attachments are active, configure BGP peering on Cloud Routers"
  echo ""
fi

# --- Shared Services - NTP Relay Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - NTP Relay Deployment"
echo "#######################################################"
echo ""
echo "This script deploys STIG-compliant NTP relay VMs that sync to USNO."
echo "Prerequisites: Stages 0-2 must already be deployed via stellar-deploy.sh."

if promptUser "Shared Services - NTP Relay -"; then
  cd "${NTP_DIR}" || exit

  resourceFile="${SCRIPT_DIR}/tmp/shared-services-ntp_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/shared-services-ntp_tf_status_$$"

  cmd=(
    "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
    "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
  )
  promptUser "Would you like to pull the remote tfvars files created in Stage 1 and Stage 3?" "${cmd[@]}"

  if promptUser "Would you like to pull the shared-services providers file from GCS?"; then
    gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
  fi

  if promptUser "Would you to generate a new tfvars file?"; then
    yq -o=json '.' data/config.yml > ntp-config.auto.tfvars.json
    cat <<EOF >ntp-global.auto.tfvars
prefix = "${PREFIX}"
EOF
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init -backend-config=prefix=ntp" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform a terraform plan?"; then
    runTerraformCommand "plan" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo ""
  echo "Congratulations, you have completed the NTP Relay deployment!"
  echo ""
  echo "Post-Apply Steps:"
  echo "  1. Retrieve relay IP: terraform output relay_ip"
  echo "  2. Relay IP has been published to GCS at:"
  echo "     ${GCS_BUCKET}/tfvars/shared-services-ntp.auto.tfvars.json"
  echo "  3. Configure spoke VMs' /etc/chrony.conf to point at the relay IPs:"
  echo "     server <relay-ip> iburst maxpoll 6"
  echo "  4. Remove any metadata.google.internal or pool.ntp.org NTP sources"
  echo ""
fi

# --- Shared Services - DNS Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - DNS Deployment"
echo "#######################################################"
echo ""
echo "This script deploys IL5-compliant DNS forwarding zones that route"
echo "domain-specific queries to the enterprise DNS resolver in Azure via VPN."
echo "Prerequisites: Stages 0-3 and 3-vpn must already be deployed."

if promptUser "Shared Services - DNS -"; then
  cd "${DNS_DIR}" || exit

  resourceFile="${SCRIPT_DIR}/tmp/shared-services-dns_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/shared-services-dns_tf_status_$$"

  cmd=(
    "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
    "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
  )
  promptUser "Would you like to pull the remote tfvars files created in Stage 1 and Stage 3?" "${cmd[@]}"

  if promptUser "Would you like to pull the shared-services providers file from GCS?"; then
    gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
  fi

  if promptUser "Would you to generate a new tfvars file?"; then
    yq -o=json '.' data/config.yml > dns-config.auto.tfvars.json
    cat <<EOF >dns-global.auto.tfvars
prefix = "${PREFIX}"
EOF
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init -backend-config=prefix=dns" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform a terraform plan?"; then
    runTerraformCommand "plan" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo ""
  echo "Congratulations, you have completed the DNS deployment!"
  echo ""
  echo "Post-Apply Steps:"
  echo "  1. Forwarding zone info has been published to GCS at:"
  echo "     ${GCS_BUCKET}/tfvars/shared-services-dns.auto.tfvars.json"
  echo "  2. Verify forwarding from a GCP VM:"
  echo "     dig test.example.com @35.199.192.0"
  echo "  3. Verify internal DNS still works:"
  echo "     dig vm-name.us-east4-a.c.project.internal"
  echo ""
fi
# --- Shared Services - SMTP Relay Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - SMTP Relay Deployment"
echo "#######################################################"
echo ""
echo "This script deploys a STIG-compliant Postfix SMTP relay (smarthost)"
echo "that relays all outbound email through the DISA EESG via BCAP."
echo "Prerequisites: Stages 0-3 must already be deployed via stellar-deploy.sh."

if promptUser "Shared Services - SMTP Relay -"; then
  cd "${SMTP_DIR}" || exit

  resourceFile="${SCRIPT_DIR}/tmp/shared-services-smtp_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/shared-services-smtp_tf_status_$$"

  cmd=(
    "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
    "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
  )
  promptUser "Would you like to pull the remote tfvars files created in Stage 1 and Stage 3?" "${cmd[@]}"

  if promptUser "Would you like to pull the shared-services providers file from GCS?"; then
    gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
  fi

  if promptUser "Would you to generate a new tfvars file?"; then
    yq -o=json '.' data/config.yml > smtp-config.auto.tfvars.json
    # Override encryption_key with the SMTP-specific KMS key from the shared-services output.
    # The shared-services tfvars exports encryption_key (NTP) and smtp_encryption_key (SMTP).
    jq -n --arg key "$(jq -r '.smtp_encryption_key' 3-networking-shared-services.auto.tfvars.json)" \
      '{encryption_key: $key}' > smtp-encryption.auto.tfvars.json
    cat <<EOF >smtp-global.auto.tfvars
prefix = "${PREFIX}"
EOF
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init -backend-config=prefix=smtp" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform a terraform plan?"; then
    runTerraformCommand "plan" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo ""
  echo "Congratulations, you have completed the SMTP Relay deployment!"
  echo ""
  echo "Post-Apply Steps:"
  echo "  1. Retrieve relay IP: terraform output relay_ip"
  echo "  2. Relay IP has been published to GCS at:"
  echo "     ${GCS_BUCKET}/tfvars/shared-services-smtp.auto.tfvars.json"
  echo "  3. Configure spoke applications to relay mail through:"
  echo "     SMTP_HOST=<relay-ip> SMTP_PORT=25"
  echo "  4. Verify from a spoke VM: telnet <relay-ip> 25"
  echo ""
fi

# --- Shared Services - SMTP Relay Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - SMTP Relay Deployment"
echo "#######################################################"
echo ""
echo "This script deploys a STIG-compliant Postfix SMTP relay (smarthost)"
echo "that relays all outbound email through the DISA EESG via BCAP."
echo "Prerequisites: Stages 0-3 must already be deployed via stellar-deploy.sh."

if promptUser "Shared Services - SMTP Relay -"; then
  cd "${SMTP_DIR}" || exit

  resourceFile="${SCRIPT_DIR}/tmp/shared-services-smtp_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/shared-services-smtp_tf_status_$$"

  cmd=(
    "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
    "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
  )
  promptUser "Would you like to pull the remote tfvars files created in Stage 1 and Stage 3?" "${cmd[@]}"

  if promptUser "Would you like to pull the shared-services providers file from GCS?"; then
    gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
  fi

  if promptUser "Would you to generate a new tfvars file?"; then
    yq -o=json '.' data/config.yml > smtp-config.auto.tfvars.json
    # Override encryption_key with the SMTP-specific KMS key from the shared-services output.
    # The shared-services tfvars exports encryption_key (NTP) and smtp_encryption_key (SMTP).
    jq -n --arg key "$(jq -r '.smtp_encryption_key' 3-networking-shared-services.auto.tfvars.json)" \
      '{encryption_key: $key}' > smtp-encryption.auto.tfvars.json
    cat <<EOF >smtp-global.auto.tfvars
prefix = "${PREFIX}"
EOF
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init -backend-config=prefix=smtp" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform a terraform plan?"; then
    runTerraformCommand "plan" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo ""
  echo "Congratulations, you have completed the SMTP Relay deployment!"
  echo ""
  echo "Post-Apply Steps:"
  echo "  1. Retrieve relay IP: terraform output relay_ip"
  echo "  2. Relay IP has been published to GCS at:"
  echo "     ${GCS_BUCKET}/tfvars/shared-services-smtp.auto.tfvars.json"
  echo "  3. Configure spoke applications to relay mail through:"
  echo "     SMTP_HOST=<relay-ip> SMTP_PORT=25"
  echo "  4. Verify from a spoke VM: telnet <relay-ip> 25"
  echo ""
fi

# --- Shared Services - Active Directory Domain Controller Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - Active Directory Domain Controller Deployment"
echo "#######################################################"
echo ""
echo "This script deploys a STIG-compliant Active Directory Domain Controller"
echo "that replicates from the the Domain Controllers in Azure."
echo "Prerequisites: Stages 0-3 must already be deployed via stellar-deploy.sh."

if promptUser "Shared Services - Active Directory -"; then
  cd "${AD_DIR}" || exit

  resourceFile="${SCRIPT_DIR}/tmp/shared-services-ad_tf_resources_$$"
  statusFile="${SCRIPT_DIR}/tmp/shared-services-ad_tf_status_$$"

  cmd=(
    "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
    "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
  )
  promptUser "Would you like to pull the remote tfvars files created in Stage 1 and Stage 3?" "${cmd[@]}"

  if promptUser "Would you like to pull the shared-services providers file from GCS?"; then
    gcloud storage cp "${GCS_BUCKET}/providers/shared-services-providers.tf" ./
  fi

  if promptUser "Would you to generate a new tfvars file?"; then
    yq -o=json '.' data/config.yml > ad-config.auto.tfvars.json
    cat <<EOF >ad-global.auto.tfvars
prefix = "${PREFIX}"
EOF
  fi

  if promptUser "Would you like to perform the terraform init?"; then
    runTerraformCommand "init -backend-config=prefix=ad" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform a terraform plan?"; then
    runTerraformCommand "plan" "$resourceFile" "$statusFile"
  fi

  if promptUser "Would you like to perform the terraform apply?"; then
    runTerraformCommand "apply" "$resourceFile" "$statusFile"
  fi

  echo ""
  echo "Congratulations, you have completed the Active Directory Domain Controller deployment!"
  echo ""
  echo "1. Hand off networking to Palo Alto / Security Team"
  echo "   Provide the provisioned GCP DC IPs above to the firewall administrators."
  echo "   Request ingress/egress policy mapping to authorize AD traffic to/from Azure."
  echo ""
  echo "2. Stage Google Cloud Subnet in Azure Active Directory"
  echo "   Coordinated with the Azure AD identity team to open 'dssite.msc'."
  echo "   Map the GCP Subnet CIDR block directly to a new"
  echo "   Active Directory Site object (e.g., 'GCP-Region-Shared-Services')."
  echo ""
  echo "3. Execute Active Directory Replica Promotion"
  echo "   RDP to the newly provisioned Windows instances using approved secure access."
  echo "   Verify the local NTP clock is actively syncing against NTP Server."
  echo "   Run the AD replica promotion wizard or utilize the Offline Domain Join (.blob)"
  echo "   file generated by the primary forest authorities."
  echo ""
  echo "4. Verify Replication Health with Azure"
  echo "   From an administrative PowerShell terminal on the new GCP DCs, run:"
  echo "     > repadmin /showrepl"
  echo "   Verify all inbound neighbor statuses return SUCCESS."
  echo "========================================================================="
  echo ""
fi

# --- Shared Services - ACAS (Assured Compliance Assessment Solution) Deployment ---

echo -e "\n#######################################################"
echo "  Shared Services - ACAS Deployment"
echo "#######################################################"
echo ""
echo "This script deploys the ACAS solution (Image Factory, Nessus Scanner, and SecurityCenter)."
echo "Prerequisites: Stages 0-3 must already be deployed via stellar-deploy.sh."

if promptUser "Shared Services - ACAS -"; then
  ACAS_DIR="${SCRIPT_DIR}/../fast/stages-aw/shared-services/acas"

  # --------------------------------------------------------
  # A. ACAS Image Factory
  # --------------------------------------------------------
  if promptUser "Deploy ACAS Component [1/3]: Image Factory?"; then
    cd "${ACAS_DIR}/image-factory" || exit

    resourceFile="${SCRIPT_DIR}/tmp/shared-services-acas-factory_tf_resources_$$"
    statusFile="${SCRIPT_DIR}/tmp/shared-services-acas-factory_tf_status_$$"

    cmd=(
      "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
      "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
      "gcloud storage cp ${GCS_BUCKET}/providers/shared-services-providers.tf ./"
    )
    promptUser "Pull remote tfvars and providers from GCS?" "${cmd[@]}"

    if promptUser "Generate local tfvars file from centralized config.yml?"; then
      yq -o=json '.image_factory' "${ACAS_DIR}/data/config.yml" > acas-factory.auto.tfvars.json
      cat <<EOF >acas-global.auto.tfvars
prefix = "${PREFIX}"
EOF
    fi

    if promptUser "Pull ACAS RPM packages from GCS staging?"; then
      mkdir -p rpms
      # RPM Ingestion Check
      if ! gcloud storage ls "${GCS_BUCKET}/acas-staging/*.rpm" &>/dev/null; then
        echo -e "\n========================================================================="
        echo -e " [!] CONFIGURATION ERROR: No ACAS RPMs found in GCS staging!"
        echo -e "========================================================================="
        echo " Path Checked: ${GCS_BUCKET}/acas-staging/"
        echo ""
        echo " Please download the RHEL8 RPMs from the DoD Patch Repository:"
        echo "   -> https://patches.csd.disa.mil (CAC required)"
        echo ""
        echo " Then upload them to your GCS outputs bucket using this command:"
        echo "   $ gcloud storage cp *.rpm ${GCS_BUCKET}/acas-staging/"
        echo ""
        echo " For detailed instructions, refer to: "
        echo "   fast/stages-aw/shared-services/acas/README.md"
        echo "========================================================================="
        exit 1
      fi
      gcloud storage cp "${GCS_BUCKET}/acas-staging/*.rpm" ./rpms/
    fi

    if promptUser "Perform terraform init?"; then
      runTerraformCommand "init -backend-config=prefix=acas-factory" "$resourceFile" "$statusFile"
    fi
    if promptUser "Perform terraform plan?"; then
      runTerraformCommand "plan" "$resourceFile" "$statusFile"
    fi
    if promptUser "Perform terraform apply?"; then
      runTerraformCommand "apply" "$resourceFile" "$statusFile"
    fi
  fi

  # --------------------------------------------------------
  # B. ACAS Nessus Scanner
  # --------------------------------------------------------
  if [[ $(yq '.scanner_deployment.enable' "${ACAS_DIR}/data/config.yml") == "true" ]]; then
    if promptUser "Deploy ACAS Component [2/3]: Nessus Scanner VM(s)?"; then
      cd "${ACAS_DIR}/scanner" || exit

      resourceFile="${SCRIPT_DIR}/tmp/shared-services-acas-scanner_tf_resources_$$"
      statusFile="${SCRIPT_DIR}/tmp/shared-services-acas-scanner_tf_status_$$"

      cmd=(
        "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
        "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
        "gcloud storage cp ${GCS_BUCKET}/providers/shared-services-providers.tf ./"
      )
      promptUser "Pull remote tfvars and providers from GCS?" "${cmd[@]}"

      if promptUser "Generate local tfvars file from centralized config.yml?"; then
        yq -o=json '.scanner_deployment' "${ACAS_DIR}/data/config.yml" | jq 'del(.enable)' > acas-scanner.auto.tfvars.json
        cat <<EOF >acas-global.auto.tfvars
prefix = "${PREFIX}"
EOF
      fi

      if promptUser "Perform terraform init?"; then
        runTerraformCommand "init -backend-config=prefix=acas-scanner" "$resourceFile" "$statusFile"
      fi
      if promptUser "Perform terraform plan?"; then
        runTerraformCommand "plan" "$resourceFile" "$statusFile"
      fi
      if promptUser "Perform terraform apply?"; then
        runTerraformCommand "apply" "$resourceFile" "$statusFile"
      fi
    fi
  else
    echo -e "\n--- ACAS Scanner Deployment is disabled in config.yml. Skipping. ---"
  fi

  # --------------------------------------------------------
  # C. ACAS SecurityCenter
  # --------------------------------------------------------
  if [[ $(yq '.securitycenter_deployment.enable' "${ACAS_DIR}/data/config.yml") == "true" ]]; then
    if promptUser "Deploy ACAS Component [3/3]: SecurityCenter VM?"; then
      cd "${ACAS_DIR}/securitycenter" || exit

      resourceFile="${SCRIPT_DIR}/tmp/shared-services-acas-sc_tf_resources_$$"
      statusFile="${SCRIPT_DIR}/tmp/shared-services-acas-sc_tf_status_$$"

      cmd=(
        "gcloud storage cp ${GCS_BUCKET}/tfvars/1-assured-workload.auto.tfvars.json ./"
        "gcloud storage cp ${GCS_BUCKET}/tfvars/3-networking-shared-services.auto.tfvars.json ./"
        "gcloud storage cp ${GCS_BUCKET}/providers/shared-services-providers.tf ./"
      )
      promptUser "Pull remote tfvars and providers from GCS?" "${cmd[@]}"

      if promptUser "Generate local tfvars file from centralized config.yml?"; then
        yq -o=json '.securitycenter_deployment' "${ACAS_DIR}/data/config.yml" | jq 'del(.enable)' > acas-sc.auto.tfvars.json
        cat <<EOF >acas-global.auto.tfvars
prefix = "${PREFIX}"
EOF
      fi

      if promptUser "Perform terraform init?"; then
        runTerraformCommand "init -backend-config=prefix=acas-sc" "$resourceFile" "$statusFile"
      fi
      if promptUser "Perform terraform plan?"; then
        runTerraformCommand "plan" "$resourceFile" "$statusFile"
      fi
      if promptUser "Perform terraform apply?"; then
        runTerraformCommand "apply" "$resourceFile" "$statusFile"
      fi
    fi
  else
    echo -e "\n--- ACAS SecurityCenter Deployment is disabled in config.yml. Skipping. ---"
  fi

  echo ""
  echo "Congratulations, you have completed the ACAS Shared Service deployment!"
  echo ""
fi