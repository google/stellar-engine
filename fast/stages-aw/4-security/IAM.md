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

# IAM bindings reference

Legend: <code>+</code> additive, <code>•</code> conditional.

## Project <i>dev-sec-core-0</i>

| members | roles |
|---|---|
|<b>dev-resman-dp-0</b><br><small><i>serviceAccount</i></small>|[roles/cloudkms.viewer](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.viewer) <br>[roles/cloudkms.admin](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.admin) <code>+</code><code>•</code>|
|<b>dev-resman-pf-0</b><br><small><i>serviceAccount</i></small>|[roles/cloudkms.viewer](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.viewer) <br>[roles/cloudkms.admin](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.admin) <code>+</code><code>•</code>|
|<b>prod-resman-pf-0</b><br><small><i>serviceAccount</i></small>|[roles/cloudkms.viewer](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.viewer) <br>[roles/cloudkms.admin](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.admin) <code>+</code><code>•</code>|

## Project <i>prod-sec-core-0</i>

| members | roles |
|---|---|
|<b>prod-resman-dp-0</b><br><small><i>serviceAccount</i></small>|[roles/cloudkms.viewer](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.viewer) <br>[roles/cloudkms.admin](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.admin) <code>+</code><code>•</code>|
|<b>prod-resman-pf-0</b><br><small><i>serviceAccount</i></small>|[roles/cloudkms.viewer](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.viewer) <br>[roles/cloudkms.admin](https://cloud.google.com/iam/docs/understanding-roles#cloudkms.admin) <code>+</code><code>•</code>|
