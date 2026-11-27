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

# Cloud Build configuration template for RHEL 9 golden images.
# Executes exclusively inside a private Cloud Build worker pool using a
# SHA-256 digest-pinned Artifact Registry builder image, reaches the
# ephemeral Shielded VM over private VPC peering (--internal-ip) with
# 1-hour expiring OS Login keys, deletes the ephemeral builder VM exactly
# once on EXIT, INT, or TERM, configures Google Guest Agent run_dir to
# bypass /tmp noexec hardening, and stamps the configured guest OS features
# (SEV_CAPABLE, UEFI_COMPATIBLE, and GVNIC by default) on the captured image.

steps:
  - name: "${builder_image_digest}"
    id: "write-hardening-script"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        set -euo pipefail
        cat > /workspace/harden-rhel9.sh << 'EOF'
        #!/bin/bash
        set -euo pipefail

        echo "Starting RHEL 9 guest-agent hardening scaffold."
        cat /etc/redhat-release

        # Ensure host firewall remains enabled on the golden image.
        systemctl enable firewalld || true

        # Redirect Google Guest Agent startup script execution away from /tmp
        # so CIS and DISA STIG /tmp noexec mount hardening does not break
        # startup-script execution on downstream VMs.
        run_dir="/opt/google-startup-scripts"
        cfg="/etc/default/instance_configs.cfg"
        install -d -m 0750 -o root -g root "$$${run_dir}"
        if command -v restorecon >/dev/null 2>&1; then
          restorecon -Rv "$$${run_dir}" || true
        fi

        install -d -m 0755 -o root -g root /etc/default
        touch "$$${cfg}"

        if grep -q '^\[MetadataScripts\]' "$$${cfg}"; then
          pat='^[[:space:]]*run_dir[[:space:]]*=.*'
          sed_expr="s|$$${pat}|run_dir = $$${run_dir}|"
          if sed -n '/^\[MetadataScripts\]/,/^\[/p' "$$${cfg}" \
            | grep -q '^[[:space:]]*run_dir[[:space:]]*='; then
            sed -i "/^\[MetadataScripts\]/,/^\[/ $$${sed_expr}" "$$${cfg}"
          else
            sed -i \
              "/^\[MetadataScripts\]/a run_dir = $$${run_dir}" \
              "$$${cfg}"
          fi
        else
          printf '\n[MetadataScripts]\nrun_dir = %s\n' "$$${run_dir}" \
            >> "$$${cfg}"
        fi

        # Write only the minimal MetadataScripts override stanza to the
        # template file so google-guest-agent package upgrades retain run_dir
        # without freezing unrelated vendor defaults.
        printf '[MetadataScripts]\nrun_dir = %s\n' "$$${run_dir}" \
          > /etc/default/instance_configs.cfg.template
        chmod 0644 "$$${cfg}" \
          /etc/default/instance_configs.cfg.template

        echo "Completed RHEL 9 guest-agent hardening scaffold."
        EOF
        chmod 0750 /workspace/harden-rhel9.sh

  - name: "${builder_image_digest}"
    id: "build-and-capture-image"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        set -euo pipefail

        INSTANCE_NAME="rhel9-stig-builder-$${BUILD_ID}"
        IMAGE_NAME="$${_IMAGE_NAME_PREFIX}-$${BUILD_ID}"
        cleanup_done=0

        # Delete the builder VM and its CMEK boot disk exactly once on exit,
        # failure, interrupt, or termination. EXIT keeps the original exit
        # status; INT and TERM exit with the conventional 130 and 143.
        cleanup() {
          local status="$$${1:-$$?}"
          trap '' INT TERM
          trap - EXIT
          if [ "$$${cleanup_done}" -eq 0 ]; then
            cleanup_done=1
            gcloud compute instances delete "$$${INSTANCE_NAME}" \
              --project="$${_PROJECT_ID}" \
              --zone="$${_ZONE}" \
              --quiet || true
          fi
          exit "$$${status}"
        }
        trap cleanup EXIT
        trap 'cleanup 130' INT
        trap 'cleanup 143' TERM

        gcloud compute instances create "$$${INSTANCE_NAME}" \
          --project="$${_PROJECT_ID}" \
          --zone="$${_ZONE}" \
          --machine-type="$${_BUILDER_MACHINE_TYPE}" \
