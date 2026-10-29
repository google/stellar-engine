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

"""Queries the operator's local command line tools."""

import json
import shutil
import subprocess
from typing import Protocol

_TIMEOUT_SECONDS = 30


class LocalTools(Protocol):
    """Local tool queries used by preflight checks and rendering."""

    def terraform_version(self) -> str | None:
        """Returns the installed Terraform version, or None if missing."""
        ...

    def gcloud_version(self) -> str | None:
        """Returns the installed Google Cloud SDK version, or None."""
        ...

    def gcloud_account(self) -> str | None:
        """Returns the active gcloud account, or None if none is set."""
        ...

    def gcloud_project(self) -> str | None:
        """Returns the active gcloud project, or None if none is set."""
        ...

    def jq_version(self) -> str | None:
        """Returns the installed jq version, or None if missing."""
        ...

    def terraform_fmt(self, text: str) -> str | None:
        """Returns `text` formatted by `terraform fmt`.

        Returns None when Terraform is missing or rejects the text.
        """
        ...


def _run(args, stdin=None):
    """Runs a command and returns its stdout, or None on any failure."""
    if shutil.which(args[0]) is None:
        return None
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            check=True,
            input=stdin,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except OSError, subprocess.SubprocessError:
        return None
    return completed.stdout


class SystemTools:
    """Reads tool versions and the gcloud account from the local system."""

    def terraform_version(self):
        """See `LocalTools.terraform_version`."""
        output = _run(["terraform", "version", "-json"])
        if output is None:
            return None
        return json.loads(output).get("terraform_version")

    def gcloud_version(self):
        """See `LocalTools.gcloud_version`."""
        output = _run(["gcloud", "version", "--format=json"])
        if output is None:
            return None
        return json.loads(output).get("Google Cloud SDK")

    def gcloud_account(self):
        """See `LocalTools.gcloud_account`."""
        output = _run(["gcloud", "config", "get-value", "account"])
        return (output or "").strip() or None

    def gcloud_project(self):
        """See `LocalTools.gcloud_project`."""
        output = _run(["gcloud", "config", "get-value", "project"])
        return (output or "").strip() or None

    def jq_version(self):
        """See `LocalTools.jq_version`."""
        return (_run(["jq", "--version"]) or "").strip() or None

    def terraform_fmt(self, text):
        """See `LocalTools.terraform_fmt`."""
        # `terraform fmt -` reads stdin and needs no configuration directory.
        return _run(["terraform", "fmt", "-"], stdin=text)
