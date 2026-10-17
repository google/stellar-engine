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

from flask import Flask, request

app = Flask(__name__)
BASE = "/srv/files"


@app.route("/a")
def a():
    # ruleid: python-path-traversal-unvalidated-join
    return open(os.path.join(BASE, request.args.get("f"))).read()


@app.route("/b")
def b():
    name = request.args["f"]
    p = os.path.join(BASE, name)
    # ruleid: python-path-traversal-unvalidated-join
    return open(p).read()


@app.route("/c")
def c():
    # ruleid: python-path-traversal-unvalidated-join
    return open(request.form["path"]).read()


@app.route("/d")
def d():
    # ok: python-path-traversal-unvalidated-join
    return open(os.path.join(BASE, "static.txt")).read()
