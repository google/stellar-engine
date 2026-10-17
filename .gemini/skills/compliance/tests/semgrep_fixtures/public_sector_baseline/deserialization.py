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

import marshal
import pickle

import yaml

data = b"fixture"
# ruleid: python-insecure-deserialization
o1 = pickle.loads(data)
# ruleid: python-insecure-deserialization
o2 = yaml.load(data)
# ruleid: python-insecure-deserialization
o3 = yaml.load(data, Loader=yaml.UnsafeLoader)
# ruleid: python-insecure-deserialization
o4 = pickle.Unpickler(open("state.bin", "rb")).load()
# ruleid: python-insecure-deserialization
o5 = marshal.loads(data)
# ruleid: python-insecure-deserialization
o6 = yaml.unsafe_load(data)
# ok: python-insecure-deserialization
p1 = yaml.safe_load(data)
# ok: python-insecure-deserialization
p2 = yaml.load(data, Loader=yaml.SafeLoader)
# ok: python-insecure-deserialization
p3 = pickle.dumps(data)
