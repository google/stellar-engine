# Incident Response Runbook: Compute Resource Compromise

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-COMP-001 |
| **Version** | {{ VERSION }} |
| **Last Updated** | {{ DATE }} |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | [CONFIG_REQUIRED: organization-defined triage, containment, forensics, and recovery targets, e.g., Triage: 15m \| Containment: 45m \| Forensics: 2h \| Recovery: 4h] |


> [!NOTE]
> **SIEM & Threat Detection Tooling**:
> Threat monitoring and security operations are driven by the services enabled in the environment configuration:
> - **Cloud-Native Posture & Threat Detection**: Where Security Command Center (SCC) or Google Cloud SecOps (Chronicle) is enabled, Event Threat Detection (ETD) and Security Health Analytics (SHA) provide native cloud threat alerts. In <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> enclaves, SCC is not a telemetry source unless the Authorizing Official has approved an exception to policy.
> - **Centralized SIEM / CSSP Integration**: Telemetry and audit trails route via Cloud Logging export sinks to the configured external CSSP / SIEM (e.g. {{ CSSP_PROVIDER }}, {{ EXTERNAL_SIEM }}) for centralized 24/7 security monitoring.

> [!NOTE]
> **Lifecycle alignment**: NIST SP 800-61 Rev. 3 (April 2025) organizes incident response under the NIST CSF 2.0 Functions. The phases in this runbook map as follows: Phase 1 (Identification & Scoping) to Detect (DE.AE) and Respond (RS.MA, RS.AN, RS.CO); Phase 2 (Containment) to Respond (RS.MI); Phase 3 (Forensics and Analysis) to Respond (RS.AN); Phase 4 (Eradication and Recovery) to Respond (RS.MI) and Recover (RC.RP, RC.CO); Phase 5 (Lessons Learned) to Identify (ID.IM).

{{ DISCOVERED_ENVIRONMENT_CONTEXT }}

## 1. Objective
This runbook provides a structured, actionable process for Security Operators and Incident Responders to identify, contain, analyze, and recover from incidents involving the compromise of compute resources—specifically Google Kubernetes Engine (GKE) Pods/Nodes or Compute Engine (GCE) Virtual Machines—within the {{ SYSTEM_NAME }} cloud architecture on {{ CLOUD_PROVIDER }} ({{ CSP_ABBR }}).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts (L1/L2/L3)
* Incident Responders
* Platform / DevOps Engineers

**Prerequisites for Responders:**
* **Audit & Log Inspection:** `roles/logging.viewer` and `roles/logging.privateLogViewer` for scoping and log analysis.
* **Security & Posture Management (where SCC is enabled):** `roles/securitycenter.adminViewer`, `roles/securitycenter.findingsViewer`, or `roles/securitycenter.admin` on the {{ ORGANIZATION }} Organization.
* **Compute & Workload Inspection:** `roles/compute.viewer` and `roles/container.viewer` for scoping.
* `roles/compute.securityAdmin` to modify network tags and firewalls for VM containment.
* `roles/container.developer` or equivalent RBAC `ClusterRole` to manipulate Pods and apply NetworkPolicies.
* `roles/compute.storageAdmin` to snapshot disks for forensics.
* Access to configured external CSOC / SIEM console (e.g. {{ CSSP_PROVIDER }} / {{ EXTERNAL_SIEM }}) where centralized audit telemetry streams.

## 3. Scope
This runbook applies to all environments deployed using the {{ SYSTEM_NAME }} foundation, including {{ REGIME_DISPLAY_NAME }} landing zones. It assumes the use of modern GCP compute paradigms, including Shielded VMs, OS Login, Workload Identity, and immutable infrastructure.

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
Monitor for the following indicators of compromise (IoCs):
* **Security Command Center (SCC) (FedRAMP High / Commercial, where enabled; not in <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> without an AO exception):** High-severity alerts from Event Threat Detection (ETD) or Container Threat Detection (CTD, where enabled), such as `Execution: Added Malicious Binary Executed`, `Malware: Cryptomining Bad Domain`, or `Reverse Shell`.
* **External CSSP / SIEM (<!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF -->):** Alerts forwarded from Cloud Logging export sinks to external SIEM/SOC platforms ({{ CSSP_PROVIDER }}, {{ EXTERNAL_SIEM }}).
* **Network IDS / NGFW (or Cloud IDS where enabled in FedRAMP High / Commercial):** Intrusion detection alerts showing lateral movement, C2 beacons, or data exfiltration (note: Cloud IDS is not accredited in <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> without an AO exception).
* **Billing Anomalies:** Sudden spikes in Compute Engine CPU usage or network egress costs.
* **Third-Party EDR/XDR:** Alerts from host-based agents deployed on the VMs or GKE nodes.

