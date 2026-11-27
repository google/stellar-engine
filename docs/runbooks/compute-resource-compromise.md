# Compute resource compromise runbook

Use this runbook to identify, contain, analyze, and recover from compromised Compute Engine virtual machines and Google Kubernetes Engine workloads in Stellar Engine environments on Google Cloud.

| Attribute | Detail |
| :--- | :--- |
| Runbook ID | IR-COMP-001 |
| Last updated | YYYY-MM-DD |
| Owner | Security Operations / Cloud Platform Team |
| Target SLA | Triage: 15m \| Containment: 45m \| Forensics: 2h \| Recovery: 4h |

## 1. Runbook objective

This runbook guides security operators and incident responders through identifying, containing, analyzing, and recovering from compromised Google Kubernetes Engine pods or nodes and Compute Engine virtual machines in Stellar Engine landing zones on Google Cloud.

## 2. Audience and prerequisites

### 2.1 Target audience

- Tier 1, tier 2, and tier 3 Security Operations Center analysts
- Incident responders
- Platform and DevOps engineers

### 2.2 Responder prerequisites

- The `roles/compute.viewer` and `roles/container.viewer` roles for resource scoping.
- The `roles/compute.orgFirewallPolicyAdmin` role to add emergency deny rules to organization or folder hierarchical firewall policies such as `<prefix>-net-default`.
- The `roles/compute.securityAdmin` and `roles/resourcemanager.tagUser` roles to bind quarantine Secure Tags and add deny rules to global or regional network firewall policies such as `<prefix>-<env>-fw-policy-0`, or to apply classic VPC firewall rules and tags when `BEFORE_CLASSIC_FIREWALL` is not active.
- The `roles/container.developer` role or an equivalent Kubernetes RBAC `ClusterRole` binding to relabel pods and apply `NetworkPolicy` resources.
- The `roles/compute.storageAdmin` role to snapshot persistent disks for forensic analysis.

## 3. Operational scope

This runbook applies to all Stellar Engine environments, including FedRAMP High, FedRAMP Moderate, IL4, and IL5 landing zones. The procedures assume Shielded VMs, Workload Identity, and immutable infrastructure managed through Terraform. Note that `compute.requireOsLogin` is enforced by organization policy in FedRAMP High and FedRAMP Moderate deployments, but is skipped by default in IL4 and IL5 custom organization policies.

## 4. Identification and scoping

### 4.1 Detection sources

Monitor these telemetry sources for indicators of compute compromise:

- High-severity Security Command Center findings from Event Threat Detection or Container Threat Detection, such as `Malicious Process execution`, `Cryptomining Domain DNS Request`, and `Reverse Shell`.
- Cloud IDS and Next-Generation Firewall alerts showing lateral movement, command-and-control beacons, or outbound data exfiltration.
- Cloud Billing anomalies showing sudden spikes in Compute Engine CPU utilization or network egress charges.
- Host-based endpoint detection alerts from agents running on virtual machines or GKE nodes.

### 4.2 Verification and triage

1. Identify the exact Google Cloud resource implicated in the alert.
2. Record the resource deployment context:
   - Record the project ID, instance name, zone, internal IP address, attached service account, and network tags for a Compute Engine virtual machine.
   - Record the project ID, cluster name, namespace, pod name, node name, and bound Workload Identity principal for a GKE workload.
3. Inspect Cloud Audit Logs and operating system logs in Logs Explorer to review recent `cloudaudit.googleapis.com` administrative changes and host activity:
   ```text
   resource.type="gce_instance"
   AND resource.labels.instance_id="[INSTANCE_ID]"
   AND logName="projects/[PROJECT_ID]/logs/syslog"
   ```

## 5. Threat containment

Isolate the compromised workload to stop lateral movement and data exfiltration without destroying volatile memory or disk state required for forensic collection.

### 5.1 Virtual machine containment

