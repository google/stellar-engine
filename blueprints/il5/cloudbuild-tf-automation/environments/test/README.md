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

This environment is an example utilizing cloud build to deploy a storage bucket in the
FRH -> Project [tenant] Test -> XXX-test-[tenant]-main-0 project after running the Deployment stage

Prerequisite: Ensure your user account has the role: roles/cloudbuild.builds.editor

Step 1. Set environment variables
```
source config.env
```

Step 2. Execute Terraform Plan on Cloudbuild. From within the environments directory, 

run the following:
```
gcloud config set project $CB_PROJECT
gcloud --project=$CB_PROJECT builds submit $REPOSITORY_ROOT \
  --config="tf-plan.yaml" \
  --region=$CB_REGION \
  --substitutions=_ENVIRONMENTS=$ENVIRONMENTS,_ENV_FOLDER=$ENV_FOLDER,_TFVARS_FILENAME=$TFVARS_FILENAME,_CB_LOG_BUCKET=$CB_LOG_BUCKET,_CB_STATE_BUCKET=$CB_STATE_BUCKET \
  --service-account=$CB_SERVICE_ACCOUNT
```

Check The Cloud Build History page in the CB_PROJECT
https://console.cloud.google.com/cloud-build/builds

Step 3. If you like the output, then execute the Terraform Apply:
```
gcloud --project=$CB_PROJECT builds submit $REPOSITORY_ROOT \
  --config="tf-apply.yaml" \
  --region=$CB_REGION \
  --substitutions=_ENVIRONMENTS=$ENVIRONMENTS,_ENV_FOLDER=$ENV_FOLDER,_TFVARS_FILENAME=$TFVARS_FILENAME,_CB_LOG_BUCKET=$CB_LOG_BUCKET,_CB_STATE_BUCKET=$CB_STATE_BUCKET \
  --service-account=$CB_SERVICE_ACCOUNT
```