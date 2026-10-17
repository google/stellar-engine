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

import hashlib
import hashlib as hl
from hashlib import md5
from hashlib import sha1 as hl_sha1

data = b"fixture"

# ruleid: python-weak-hash-algorithm
h1 = hashlib.md5(data)
# ruleid: python-weak-hash-algorithm
h2 = hashlib.sha1(data)
# ruleid: python-weak-hash-algorithm
h3 = hashlib.new("md5")
# ruleid: python-weak-hash-algorithm
h4 = hashlib.new("MD5")
# ruleid: python-weak-hash-algorithm
h5 = hashlib.new(name="sha1")
# ruleid: python-weak-hash-algorithm
h6 = hl.md5(data)
# ruleid: python-weak-hash-algorithm
h7 = md5(data)
# ruleid: python-weak-hash-algorithm
h8 = hl_sha1(data)
# ok: python-weak-hash-algorithm
n1 = hashlib.md5(data, usedforsecurity=False)
# ok: python-weak-hash-algorithm
n2 = hashlib.sha256(data)
# ok: python-weak-hash-algorithm
n3 = hashlib.new("sha256")


class Checksums:
    def md5(self, path):
        return path


# ok: python-weak-hash-algorithm
n4 = Checksums().md5("file.txt")