### 1.2 Verification & Initial Triage
1. **Locate the Resource:** Identify the exact GCP resource implicated.
2. **Gather Context:**
    * **For VMs:** Project ID, Instance Name, Zone, Internal IP, attached Service Account, and current Network Tags.
    * **For GKE:** Project ID, Cluster Name, Namespace, Pod Name, Node Name, and associated Workload Identity.
3. **Review Audit and System Logs:**
    * Use Log Explorer to check for recent `cloudaudit.googleapis.com` admin activity on the resource (e.g., who created/modified it).
    * Look at OS/Application logs routed to Cloud Logging.
    * **Query Example (VM OS Logs):**
      ```text
      resource.type="gce_instance"
      AND resource.labels.instance_id="[INSTANCE_ID]"
      AND logName="projects/[PROJECT_ID]/logs/syslog"
      ```

### 1.3 Escalation & External Reporting
* Declare SEV 1 or SEV 2 incident in ticketing system and page On-Call Incident Commander.
* Report to external parties within the timelines that apply to this system:

| Reporting path | Applies to | Requirement | Contact and deadline for this system |
| :--- | :--- | :--- | :--- |
| CISA | Federal agencies | CISA Federal Incident Notification Guidelines: report within 1 hour of identification by the agency's top-level SOC, CSIRT, or IT department. US-CERT is now part of CISA. | [CONFIG_REQUIRED: agency reporting contact] |
| FedRAMP | Cloud services with a FedRAMP authorization | Notify affected agencies and FedRAMP per the FedRAMP incident communication rules. Under the FedRAMP Consolidated Rules for 2026 (Incident Evaluation and Communication), the Initial Incident Report deadline depends on the Potential Agency Impact (PAIN) rating and the certification class. | [CONFIG_REQUIRED: FedRAMP reporting procedure and deadline that apply] |
<!-- IF DOD_ENCLAVE -->
| DoD CSSP | <!-- IF DOD_IL5 -->DoD IL4 / DoD IL5<!-- ENDIF --><!-- IF DOD_IL4 -->DoD IL4<!-- ENDIF --><!-- IF DOD_IL2 -->DoD IL2<!-- ENDIF --><!-- IF DOD_IL6 -->DoD IL6<!-- ENDIF --><!-- IF NOT DOD_ENCLAVE -->{{ REGIME_DISPLAY_NAME }}<!-- ENDIF --> systems | Report through the system's Cybersecurity Service Provider (CSSP) into the Joint Incident Management System (JIMS) using the categories and impact-tiered timelines in CJCSM 6510.01B Table C-A-1. | [CONFIG_REQUIRED: CSSP contact and reporting timeline from the CSSP agreement] |
| DoD Cloud Service Provider | Cloud Service Offerings under DFARS 252.239-7010 / DISA CSP SRG V1R7 Section 6.2 | Submit initial incident report within 1 hour of triage via DIB Cyber Incident Collection Format (ICF) at https://dibnet.dod.mil (or `DCISE@DC3.mil` / 877-838-2174) for shared CSOs, or direct to USCYBERCOM / JFHQ-DODIN for dedicated DoD infrastructure. | [CONFIG_REQUIRED: CSP incident reporting POC] |
| DoD (DIBNet) | Defense contractors subject to DFARS 252.204-7012 | Report cyber incidents at https://dibnet.dod.mil within 72 hours of discovery; submit malicious software to the DoD Cyber Crime Center (DC3). | [CONFIG_REQUIRED: contract reporting POC] |
<!-- ENDIF -->

