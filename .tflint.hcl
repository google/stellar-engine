// Copyright 2025 Google LLC
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

plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

rule "terraform_required_providers" {
  enabled = false
}

rule "terraform_required_version" {
  enabled = false
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"

  custom_formats = {
    private_snake = {
      description = "snake_case with leading _"
      regex       = "^[_a-z][a-z0-9_]*$"
    }
    kebab = {
      description = "lower kebab case"
      regex       = "^[a-z][a-z0-9-]*$"
    }
  }

  locals {
    format = "private_snake"
  }

  module {
    format = "kebab"
  }
}
