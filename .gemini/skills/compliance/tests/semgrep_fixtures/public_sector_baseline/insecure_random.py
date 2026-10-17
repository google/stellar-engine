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

import random
import secrets


def generate_token():
    # ruleid: python-insecure-random-for-security
    return random.getrandbits(64)


def generate_session_token():
    # ruleid: python-insecure-random-for-security
    return "".join(random.choices("abcdef0123456789", k=32))


def get_session_key():
    # ruleid: python-insecure-random-for-security
    return random.randint(0, 2**32)


def make_password():
    # ruleid: python-insecure-random-for-security
    return "".join(random.choice("ab") for _ in range(8))


def new_reset_code():
    # ruleid: python-insecure-random-for-security
    return random.randint(0, 999999)


def new_session_id():
    # ruleid: python-insecure-random-for-security
    return random.getrandbits(128)


# ruleid: python-insecure-random-for-security
reset_pin = random.randint(0, 9999)
# ruleid: python-insecure-random-for-security
api_key = "%032x" % random.getrandbits(128)


def session_retry_jitter_ms():
    # ok: python-insecure-random-for-security
    return random.randint(0, 100)


def shuffle_display_order(items):
    # ok: python-insecure-random-for-security
    return random.choice(items)


def generate_api_key():
    # ok: python-insecure-random-for-security
    return random.SystemRandom().getrandbits(128)


def generate_csrf_token():
    # ok: python-insecure-random-for-security
    return secrets.token_hex(16)


# ok: python-insecure-random-for-security
backoff_ms = random.randint(0, 250)
