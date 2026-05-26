# Incident Response Runbook: Compute Resource Compromise

## Document Control
| Attribute | Detail |
| :--- | :--- |
| **Runbook ID** | IR-COMP-001 |
| **Last Updated** | YYYY-MM-DD |
| **Owner** | Security Operations / Cloud Platform Team |
| **Target SLA** | Triage: 15m \| Containment: 45m \| Forensics: 2h \| Recovery: 4h |

## 1. Objective
This runbook provides a structured, actionable process for Security Operators and Incident Responders to identify, contain, analyze, and recover from incidents involving the compromise of compute resources—specifically Google Kubernetes Engine (GKE) Pods/Nodes or Compute Engine (GCE) Virtual Machines—within the Stellar architecture on Google Cloud Platform (GCP).

## 2. Target Audience & Prerequisites
**Audience:**
* Security Operations Center (SOC) Analysts (L1/L2/L3)
* Incident Responders
* Platform / DevOps Engineers

**Prerequisites for Responders:**
* `roles/compute.viewer` and `roles/container.viewer` for scoping.
* `roles/compute.securityAdmin` to modify network tags and firewalls for VM containment.
* `roles/container.developer` or equivalent RBAC `ClusterRole` to manipulate Pods and apply NetworkPolicies.
* `roles/compute.storageAdmin` to snapshot disks for forensics.

## 3. Scope
This runbook applies to all environments deployed using the Stellar framework, including FedRAMP High and IL5 landing zones. It assumes the use of modern GCP compute paradigms, including Shielded VMs, OS Login, Workload Identity, and immutable infrastructure.

---

## Phase 1: Identification & Scoping

### 1.1 Detection Sources
Monitor for the following indicators of compromise (IoCs):
* **Security Command Center (SCC):** High-severity alerts from Event Threat Detection (ETD) or Container Threat Detection (CTD), such as `Malicious Process execution`, `Cryptomining Domain DNS Request`, or `Reverse Shell`.
* **Cloud IDS / NGFW:** Intrusion detection alerts showing lateral movement, C2 beacons, or data exfiltration.
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
1. **Create Disk Snapshots:** Take a snapshot of all attached persistent disks for offline digital forensics and incident response (DFIR).
    ```bash
    gcloud compute disks snapshot [DISK_NAME] \
        --zone=[ZONE] \
        --snapshot-names=ir-snap-[INSTANCE_NAME]-[TIMESTAMP] \
        --project=[PROJECT_ID]
    ```
2. **Memory Acquisition:** If required for a SEV-1 incident, deploy a memory capture tool (like LiME or Volatility) via the serial console or a dedicated DFIR sidecar before pulling the plug.
3. **Export Metadata:** Capture the instance metadata to check for injected SSH keys or malicious startup scripts.

### 3.2 Forensics for GKE Pods
1. **Capture Pod State:** Save the full YAML definition of the pod to identify environmental variables, secrets, or image hashes.
    ```bash
    kubectl get pod [POD_NAME] -n [NAMESPACE] -o yaml > ir-pod-state.yaml
    ```
2. **Extract Logs:** Retrieve stdout/stderr logs from the container.
    ```bash
    kubectl logs [POD_NAME] -n [NAMESPACE] > ir-container-logs.txt
    ```
3. **Snapshot the Node:** If the host node is compromised (container escape), perform a disk snapshot of the GKE node's boot disk following the VM forensics process above.

---

## Phase 4: Eradication and Recovery

**Goal:** Destroy the threat actor's foothold, patch the root vulnerability, and restore secure operations via GitOps.

### 4.1 Eradication (Immutable Infrastructure)
Because Stellar relies on Infrastructure as Code (IaC) and immutable infrastructure, **do not attempt to patch or clean the compromised resource in place.**
1. **Destroy the Evidence (Post-Forensics):** Once snapshots and logs are secured, delete the compromised VM or GKE Node/Pod.
    * GKE Pods: `kubectl delete pod [POD_NAME] -n [NAMESPACE]`
    * VMs: `gcloud compute instances delete [INSTANCE_NAME] --zone=[ZONE]`
2. **Identify the Vulnerability:** Analyze the forensic data to determine the root cause (e.g., unpatched CVE in the container image, SSRF vulnerability in the web app, leaked credentials).

### 4.2 Recovery
1. **Patch the Source:** Update the Dockerfile, `requirements.txt`, or base VM image to patch the vulnerability. 
2. **Commit and Redeploy:** Push the fix to the Stellar GitOps repository. Allow the CI/CD pipeline (e.g., Cloud Build, ArgoCD) to build a new, clean artifact and deploy it.
3. **Verify Integrity:** Monitor the newly deployed resources heavily via Cloud Monitoring and SCC for 72 hours to ensure the threat actor has not returned.

---

## Phase 5: Lessons Learned

### 5.1 Post-Incident Review (PIR)
1. Schedule a PIR within 5 business days with Security, DevOps, and Application owners.
2. **Evaluate Defenses:** Did SCC or the WAF catch the attack? If not, why?
3. **Remediation Items:**
    * **GKE:** Enforce Binary Authorization to ensure only signed, scanned images are deployed. Implement stricter Pod Security Admission (PSA) standards to prevent privileged containers.
    * **VMs:** Ensure OS Patch Management is aggressively scheduled. Implement IAP (Identity-Aware Proxy) for SSH access instead of public IP exposure.
4. **Update Runbooks:** Document any missing commands or tools in this playbook.
