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

mock_provider "google" {}

override_data {
  target = data.google_project.current
  values = {
    number = "123456789012"
  }
}

override_data {
  target = data.google_kms_key_ring.default
  values = {
    id = "projects/my-core-project/locations/us-east4/keyRings/my-keyring"
  }
}

override_data {
  target = data.google_kms_crypto_key.default
  values = {
    id = "projects/my-core-project/locations/us-east4/keyRings/my-keyring/cryptoKeys/my-key"
  }
}

variables {
  main_project_id  = "my-project"
  core_project_id  = "my-core-project"
  gcp_region       = "us-east4"
  kms_keyring_name = "my-keyring"
  kms_key_name     = "my-key"
  pubsub_topic     = "my-topic"
}

# The service accounts do not exist yet on a first plan, so their member
# attribute is unknown. The plan must not need it to build a for_each key.
run "plan_fresh_deployment" {
  command = plan

  # Existing deployments address the grant by this member string, so the key
  # must not change.
  assert {
    condition = tolist(keys(google_kms_crypto_key_iam_member.kms_access)) == tolist([
      "serviceAccount:service-123456789012@gcp-sa-pubsub.iam.gserviceaccount.com",
    ])
    error_message = "Expected a single key grant, keyed by the Pub/Sub service agent member."
  }

  assert {
    condition = alltrue([
      for k, v in google_kms_crypto_key_iam_member.kms_access : v.member == k
    ])
    error_message = "Expected the key grant member to be the Pub/Sub service agent."
  }

  assert {
    condition = alltrue([
      for v in google_kms_crypto_key_iam_member.kms_access :
      v.role == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    ])
    error_message = "Expected the Pub/Sub service agent to hold the encrypter and decrypter role."
  }

  assert {
    condition = alltrue([
      for v in google_kms_crypto_key_iam_member.kms_access :
      v.crypto_key_id == "projects/my-core-project/locations/us-east4/keyRings/my-keyring/cryptoKeys/my-key"
    ])
    error_message = "Expected the grant on the key that encrypts the topic."
  }

  assert {
    condition     = module.pubsub.topic.kms_key_name == "projects/my-core-project/locations/us-east4/keyRings/my-keyring/cryptoKeys/my-key"
    error_message = "Expected the topic to stay encrypted with the existing key."
  }
}
