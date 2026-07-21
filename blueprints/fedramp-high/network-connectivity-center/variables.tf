variable "main_project_id" {
  description = "The GCP Project ID where the hub will be created."
  type        = string
}

variable "name" {
  description = "The name of the created NCC hub."
  type        = string
  default     = "example-ncc-hub"
}

variable "psc_prop" {
  description = "Whether or not private service connections can be propagated to other spokes in the network."
  type        = bool
  default     = false
}

variable "region" {
  description = "The GCP region."
  type        = string
}

variable "spokes" {
  description = "A list of spokes to be added to the NCC hub."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "topology" {
  description = "The topology of the network. Can be MESH or STAR."
  type        = string
  default     = "MESH"
  validation {
    condition     = contains(["MESH", "STAR"], var.topology)
    error_message = "Invalid topology. Must be either 'MESH' or 'STAR'."
  }
}