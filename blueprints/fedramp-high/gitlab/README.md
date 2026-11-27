# GitLab Blueprint
This blueprint will deploy all the required infrastructure to host a GitLab instance that can support 40 RPS.

## Note
To expose external HTTPS access to the GitLab instance, deploy the GCE VM, GKE cluster, and regional external Application Load Balancer into a Stage 2 Shared VPC spoke network (for example `prod-spoke-0` in host project `xxxx-prod-net-host` inside the Networking folder). The target subnet (`prod-tenant-1-subnet`) must define secondary IPv4 ranges named `gitlab-pod-range` and `gitlab-service-range` for GKE pods and services.

## Service accounts
The blueprint creates two service accounts in the deployment project:

- The GitLab VM runs as the account named by the `sa` variable.
- The GKE nodes run as a separate account named after the first 24 characters of the `gke_name` variable followed by `-nodes`. It holds only `roles/artifactregistry.reader`, `roles/autoscaling.metricsWriter`, `roles/logging.logWriter`, `roles/monitoring.metricWriter`, and `roles/monitoring.viewer` on the deployment project.

## Manual Pre-Requisite Steps
Open the Shared VPC network inside the net-host project inside the Networking folder in the Stellar Engine environment and ensure:

1. The target GKE subnet includes secondary IP ranges named `gitlab-pod-range` and `gitlab-service-range`.
2. A `REGIONAL_MANAGED_PROXY` subnet exists in the target region (Stage 2 networking creates `proxy-<region>`); pass its CIDR range via `proxy_subnetwork_cidrs` so load balancer proxy traffic reaches the GitLab VM.
3. Pass internal CIDR ranges allowed to access the GKE control plane endpoint via `gke_authorized_ranges`.

![alt text](images/image.png)

Next, open organization policies and allow `EXTERNAL_MANAGED_HTTP_HTTPS` for the "Restrict Load Balancer Creation Based on Load Balancer Types" (`compute.restrictLoadBalancerCreationForTypes`) constraint on the deployment project.

![alt text](images/image-3.png)

## Deployment Steps

Copy `terraform.tfvars.sample` to `terraform.tfvars`, populate project IDs, network paths, secondary-enabled subnet path, KMS key path, `proxy_subnetwork_cidrs`, and `gke_authorized_ranges`, then run:

```bash
terraform init
terraform plan
terraform apply
```

## Manual Post-Requisite Steps
Navigate to the deployed Load Balancer in Network Services on the Google Cloud Console. Note the HTTPS frontend IP address, configure DNS for the hostname in `gitlab_uri`, and use that HTTPS URL when connecting the GKE cluster (for example `https://gitlab.example.com`). Connect to the private GitLab VM over IAP (`gcloud compute ssh <VM_NAME> --zone=<ZONE> --project=<PROJECT_ID> --tunnel-through-iap --internal-ip`) and run the following commands in order.
```bash
gcloud container clusters get-credentials <CLUSTER_NAME> --region=<CLUSTER_LOCATION> --project <PROJECT_ID>
```
```bash
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.7.1/cert-manager.yaml
```
```bash
curl --silent --location "https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.24.0/install.sh" | bash -s v0.24.0
```
```bash
kubectl create -f https://operatorhub.io/install/gitlab-runner-operator.yaml
```
```bash
cat > certificate-issuer-install.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  labels:
    app.kubernetes.io/component: controller-manager
    app.kubernetes.io/managed-by: olm
    app.kubernetes.io/name: gitlab-runner-operator
  name: gitlab-runner-system
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: gitlab-runner-serving-cert
  namespace: gitlab-runner-system
spec:
  dnsNames:
  - gitlab-runner-webhook-service.gitlab-runner-system.svc
  - gitlab-runner-webhook-service.gitlab-runner-system.svc.cluster.local
  issuerRef:
    kind: Issuer
    name: gitlab-runner-selfsigned-issuer
  secretName: webhook-server-cert
---
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: gitlab-runner-selfsigned-issuer
  namespace: gitlab-runner-system
spec:
  selfSigned: {}
EOF
```
```bash
kubectl create -f certificate-issuer-install.yaml
```
In the SSH connection run the following command to get admin credentials.
```bash
sudo cat /etc/gitlab/initial_root_password | grep "^Password: "
```
Navigate to your deployed GitLab instance in your browser and login as root.
Navigate to Admin Page -> CI/CD -> Runners -> New instance runner.
Choose the Linux operating system option.
Note the runner's authentication token.
```bash
cat > gitlab-runner-secret.yml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: gitlab-runner-secret
type: Opaque
stringData:
  runner-token: YOUR_RUNNER_AUTHENTICATION_TOKEN
EOF
```
Before applying the runner manifest below, wait about 30 minutes for the GitLab OLM operator installation on the GKE cluster to become ready.
```bash
kubectl apply -f gitlab-runner-secret.yml
```

## Enabling HTTPS

Terraform terminates TLS at the regional external application load balancer (`protocol = "HTTPS"` on port `443`) and proxies traffic over HTTP on port `80` to the GitLab VM inside the VPC:

