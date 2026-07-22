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

# GitLab

<!-- BEGIN TOC -->
- [GitLab Blueprint](#gitlab-blueprint)
- [Pre-Requisite](#pre-requisite)
- [Deployment Steps](#deployment-steps)
  - [Gitlab Certificate Generation](#gitlab-certificate-generation)
  - [Gitlab Helm Configuration](#gitlab-helm-configuration)
- [Variables](#variables)
- [Outputs](#outputs)
<!-- END TOC -->

## GitLab Blueprint
This blueprint will deploy all the required infrastructure to host a GitLab instance that can support [40 RPS or 2,000 users](https://docs.gitlab.com/administration/reference_architectures/2k_users/). Gitlab will be deployed on a GKE cluster. 

## Pre-Requisite 
Before deployment of a new cluster, two org policies need to be configured to allow for global load balancing.
Run this code after replacing with your project id:
```
cat <<EOF > lb_types.yaml
constraint: constraints/compute.restrictLoadBalancerCreationForTypes
listPolicy:
  inheritFromParent: true
  allowedValues:
  - EXTERNAL_HTTP_HTTPS
  - GLOBAL_EXTERNAL_MANAGED_HTTP_HTTPS
  - EXTERNAL_NETWORK_TCP_UDP
EOF

gcloud resource-manager org-policies set-policy lb_types.yaml --project=<PROJECT_ID>
```

Run this code after replacing with your project id:
```
cat <<EOF > global_lb.yaml
constraint: constraints/compute.disableGlobalLoadBalancing
booleanPolicy:
  enforced: false
EOF

gcloud resource-manager org-policies set-policy global_lb.yaml --project=<PROJECT_ID>
```

## Deployment Steps
```bash
cp terraform.tfvars.sample terraform.tfvars
```
Fill out the terraform.tfvars with the appropriate values for your own deployment.
```bash
terraform init
```
```bash
terraform plan
```
```bash
terraform apply
```

### Gitlab Certificate Generation

1. Download the generation script from the storage bucket created from the blueprint
    ```
    gsutil cp gs://[BUCKET NAME]/generate_certs.sh .
    ```
1. Move this file to your project running DNS
1. Edit the initial configuration at the top of the file
    Note: Gitlab deploys a number of tools that have their own endpoints, so a wildcard cert would be beneficial.
1. Run the script
    ```
    chmod +x generate_certs.sh
    ./generate_certs.sh
    ```
1. Look for two files in ‘.lego/certificates/’; [DOMAIN].crt, and [DOMAIN].key
1. Combine the cert file by running 
    ```
    DOMAIN="[DOMAIN]"
    cat .lego/certificates/$DOMAIN.crt .lego/certificates/$DOMAIN.issuer.crt > tls.crt
    ```
1. Rename the key file by running
    ```
    mv [DOMAIN].key tls.key
    ```
1. Move the tls.crt and tls.key files into the main project bucket.

### Gitlab Helm Configuration
The deployment of Gitlab uses a Helm Chart. This contains a templated set of Kubernetes yaml files that can be configured for the deployment of Gitlab, and associated tools.  This configuration includes Gitlab, Postgres, Redis, NGINX, and other supporting tools.
1. Go to https://console.cloud.google.com/kubernetes/list/overview, and make sure to change into your project, to verify the cluster is created.
1. Click on the three dots on the right side of the listing for your cluster and choose ‘Connect’
1. Click on ‘Run in Cloud Shell’, this will open a Cloud Shell terminal and enter the command
1. Press the ‘Enter’ key to run the command. You should have access to the cluster.
1. Run ‘kubectl get nodes’ to verify connection.
1. Install Helm (if not already available)
- For documentation, go to: https://helm.sh/docs/intro/install/
1. Add the GitLab Helm repository
    ```
    helm repo add gitlab https://charts.gitlab.io/
    helm repo update
    helm pull gitlab/gitlab --untar
    ```
1. Create the namespace
    ```
    kubectl create namespace gitlab
    ```
1. Create a secret in based on the certificate we created earlier
    ```
    kubectl create secret tls gitlab-wildcard-tls \
    --cert=tls.crt \
    --key=tls.key \
    -n gitlab
    ```
1. Edit the values.yaml file from the helm chart folder
    ```
    # ------------------------------------------------
    # Global Settings
    # ------------------------------------------------
    global:
      hosts:
        domain: YOUR_DOMAIN_NAME
        # Using your manual secret stops the "Revert Loop"
        https: true

      ingress:
        # Disable internal automation so it respects your manual secret
        configureCertmanager: false
        tls:
          enabled: true
          secretName: gitlab-wildcard-tls  # Points to the secret created

    # ------------------------------------------------
    # Component Settings
    # ------------------------------------------------
    certmanager:
      install: false # Explicitly disable the bundled cert-manager

    gitlab-runner:
      install: true

    # Optional: Disable components to save resources
    prometheus:
      install: false
    grafana:
      install: false
    ```

1. Deploy the helm chart
    ```
    helm upgrade --install gitlab gitlab/gitlab --namespace gitlab -f values.yaml --timeout 600s
    ```
1. Retrieve the root password
    ```
    kubectl get secret gitlab-gitlab-initial-root-password -n gitlab -o jsonpath="{.data.password}" | base64 --decode ; echo
    ```
1. If all the pods are running and you can reach the web service at 
https://gitlab.[DOMAIN], then you can login with the credentials
  Name: root
  Password: [OUTPUT FROM ABOVE]

1. Verify Runner Registration
    ```
    kubectl logs -n gitlab -l app=gitlab-gitlab-runner
    ```

1. Force Restart (if secrets are changed, the webservice should be restarted).
    ```
    kubectl delete pods -n gitlab -l app=webservice
    ```
<!-- BEGIN TFDOC -->
## Variables

| name | description | type | required | default |
|---|---|:---:|:---:|:---:|
| [project_id](variables.tf#L60) | Project ID where the GitLab cluster, VM, and load balancer will be deployed to. | <code>string</code> | ✓ |  |
| [sa](variables.tf#L71) | Service account to run GKE and VM. | <code>string</code> | ✓ |  |
| [subnet_service_range](variables.tf#L82) | The name of the secondary IP range to be used for GKE Services. | <code>string</code> | ✓ |  |
| [bucket_name](variables.tf#L1) | Name of the bucket that will hold keycloak yaml files. | <code>string</code> |  | <code>&#34;gitlab-config&#34;</code> |
| [existing_cluster](variables.tf#L7) | A cluster already exists that will be used for Gitlab deployment. | <code>bool</code> |  | <code>false</code> |
| [gitlab_allow_source_ranges](variables.tf#L13) | A list of IP ranges for the GitLab firewall rule's source. | <code>list&#40;string&#41;</code> |  | <code>&#91;&#93;</code> |
| [gke_name](variables.tf#L19) | Name of the GKE cluster. | <code>string</code> |  | <code>&#34;gitlab-cluster&#34;</code> |
| [kms_key](variables.tf#L25) | KMS key path. | <code>string</code> |  | <code>null</code> |
| [net_project](variables.tf#L31) | Project name of the spoke network. This project has the Stellar Engine Landing Zone deployed default VPC and is in the Networking folder. | <code>string</code> |  | <code>null</code> |
| [network](variables.tf#L37) | Network path to use for cluster, VM, and load balancer. | <code>string</code> |  | <code>null</code> |
| [network_name](variables.tf#L43) | Network name to use for Firewall rules. E.G. test-net-spoke. | <code>string</code> |  | <code>null</code> |
| [nodepool_node_count](variables.tf#L49) | Number of node per zone in the Nodepool. | <code title="object&#40;&#123;&#10;  current &#61; optional&#40;number&#41;&#10;  initial &#61; number&#10;&#125;&#41;">object&#40;&#123;&#8230;&#125;&#41;</code> |  | <code title="&#123;&#10;  initial &#61; 0&#10;&#125;">&#123;&#8230;&#125;</code> |
| [region](variables.tf#L65) | Region for deployment. | <code>string</code> |  | <code>&#34;us-east4&#34;</code> |
| [subnet_pod_range](variables.tf#L76) | The name of the secondary IP range to be used for GKE Pods. | <code>string</code> |  | <code>null</code> |
| [subnetwork](variables.tf#L87) | Subnet path to use for cluster, and load balancer. | <code>string</code> |  | <code>null</code> |

## Outputs

| name | description | sensitive |
|---|---|:---:|
| [gke-cluster](outputs.tf#L1) | Deployed GKE cluster. | ✓ |
<!-- END TFDOC -->
