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

import ssl
import urllib.request

import httpx
import requests

# ruleid: python-disabled-tls-verification
r1 = requests.get("https://example.invalid", verify=False)
sess = requests.Session()
# ruleid: python-disabled-tls-verification
r2 = sess.get("https://example.invalid", verify=False)
# ruleid: python-disabled-tls-verification
sess.verify = False
ctx = ssl.create_default_context()
# ruleid: python-disabled-tls-verification
ctx.verify_mode = ssl.CERT_NONE
# ruleid: python-disabled-tls-verification
c1 = httpx.Client(verify=False)
# ruleid: python-disabled-tls-verification
c2 = ssl._create_unverified_context()
# ok: python-disabled-tls-verification
r3 = requests.get("https://example.invalid", verify="/etc/ssl/ca.pem")
# ok: python-disabled-tls-verification
r4 = requests.get("https://example.invalid", verify=True)
# ok: python-disabled-tls-verification
sess.verify = "/etc/ssl/ca.pem"
