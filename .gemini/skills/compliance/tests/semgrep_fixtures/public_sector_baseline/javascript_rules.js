// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Intentionally insecure scanner fixture for `semgrep --test`; never imported or executed.
// A "ruleid" annotation marks the next line as a required match; an "ok" annotation marks it as forbidden.

const https = require("https");
const userInput = process.argv[2];

// ruleid: javascript-eval-of-dynamic-input
eval(userInput);
// ruleid: javascript-eval-of-dynamic-input
const f = new Function("a", userInput);
// ruleid: javascript-eval-of-dynamic-input
setTimeout("run(" + userInput + ")", 10);
// ok: javascript-eval-of-dynamic-input
eval("1 + 1");
// ok: javascript-eval-of-dynamic-input
setTimeout(() => console.log(userInput), 10);

// ruleid: javascript-disabled-tls-verification
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
// ruleid: javascript-disabled-tls-verification
const agent = new https.Agent({ rejectUnauthorized: false });
const opts = {};
// ruleid: javascript-disabled-tls-verification
opts.rejectUnauthorized = false;
// ok: javascript-disabled-tls-verification
const safe = new https.Agent({ rejectUnauthorized: true });
