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

import sqlite3

cur = sqlite3.connect(":memory:").cursor()
user = input()
# ruleid: python-sql-injection-string-built-query
cur.execute("SELECT * FROM t WHERE n = '%s'" % user)
# ruleid: python-sql-injection-string-built-query
cur.execute("SELECT * FROM t WHERE n = '" + user + "'")
# ruleid: python-sql-injection-string-built-query
cur.execute(f"SELECT * FROM t WHERE n = '{user}'")
# ruleid: python-sql-injection-string-built-query
cur.execute("SELECT * FROM t WHERE n = '{}'".format(user))
q = "SELECT * FROM t WHERE n = '" + user + "'"
# ruleid: python-sql-injection-string-built-query
cur.execute(q)
q2 = f"DELETE FROM t WHERE n = '{user}'"
# ruleid: python-sql-injection-string-built-query
cur.executemany(q2, [])
# ok: python-sql-injection-string-built-query
cur.execute("SELECT * FROM t WHERE n = ?", (user,))
# ok: python-sql-injection-string-built-query
cur.execute("SELECT 1")
q3 = "SELECT * FROM t WHERE n = ?"
# ok: python-sql-injection-string-built-query
cur.execute(q3, (user,))
