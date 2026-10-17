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

package main

import (
	"crypto"
	"crypto/md5"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/tls"
	"net/http"
)

func main() {
	data := []byte("fixture")
	// ruleid: go-weak-hash-algorithm
	_ = md5.Sum(data)
	// ruleid: go-weak-hash-algorithm
	_ = sha1.New()
	// ruleid: go-weak-hash-algorithm
	_ = crypto.MD5.New()
	// ok: go-weak-hash-algorithm
	_ = sha256.Sum256(data)

	// ruleid: go-disabled-tls-verification
	c1 := &tls.Config{InsecureSkipVerify: true}
	// ruleid: go-disabled-tls-verification
	tr := &http.Transport{TLSClientConfig: &tls.Config{MinVersion: tls.VersionTLS12, InsecureSkipVerify: true}}
	c2 := &tls.Config{}
	// ruleid: go-disabled-tls-verification
	c2.InsecureSkipVerify = true
	// ok: go-disabled-tls-verification
	c3 := &tls.Config{InsecureSkipVerify: false}
	_, _, _, _ = c1, tr, c2, c3
}