<!-- IF DOD_ENCLAVE -->
* **CJCSM 6510.01B categories & Table C-A-1 timelines:** a compute or container compromise is usually CAT 1 (Root Level Intrusion), CAT 2 (User Level Intrusion), or CAT 7 (Malicious Logic). Per CJCSM 6510.01B Table C-A-1: High impact CAT 1/2/7 notify next tier within 15 minutes / initial report within 4 hours / JIMS submission within 6 hours; Moderate impact CAT 1/2/7 notify within 2 hours / report within 8 hours / JIMS within 12 hours; confirm the category and `[CONFIG_REQUIRED: CSSP agreement timeline]` with the CSSP.
* **Authorized DoD Component CSSP escalation points (DoDM 8530.01 / GAO-25-107121; confirm against the system's CSSP agreement):**
  * Army: U.S. Army Cyber Command (ARCYBER) CSSP (executed via Army Network Enterprise Technology Command Regional Cyber Centers [RCCs]) and U.S. Army C5ISR Center CSSP.
  * Air Force: 16th Air Force (AFCYBER / AFIN CSSP, 616th Operations Center) and U.S. Air Forces Central (AFCENT) CSSP.
  * Navy: Navy Cyber Defense Operations Command (NCDOC) and NIWC Atlantic CSSP.
  * Marine Corps: Marine Corps Forces Cyberspace Command (MARFORCYBER / Marine Corps Cyberspace Operations Group [MCCOG]).
  * Space Force: U.S. Space Force CSSP (Space Delta 6 / Mission Delta 6).
  * Defense Agencies: DISA CSSP (or component-specific CSSP such as DIA, DLA, DTRA, MDA, NGA, NRO, NSA), which reports upstream to USCYBERCOM / JFHQ-DODIN (DoD Cyber Defense Command) via JIMS.
<!-- ENDIF -->

---

## Phase 2: Containment

**Goal:** Isolate the compromised resource to prevent lateral movement or data exfiltration *without* destroying volatile memory (RAM) or disk state needed for forensics.

### 2.1 Containment for Compute Engine VMs
1. **Do NOT Terminate or Restart:** This destroys volatile memory (RAM) and temporary files.
2. **Isolate Network (Quarantine):** Apply a strict network tag that isolates the VM.
    * *Prerequisite:* Ensure a VPC Firewall Rule exists that explicitly DENIES all ingress/egress for the tag `ir-quarantine`, priority `1`.
    * **Command:**
      ```bash
      gcloud compute instances add-tags [INSTANCE_NAME] --zone=[ZONE] --project=[PROJECT_ID] --tags=ir-quarantine
      ```
    * Remove the instance from any target pools or backend services to stop it from receiving legitimate traffic.
3. **Revoke OS Level Access:** Block new SSH connections via OS Login.
4. **Disable Attached Service Account:** If the VM uses a dedicated Service Account, disable it to prevent the attacker from using the VM's identity to access other GCP APIs.

### 2.2 Containment for GKE Pods
1. **Do NOT Delete the Pod:** Deleting the pod destroys the container filesystem and memory state.
2. **Remove from Service Routing:** Modify the pod's labels so it no longer matches the `Service` selector. This instantly stops it from receiving load-balanced user traffic.
    ```bash
    kubectl label pod [POD_NAME] -n [NAMESPACE] app- # Removes the 'app' label (adjust to match your routing labels)
    kubectl label pod [POD_NAME] -n [NAMESPACE] incident-response=quarantined
    ```
3. **Isolate via NetworkPolicy:** Apply a default-deny `NetworkPolicy` specifically targeting the quarantined pod to block all ingress and egress.
4. **Cordon the Node:** Prevent the scheduler from placing new, healthy workloads on the potentially compromised underlying node.
    ```bash
    kubectl cordon [NODE_NAME]
    ```

---

## Phase 3: Forensics and Analysis

**Goal:** Collect immutable evidence to understand the attack vector, persistence mechanisms, and blast radius.

### 3.1 Forensics for VMs
1. **Enumerate and Create Disk Snapshots:** List every attached persistent disk (boot and data disks) and take an immutable snapshot of each for offline digital forensics and incident response (DFIR) before deleting any instance.
    ```bash
    # Enumerate all attached disks on the instance
    gcloud compute instances describe [INSTANCE_NAME] \
        --zone=[ZONE] \
        --project=[PROJECT_ID] \
        --format="value(disks[].source)"

    # Snapshot each attached disk
    gcloud compute disks snapshot [DISK_NAME] \
        --zone=[ZONE] \
        --snapshot-names=ir-snap-[INSTANCE_NAME]-[TIMESTAMP] \
        --project=[PROJECT_ID]
    ```
2. **Memory Acquisition:** If required for a SEV-1 incident, deploy a volatile memory acquisition tool (such as LiME or AVML; analyze captured dumps offline with Volatility) via the serial console or a dedicated DFIR sidecar before pulling the plug.
3. **Export Metadata:** Capture the instance metadata to check for injected SSH keys or malicious startup scripts.

### 3.2 Forensics for GKE Pods
1. **Capture Pod State:** Save the full YAML definition of the pod to identify environmental variables, secrets, or image hashes.
    ```bash
    kubectl get pod [POD_NAME] -n [NAMESPACE] -o yaml > ir-pod-state.yaml
    ```
2. **Extract Logs:** Retrieve stdout/stderr logs from all containers in the pod (including any restarted container instances).
    ```bash
    kubectl logs [POD_NAME] -n [NAMESPACE] --all-containers=true --timestamps=true > ir-container-logs.txt
    kubectl logs [POD_NAME] -n [NAMESPACE] --all-containers=true --previous > ir-container-logs-previous.txt
    ```
3. **Snapshot the Node:** If the host node is compromised (container escape), perform a disk snapshot of the GKE node's boot disk following the VM forensics process above.

---

## Phase 4: Eradication and Recovery

**Goal:** Destroy the threat actor's foothold, patch the root vulnerability, and restore secure operations via GitOps.

### 4.1 Eradication (Immutable Infrastructure)
Because {{ SYSTEM_NAME }} relies on Infrastructure as Code (IaC) and immutable infrastructure, **do not attempt to patch or clean the compromised resource in place.**
1. **Destroy the Compromised Compute Resource (Post-Forensics):** Once disk snapshots and logs are verified, remove the compromised Pod, GKE node, or VM while retaining forensic disks until evidence retention is confirmed.
    * GKE Pods: `kubectl delete pod [POD_NAME] -n [NAMESPACE]`
    * GKE Nodes (if host escape confirmed): `kubectl drain [NODE_NAME] --ignore-daemonsets --delete-emptydir-data` and recycle the node through its GKE node pool / managed instance group.
    * VMs: `gcloud compute instances delete [INSTANCE_NAME] --zone=[ZONE] --project=[PROJECT_ID] --keep-disks=all`
2. **Identify the Vulnerability:** Analyze the forensic data to determine the root cause (e.g., unpatched CVE in the container image, SSRF vulnerability in the web app, leaked credentials).

### 4.2 Recovery
1. **Patch the Source:** Update the Dockerfile, `requirements.txt`, or base VM image to patch the vulnerability.
2. **Commit and Redeploy:** Push the fix to the {{ SYSTEM_NAME }} GitOps repository. Allow the accredited CI/CD pipeline (e.g., ArgoCD or Cloud Build where enabled in the authorization boundary) to build a new, clean artifact and deploy it.
3. **Verify Integrity:** Monitor the newly deployed resources closely via Cloud Monitoring and the configured SIEM / CSSP (or SCC where enabled) for [CONFIG_REQUIRED: monitoring period, e.g., 72 hours] to ensure the threat actor has not returned.

---

## Phase 5: Lessons Learned

### 5.1 Post-Incident Review (PIR)
1. Schedule a PIR within [CONFIG_REQUIRED: review deadline, e.g., 5 business days] with Security, DevOps, and Application owners.
2. **Evaluate Defenses:** Did the SIEM / CSSP, WAF, or SCC (where enabled) catch the attack? If not, why?
3. **Remediation Items:**
    * **GKE:** Enforce container image signature verification (e.g., Cosign / admission controller policies, or Binary Authorization where enabled in FedRAMP High / Commercial) to ensure only signed, scanned images are deployed. Implement stricter Pod Security Admission (PSA) standards to prevent privileged containers.
    * **VMs:** Ensure OS Patch Management is aggressively scheduled. Implement IAP (Identity-Aware Proxy) or bastion host controls for SSH access instead of public IP exposure.
4. **Update Runbooks:** Document any missing commands or tools in this playbook.
