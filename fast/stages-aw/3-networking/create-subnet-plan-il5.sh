#!/bin/bash
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
