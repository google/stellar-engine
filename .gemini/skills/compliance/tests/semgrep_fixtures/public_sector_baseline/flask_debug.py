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

import asyncio

from flask import Flask

app = Flask(__name__)
# ruleid: python-flask-debug-enabled
app.run(debug=True)
# ruleid: python-flask-debug-enabled
app.config["DEBUG"] = True
# ruleid: python-flask-debug-enabled
app.debug = True
# ok: python-flask-debug-enabled
app.run(debug=False)
# ok: python-flask-debug-enabled
asyncio.run(asyncio.sleep(0), debug=True)
