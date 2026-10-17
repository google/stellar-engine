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
import subprocess
from subprocess import run as sp_run

user = input()
cmd = "echo " + user
# ruleid: python-os-command-injection
os.system(cmd)
# ruleid: python-os-command-injection
subprocess.run(cmd, shell=True)
# ruleid: python-os-command-injection
sp_run(cmd, shell=True)
# ruleid: python-os-command-injection
subprocess.Popen(cmd, shell=True)
# ruleid: python-os-command-injection
os.popen(cmd)
# ok: python-os-command-injection
subprocess.run(["echo", user])
# ok: python-os-command-injection
os.system("true")
# ok: python-os-command-injection
subprocess.run("true", shell=True)