- By default (`ssl_certificate = null`), Terraform generates a 720-hour self-signed certificate whose common name and SAN match the hostname in `gitlab_uri`, stores the generated TLS private key in a CMEK-encrypted Secret Manager secret (`tls_private_key_secret_id`), and attaches the certificate to the load balancer.
- For production deployments or certificate renewal, pass a managed or CA-signed certificate through `ssl_certificate` (`certificate_id` for an existing regional SSL certificate, or `certificate` and `private_key` PEM values).
- During VM bootstrap, the startup script writes `/etc/gitlab/gitlab.rb` with `external_url`, `letsencrypt['enable'] = false`, `nginx['listen_port'] = 80`, `nginx['listen_https'] = false`, and `X-Forwarded-Proto` and `X-Forwarded-Ssl` proxy headers before installing `gitlab-ee` and running `gitlab-ctl reconfigure`. No manual `/etc/gitlab/gitlab.rb` or load balancer changes are needed.

Configure the GitLab Runner to connect using your HTTPS `gitlab_uri`:
```bash
cat > gitlab-runner.yml << EOF
apiVersion: apps.gitlab.com/v1beta2
kind: Runner
metadata:
  name: gitlab-runner
spec:
  gitlabUrl: <your gitlab url here (e.g. https://gitlab.example.com)>
  buildImage: alpine
  token: gitlab-runner-secret
EOF
```
```bash
kubectl apply -f gitlab-runner.yml
```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [gitlab_uri](variables.tf#L31) | The HTTPS URL that the GitLab instance will be served on. | <code>string</code> | ✓ |  |
| [kms_key](variables.tf#L69) | KMS key path. | <code>string</code> | ✓ |  |
| [net_project](variables.tf#L80) | Project name of the spoke network. This project has the Stellar Engine deployed default VPC and is in the Networking folder. | <code>string</code> | ✓ |  |
| [network](variables.tf#L85) | Network path to use for cluster, VM, and load balancer. | <code>string</code> | ✓ |  |
| [network_name](variables.tf#L90) | Network name to use for firewall rules (for example, prod-spoke-0). | <code>string</code> | ✓ |  |
| [nodepool_node_count](variables.tf#L95) | Number of node per zone in the Nodepool. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> | ✓ |  |
| [project_id](variables.tf#L104) | Project ID where the GitLab cluster, VM, and load balancer will be deployed to. | <code>string</code> | ✓ |  |
| [sa](variables.tf#L126) | Account ID of the service account that runs the GitLab VM. | <code>string</code> | ✓ |  |
| [subnetwork](variables.tf#L158) | Subnet path to use for cluster, VM, and load balancer. | <code>string</code> | ✓ |  |
| [compute_image](variables.tf#L15) | The image used to provision the compute instance. | <code>string</code> |  | <code>&#34;projects&#47;ubuntu-os-cloud&#47;global&#47;images&#47;ubuntu-2404-noble-amd64-v20241219&#34;</code> |
| [gitlab_install_script_sha256](variables.tf#L21) | Expected SHA-256 hash for the GitLab package repository install script. | <code>string</code> |  | <code>&#34;47c124527729776870cf09cd6bd46a9b94f55d40c7545ca26640c75de86b560d&#34;</code> |
| [gke_authorized_ranges](variables.tf#L40) | Map of display names to IPv4 CIDR ranges authorized to access the GKE control plane endpoint. | <code>map&#40;string&#41;</code> |  | <code>&#123;&#125;</code> |
| [gke_initial_node_per_zone](variables.tf#L51) | Initial node amount per zone. | <code>number</code> |  | <code>1</code> |
| [gke_name](variables.tf#L57) | Name of the GKE cluster. | <code>string</code> |  | <code>&#34;gitlab-cluster&#34;</code> |
| [instance_name](variables.tf#L63) | Name of the vm. | <code>string</code> |  | <code>&#34;gitlab-instance&#34;</code> |
| [lb_name](variables.tf#L74) | Application load balancer name. | <code>string</code> |  | <code>&#34;gitlab-load-balancer&#34;</code> |
| [proxy_subnetwork_cidrs](variables.tf#L109) | CIDR ranges of the regional managed proxy subnets permitted to reach the GitLab backend VM through the firewall rule. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [region](variables.tf#L120) | Region for deployment. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [ssl_certificate](variables.tf#L131) | Optional TLS certificate configuration for the HTTPS load balancer. Generates a self-signed certificate and stores its key in Secret Manager when null. | <code>object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code>null</code> |
| [vm_name](variables.tf#L163) | VM name. | <code>string</code> |  | <code>&#34;gitlab-vm&#34;</code> |
| [zone](variables.tf#L169) | Zone to deploy to. | <code>string</code> |  | <code>&#34;us-east4-a&#34;</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [gke_cluster](outputs.tf#L15) | Deployed GKE cluster. | ✓ |
| [lb](outputs.tf#L21) | Application Load Balancer. | ✓ |
| [tls_private_key_secret_id](outputs.tf#L27) | Secret Manager ID storing the generated self-signed TLS private key, or null when using a custom certificate. |  |
| [umig](outputs.tf#L36) | Unmanaged instance group. | ✓ |
| [vm](outputs.tf#L42) | Deployed VM. | ✓ |
<!-- END TFDOC -->
