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

required_roles = [
    'roles/discoveryengine.admin',
    'roles/aiplatform.admin',
    'roles/serviceusage.serviceUsageAdmin',
    'roles/storage.admin',
    'roles/bigquery.admin'
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
    """Checks if the user has the required roles."""
    service = build('cloudresourcemanager', 'v1', credentials=credentials)
    policy = service.projects().getIamPolicy(resource=project_id).execute()
    user_email = get_user_email(credentials)
    user_roles = []
    for binding in policy.get('bindings', []):
        if user_email in [member.split(':', 1)[1] for member in binding.get('members', []) if ':' in member]:
            user_roles.append(binding['role'])

    missing_roles = [role for role in required_roles if role not in user_roles]

    if missing_roles:
        click.echo("You are missing the following required roles:")
        for role in missing_roles:
            click.echo(f"- {role}")
        return False
    click.echo("Role validation successful.")
    return True