%{ if builder_confidential_compute_type != null ~}
          --confidential-compute-type=${builder_confidential_compute_type} \
%{ if builder_confidential_compute_type == "SEV_SNP" ~}
          --min-cpu-platform="AMD Milan" \
%{ endif ~}
%{ endif ~}
          --image="$${_BASE_IMAGE}" \
          --boot-disk-size=50GB \
          --boot-disk-type=pd-ssd \
          --boot-disk-kms-key="$${_KMS_KEY}" \
          --subnet="$${_SUBNETWORK}" \
          --no-address \
          --no-service-account \
          --no-scopes \
          --shielded-secure-boot \
          --shielded-vtpm \
          --shielded-integrity-monitoring \
          --maintenance-policy=TERMINATE \
          --tags=image-builder \
          --metadata=enable-oslogin=TRUE,block-project-ssh-keys=TRUE

        echo "Waiting for private SSH readiness on ephemeral builder VM."
        # A 10-second connect timeout and batch mode bound each probe, so 30
        # attempts against a dropped TCP 22 path fail in roughly 10 to 15
        # minutes, well inside the default 3600s build timeout.
        attempt=1
        ssh_ready=0
        while [ "$$${attempt}" -le 30 ]; do
          if gcloud compute ssh "$$${INSTANCE_NAME}" \
            --project="$${_PROJECT_ID}" \
            --zone="$${_ZONE}" \
            --internal-ip \
            --ssh-key-expire-after=1h \
            --ssh-flag=-oConnectTimeout=10 \
            --ssh-flag=-oBatchMode=yes \
            --quiet \
            --command="echo 'SSH Ready'"; then
            echo "Private SSH connection established."
            ssh_ready=1
            break
          fi
          echo "Attempt $$${attempt}/30 failed; retrying in 10 seconds."
          attempt=$$((attempt + 1))
          sleep 10
        done

        if [ "$$${ssh_ready}" -ne 1 ]; then
          echo "ERROR: Timed out waiting for internal SSH readiness." >&2
          exit 1
        fi

        gcloud compute scp /workspace/harden-rhel9.sh \
          "$$${INSTANCE_NAME}:/tmp/harden-rhel9.sh" \
          --project="$${_PROJECT_ID}" \
          --zone="$${_ZONE}" \
          --internal-ip \
          --ssh-key-expire-after=1h \
          --quiet

        # shellcheck disable=SC2016
        gcloud compute ssh "$$${INSTANCE_NAME}" \
          --project="$${_PROJECT_ID}" \
          --zone="$${_ZONE}" \
          --internal-ip \
          --ssh-key-expire-after=1h \
          --quiet \
          --command='sudo bash /tmp/harden-rhel9.sh;
            status=$$?; rm -f /tmp/harden-rhel9.sh; exit $$status'

        gcloud compute instances stop "$$${INSTANCE_NAME}" \
          --project="$${_PROJECT_ID}" \
          --zone="$${_ZONE}" \
          --quiet

        gcloud compute images create "$$${IMAGE_NAME}" \
          --project="$${_PROJECT_ID}" \
          --source-disk="$$${INSTANCE_NAME}" \
          --source-disk-zone="$${_ZONE}" \
          --family="$${_IMAGE_FAMILY}" \
          --kms-key="$${_KMS_KEY}" \
          --storage-location="$${_REGION}" \
          --guest-os-features="$${_GUEST_OS_FEATURES}" \
          --description="RHEL 9 STIG image built by Cloud Build $${BUILD_ID}."
    waitFor:
      - "write-hardening-script"

substitutions:
  _BASE_IMAGE: "${base_image}"
  _BUILDER_MACHINE_TYPE: "${builder_machine_type}"
  _GUEST_OS_FEATURES: "${guest_os_features}"
  _IMAGE_FAMILY: "${image_family}"
  _IMAGE_NAME_PREFIX: "${image_name_prefix}"
  _KMS_KEY: "${kms_key_id}"
  _PROJECT_ID: "${project_id}"
  _REGION: "${region}"
  _SUBNETWORK: "${builder_subnetwork}"
  _ZONE: "${builder_zone}"

serviceAccount: "projects/${project_id}/serviceAccounts/${builder_sa_email}"
timeout: "${build_timeout}"
options:
  logging: CLOUD_LOGGING_ONLY
  pool:
    name: "${worker_pool_id}"
