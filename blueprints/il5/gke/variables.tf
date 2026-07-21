variable "gke_cluster_name" {
  description = "The GKE Kubernetes Cluster Name."
  type        = string
  # default     = "gke-kubernetes-cls"
}

variable "gke_initial_node_per_zone" {
  description = "The initial number of Node per each zone."
  type        = number
  #default     = 1
}

variable "gke_nodepool_name" {
  description = "The GKE Kubernetes Cluster Name."
  type        = string
  # default     = "gke-nodepool-k8s"
}

variable "gke_vpc_master_ipv4_cidr_block" {
  description = "The CIDR Range for the GKE Master IP CIDR Ranges for the k8s used for VPC configuration."
  type        = string
  # default     = "192.168.0.0/28"
}

variable "kms_key_names" {
  description = "Key names and base attributes. Set attributes to null if not needed."
  type = map(object({
    destroy_scheduled_duration    = optional(string)
    rotation_period               = optional(string, "7776000s") # CIS Compliance Benchmark 1.10
    labels                        = optional(map(string))
    purpose                       = optional(string, "ENCRYPT_DECRYPT")
    skip_initial_version_creation = optional(bool, false)
    version_template = optional(object({
      algorithm        = string
      protection_level = optional(string, "SOFTWARE")
    }))
    iam = optional(map(list(string)), {})
    iam_bindings = optional(map(object({
      members = list(string)
      role    = string
      condition = optional(object({
        expression  = string
        title       = string
        description = optional(string)
      }))
    })), {})
    iam_bindings_additive = optional(map(object({
      member = string
      role   = string
      condition = optional(object({
        expression  = string
        title       = string
        description = optional(string)
      }))
    })), {})
  }))
  default = {
    "key-gke" = {
      rotation_period            = "7776000s"
      destroy_scheduled_duration = "2592000s"
      labels = {
        team = "gke-team"
      }
      version_template = {
        algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
        protection_level = "SOFTWARE"
      }
      lifecycle = {
        prevent_destroy = true
      }
    }
  }
  nullable = false
}

variable "kms_keyring_name" {
  description = "Keyring attributes."
  type = object({
    location = string
    name     = string
  })
}

variable "main_project_id" {
  description = "The ID of the project in which to create the GKE cluster."
  type        = string
}

variable "master_authorized_ranges_ip_ranges" {
  description = "The CIDR Range for the GKE Nodes Pool when enabled Private End Point with master authorized ranges of CIDR."
  type        = string
}

variable "network_name" {
  description = "The VPC Name."
  type        = string
  # default     = "vpc-gke-kubernetes"
}

variable "node_config_tags" {
  description = "The Tags on the Node Configuration."
  type        = list(string)
  nullable    = false
}

variable "node_disk_size_gb" {
  description = "The disk size in GB to be given to each node."
  type        = number
}

variable "node_machine_type" {
  description = "The Node Machine type to be used in the NodePool."
  type        = string
  default     = "n2d-standard-2"
}

variable "nodepool_node_count" {
  description = "Number of node per zone in the Nodepool."
  type = object({
    current = optional(number)
    initial = number
  })
  nullable = false
}

variable "region" {
  description = "The GCP region to use for the resources."
  type        = string
}

# tflint-ignore: terraform_unused_declarations
variable "remove_default_node_pool" {
  description = "The Default NodePool remove it or not."
  type        = bool
  # default     = false
}

variable "subnetwork_ip_cidr_range_1" {
  description = "The CIDR Range for the VPC Subnet."
  type        = string
  # default     = "10.0.4.0/22"
}

variable "subnetwork_name" {
  description = "The Subnet Name."
  type        = string
  # default     = "subnet-gke-kubernetes"
}

variable "subnetwork_secondary_ip_range_pods_1" {
  description = "The CIDR Range for the secondary IP CIDR Ranges for the k8s pods."
  type        = string
  # default     = "10.4.0.0/14"
}

variable "subnetwork_secondary_ip_range_services_1" {
  description = "The CIDR Range for the secondary IP CIDR Ranges for the k8s services."
  type        = string
  # default     = "10.0.32.0/20"
}

