
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