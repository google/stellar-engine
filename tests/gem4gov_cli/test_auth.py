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

import subprocess
import unittest
from unittest.mock import MagicMock, patch

import auth


class TestAuth(unittest.TestCase):

  def test_required_permissions_defined(self):
    self.assertTrue(len(auth.required_permissions) > 0)
    self.assertIn('discoveryengine.engines.create', auth.required_permissions)
    self.assertIn('aiplatform.datasets.create', auth.required_permissions)
    self.assertIn('serviceusage.services.enable', auth.required_permissions)
    self.assertIn('storage.buckets.create', auth.required_permissions)
    self.assertIn('bigquery.datasets.create', auth.required_permissions)

  @patch('auth.build')
  def test_check_roles_all_granted(self, mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_test_iam = mock_service.projects().testIamPermissions()
    mock_test_iam.execute.return_value = {
        'permissions': list(auth.required_permissions)
    }

    mock_creds = MagicMock()
    result = auth.check_roles(mock_creds, 'test-project-123')
    self.assertTrue(result)
    mock_build.assert_called_with('cloudresourcemanager', 'v1', credentials=mock_creds)

  @patch('auth.build')
  def test_check_roles_missing_permissions(self, mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_test_iam = mock_service.projects().testIamPermissions()
    # Return only one permission granted
    mock_test_iam.execute.return_value = {
        'permissions': ['discoveryengine.engines.create']
    }

    mock_creds = MagicMock()
    result = auth.check_roles(mock_creds, 'test-project-123')
    self.assertFalse(result)

  @patch('subprocess.run')
  def test_get_user_email_success(self, mock_run):
    mock_proc = MagicMock()
    mock_proc.stdout = 'user@example.com\n'
    mock_run.return_value = mock_proc

    email = auth.get_user_email(MagicMock())
    self.assertEqual(email, 'user@example.com')

  @patch('subprocess.run')
  def test_get_user_email_failure(self, mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, 'gcloud')

    with self.assertRaises(SystemExit):
      auth.get_user_email(MagicMock())

  @patch('subprocess.run')
  @patch('auth.google.auth.default')
  def test_get_credentials(self, mock_default, mock_run):
    mock_creds = MagicMock()
    mock_default.return_value = (mock_creds, 'dummy-project')

    creds = auth.get_credentials()
    self.assertEqual(creds, mock_creds)
    mock_default.assert_called_with(scopes=['https://www.googleapis.com/auth/cloud-platform'])


if __name__ == '__main__':
  unittest.main()
