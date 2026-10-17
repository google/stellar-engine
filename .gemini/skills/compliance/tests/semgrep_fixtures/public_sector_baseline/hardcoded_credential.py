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

# flake8: noqa
# Intentionally insecure scanner fixture for `semgrep --test`; never imported or executed.
# A "ruleid" annotation marks the next line as a required match; an "ok" annotation marks it as forbidden.

import os

# ruleid: python-hardcoded-credential-assignment
password = "fixture-not-a-credential"
# ruleid: python-hardcoded-credential-assignment
DB_PASSWORD = "fixture-not-a-credential"
# ruleid: python-hardcoded-credential-assignment
CLIENT_SECRET = "fixture-not-a-credential"


class Cfg:
    def __init__(self):
        # ruleid: python-hardcoded-credential-assignment
        self.password = "fixture-not-a-credential"


# ruleid: python-hardcoded-credential-assignment
settings = {"password": "fixture-not-a-credential"}
# ok: python-hardcoded-credential-assignment
password_env = os.environ["DB_PASSWORD"]
# ok: python-hardcoded-credential-assignment
PASSWORD_ENV = "DB_PASSWORD"
# ok: python-hardcoded-credential-assignment
TOKEN_TYPE = "Bearer"
# ok: python-hardcoded-credential-assignment
api_key = "<your-api-key>"
# ok: python-hardcoded-credential-assignment
DB_PASSWORD_PLACEHOLDER = "[CONFIG_REQUIRED]"
# ok: python-hardcoded-credential-assignment
CSRF_TOKEN = "csrf_token"
# ok: python-hardcoded-credential-assignment
headers = {"password": os.environ.get("APP_PASSWORD")}
