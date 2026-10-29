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

"""Deployment answers: the model, its validation and derived values.

`answers.yaml` holds what the operator chose for one environment. Values
that Terraform derives on its own, such as the KMS protection level, stay
unset there and `derive` computes them, so a seeded environment with a new
regime picks up the new defaults.
"""
