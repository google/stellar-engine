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

json_file="2-resman.auto.tfvars.json"
subnet_plan="data/subnet_plan.yaml"
env_names=$(jq -r '.tenant_environments | keys[]' "$json_file")

base_ip="10.1.0.0"
base_octet=$(echo "$base_ip" | cut -d '.' -f 2)

echo "---" > "$subnet_plan"
echo "tenant_environments_subnets:" >> "$subnet_plan"
counter=0
while IFS= read -r env_names; do
    incremented_octet=$((base_octet + counter))
    cidr="10.${incremented_octet}.0.0/16"
    echo "    ${env_names}: \"${cidr}\"" >> "$subnet_plan"
    ((counter++))
done <<< "$env_names"
