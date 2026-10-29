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

"""Formats of the values that both answers and preflight inputs accept.

The answers model and the preflight inputs validate the same fields, and
preflight must not depend on the answers package, so both read the
patterns from this leaf module.
"""

# An email address, such as the bootstrap user or the alert email.
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
# A numeric organization ID.
ORG_ID = r"^[0-9]+$"
# A billing account ID such as `000000-AAAAAA-BBBBBB`.
BILLING_ACCOUNT = r"^[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}$"
# A project ID: 6 to 30 characters, starting with a letter.
PROJECT_ID = r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$"
# An Assured Workloads regime name in capitals, such as `IL5`.
REGIME = r"^[A-Z0-9_]+$"
# A deployment prefix. Stages 0 and 1 validate only its length, which the
# answers validation reads from the repository. The pattern keeps every
# derived project ID valid, and it never matches a path separator or a dot,
# so the prefix also works as the folder name of the environment.
PREFIX = r"^[a-z](?:[a-z0-9-]*[a-z0-9])?$"