1. Keep the compromised virtual machine running rather than stopping or restarting it so volatile memory and temporary files remain intact for forensic capture.
2. Quarantine the instance on the network using the mechanism that matches the VPC firewall evaluation order of the environment:
   - In Stage 2a Shared VPCs created by `fast/stages-aw/2-networking-a-fedramp`, `BEFORE_CLASSIC_FIREWALL` evaluates the folder hierarchical firewall policy `<prefix>-net-default` and global network firewall policies such as `<prefix>-hub-fw-policy-0` and `<prefix>-<env>-fw-policy-0` before classic VPC rules, so classic `--tags=ir-quarantine` rules cannot override higher-priority policy allow rules. Resolve the numeric `[PROJECT_NUMBER]` and `[INSTANCE_ID]`, bind a quarantine Secure Tag value to the instance, and add top-priority `INGRESS` and `EGRESS` deny rules targeting that Secure Tag on the global network firewall policy in the network host project, adding matching higher-priority deny rules on `<prefix>-net-default` if an existing hierarchical allow rule would otherwise match:
     ```bash
     # Resolve numeric project number and instance ID required by Resource Manager TagBindings
     PROJECT_NUMBER=$(gcloud projects describe [PROJECT_ID] --format='value(projectNumber)')
     INSTANCE_ID=$(gcloud compute instances describe [INSTANCE_NAME] --zone=[ZONE] --project=[PROJECT_ID] --format='value(id)')
     gcloud resource-manager tags bindings create \
         --parent=//compute.googleapis.com/projects/${PROJECT_NUMBER}/zones/[ZONE]/instances/${INSTANCE_ID} \
         --tag-value=[QUARANTINE_TAG_VALUE_ID] \
         --location=[ZONE]
     gcloud compute network-firewall-policies rules create 1 \
         --firewall-policy=[ENV_FW_POLICY_NAME] \
         --global-firewall-policy \
         --project=[NETWORK_HOST_PROJECT_ID] \
         --direction=INGRESS \
         --action=deny \
         --layer4-configs=all \
         --src-ip-ranges=0.0.0.0/0 \
         --target-secure-tags=[QUARANTINE_TAG_VALUE_ID] \
         --enable-logging
     gcloud compute network-firewall-policies rules create 2 \
         --firewall-policy=[ENV_FW_POLICY_NAME] \
         --global-firewall-policy \
         --project=[NETWORK_HOST_PROJECT_ID] \
         --direction=EGRESS \
         --action=deny \
         --layer4-configs=all \
         --dest-ip-ranges=0.0.0.0/0 \
         --target-secure-tags=[QUARANTINE_TAG_VALUE_ID] \
         --enable-logging
     ```
   - In Stage 2b deployments using `fast/stages-aw/2-networking-b-il5-ngfw` or any VPC using default classic evaluation order without overriding NGFW allow policies, apply the `ir-quarantine` network tag only after verifying that priority `1` VPC firewall rules deny all ingress and egress traffic for `ir-quarantine`:
     ```bash
     gcloud compute instances add-tags [INSTANCE_NAME] --zone=[ZONE] --project=[PROJECT_ID] --tags=ir-quarantine
     ```
3. Remove the instance from load balancer target pools and backend services so it stops receiving production traffic.
4. Block new SSH sessions through OS Login.
5. Disable the attached dedicated service account so the attacker cannot use the virtual machine identity to call Google Cloud APIs.

### 5.2 GKE pod containment

1. Keep the compromised pod running rather than deleting it so the container filesystem and memory state remain available for inspection.
2. Strip routing labels from the pod so it no longer matches the Kubernetes `Service` selector and stops receiving load-balanced traffic:
   ```bash
   kubectl label pod [POD_NAME] -n [NAMESPACE] app- # Removes the 'app' label (adjust to match your routing labels)
   kubectl label pod [POD_NAME] -n [NAMESPACE] incident-response=quarantined
   ```
