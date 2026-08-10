# Copyright 2026 Google Inc.
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

import click
import google.auth
from googleapiclient.discovery import build
import subprocess

# Representative permissions from each required role.
# testIamPermissions checks effective permissions, so Owner, custom roles,
# and group-inherited bindings all pass correctly — unlike getIamPolicy
# which only matches direct user: bindings by role name.
required_permissions = [
    'discoveryengine.engines.create',
    'aiplatform.datasets.create',
    'serviceusage.services.enable',
    'storage.buckets.create',
    'bigquery.datasets.create',
]

def get_credentials():
    """Gets user credentials for Google Cloud."""
    try:
        # Check if the user is authenticated
        subprocess.run(['gcloud', 'auth', 'print-access-token'], check=True, capture_output=True)
        subprocess.run(['gcloud', 'auth', 'application-default', 'print-access-token'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("You are not logged in. Running 'gcloud auth login' and 'gcloud auth application-default login'...")
        subprocess.run(['gcloud', 'auth', 'login'])
        subprocess.run(['gcloud', 'auth', 'application-default', 'login'])

    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    return credentials

def force_reauthentication():
    """Forces user to re-authenticate with Google Cloud."""
    click.echo("Forcing re-authentication. Please follow the prompts from gcloud.")
    subprocess.run(['gcloud', 'auth', 'login'])
    subprocess.run(['gcloud', 'auth', 'application-default', 'login'])

def get_user_email(credentials):
    """Gets the user's email from the gcloud config."""
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'account'], check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("Could not determine your email address. Please ensure you are logged in with a user account.")
        exit()

def check_roles(credentials, project_id):
    """Checks if the user has the required permissions using testIamPermissions.

    Uses testIamPermissions rather than getIamPolicy so that effective
    permissions granted via roles/owner, custom roles, or group membership
    are correctly recognised. getIamPolicy only matched direct user: bindings
    by role name, causing false "missing roles" warnings for those cases.
    """
    service = build('cloudresourcemanager', 'v1', credentials=credentials)
    body = {'permissions': required_permissions}
    response = service.projects().testIamPermissions(resource=project_id, body=body).execute()
    granted = response.get('permissions', [])
    missing = [p for p in required_permissions if p not in granted]

    if missing:
        click.echo("You are missing the following required permissions:")
        for p in missing:
            click.echo(f"- {p}")
        return False
    click.echo("Role validation successful.")
    return True
