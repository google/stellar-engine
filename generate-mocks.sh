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



SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Generate mock provider files for all stages in stages-aw
echo 'terraform {
  required_version = ">= 1.7.4"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.24.0"
    }
    google-beta = {
      source = "hashicorp/google-beta"
      version = ">=1.0.0"
    }
    local = {
      source = "hashicorp/local"
      version = ">=2.0.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">=0.0.0"
    }
    external = {
      source  = "hashicorp/external"
      version = ">=0.0.0"
    }
   random = {
      source  = "hashicorp/random"
      version = ">=3.0.0"
    }
   tls = {
      source  = "hashicorp/tls"
      version = ">=3.0.0"
    }
  }
}' | tee "${SCRIPT_DIR}"/fast/stages-aw/0-bootstrap/mock-versions.tf \
         "${SCRIPT_DIR}"/fast/stages-aw/1-resman/mock-versions.tf \
         "${SCRIPT_DIR}"/fast/stages-aw/2-networking-a-fedramp-high/mock-versions.tf \
         "${SCRIPT_DIR}"/fast/stages-aw/2-networking-b-il5-ngfw/mock-versions.tf \
         "${SCRIPT_DIR}"/fast/stages-aw/3-security/mock-versions.tf