3. Apply a default-deny `NetworkPolicy` resource targeting the `incident-response=quarantined` label to block all pod ingress and egress traffic.
4. Cordon the underlying GKE node so the scheduler places no new workloads on the potentially affected host:
   ```bash
   kubectl cordon [NODE_NAME]
   ```

## 6. Forensics and analysis

Collect immutable evidence from the isolated workload to determine the initial attack vector, persistence mechanisms, and blast radius.

### 6.1 Virtual machine forensics

1. Snapshot every persistent disk attached to the instance inside an approved Assured Workloads region for offline digital forensics analysis:
   ```bash
   gcloud compute disks snapshot [DISK_NAME] \
       --zone=[ZONE] \
       --storage-location=[REGION] \
       --snapshot-names=ir-snap-[INSTANCE_NAME]-[TIMESTAMP] \
       --project=[PROJECT_ID]
   ```
2. Capture volatile memory on SEV 1 incidents using LiME or an authenticated forensic sidecar over an Identity-Aware Proxy SSH tunnel or dedicated forensics collection agent before terminating the instance, writing the capture to an isolated CMEK-protected Cloud Storage bucket for offline analysis with Volatility. Do not rely on serial console access because `compute.disableSerialPortAccess` is enforced by organization policy.
3. Export the instance metadata to inspect for injected SSH keys or unauthorized startup scripts.

### 6.2 GKE pod forensics

1. Export the full pod YAML manifest to capture environment variables, mounted secrets, and container image digests:
   ```bash
   kubectl get pod [POD_NAME] -n [NAMESPACE] -o yaml > ir-pod-state.yaml
   ```
2. Export standard output and standard error logs from the compromised container:
   ```bash
   kubectl logs [POD_NAME] -n [NAMESPACE] > ir-container-logs.txt
   ```
3. Snapshot the GKE node boot disk using the virtual machine disk snapshot procedure whenever evidence indicates a container escape to the host node.

## 7. Eradication and recovery

Destroy the compromised compute resource after securing forensic artifacts, patch the underlying vulnerability, and redeploy clean workloads through GitOps.

### 7.1 Immutable infrastructure eradication

Replace compromised resources completely rather than attempting in-place cleanup because Stellar Engine enforces immutable infrastructure through Terraform:

1. Delete the compromised pod, node, or virtual machine once disk snapshots and logs are preserved:
   - Delete a GKE pod with `kubectl delete pod [POD_NAME] -n [NAMESPACE]`.
   - Delete a Compute Engine instance with `gcloud compute instances delete [INSTANCE_NAME] --zone=[ZONE] --project=[PROJECT_ID]`.
2. Analyze the collected forensic artifacts to pinpoint the root vulnerability, such as an unpatched container CVE, a server-side request forgery flaw, or leaked credentials.

### 7.2 Workload recovery

1. Patch the vulnerability in source control by updating the `Dockerfile`, dependency manifest such as `requirements.txt`, or base virtual machine image.
2. Commit the fix to the GitOps repository so the trusted CI/CD pipeline, such as Cloud Build or Argo CD, builds and deploys a clean artifact.
3. Monitor the redeployed resources in Cloud Monitoring and Security Command Center for 72 hours to confirm that unauthorized activity does not recur.

## 8. Lessons learned

### 8.1 Post-incident review

1. Conduct a post-incident review within 5 business days with security, DevOps, and application owners.
2. Evaluate whether Security Command Center and web application firewall rules detected the intrusion promptly, and identify any detection gaps.
3. Harden workload defenses based on the affected compute platform:
   - Enforce Binary Authorization on GKE clusters so only signed, vulnerability-scanned container images deploy, and apply Pod Security Admission policies to block privileged containers.
   - Enforce automated OS Patch Management schedules on Compute Engine virtual machines and require Identity-Aware Proxy TCP forwarding for SSH rather than public IP addresses.
4. Update this runbook with any additional commands or forensic tooling used during the incident.
