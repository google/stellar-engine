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

import json
import unittest
from unittest.mock import MagicMock, patch

import data_stores


class TestDataStores(unittest.TestCase):

  def test_generate_id_format(self):
    prefix = "ds-"
    gen_id = data_stores.generate_id(prefix)
    self.assertTrue(gen_id.startswith(prefix))
    self.assertEqual(len(gen_id), len(prefix) + 6)
    suffix = gen_id[len(prefix):]
    self.assertTrue(suffix.isalnum())
    self.assertTrue(suffix.islower())

  def test_generate_id_uniqueness(self):
    prefix = "test-"
    id1 = data_stores.generate_id(prefix)
    id2 = data_stores.generate_id(prefix)
    self.assertNotEqual(id1, id2)

  def test_parse_http_error_valid_json(self):
    mock_error = MagicMock()
    error_payload = json.dumps({"error": {"message": "The requested entity was not found."}}).encode("utf-8")
    mock_error.content = error_payload

    msg = data_stores.parse_http_error(mock_error)
    self.assertEqual(msg, "The requested entity was not found.")

  def test_parse_http_error_missing_message(self):
    mock_error = MagicMock()
    error_payload = json.dumps({"error": {}}).encode("utf-8")
    mock_error.content = error_payload

    msg = data_stores.parse_http_error(mock_error)
    self.assertEqual(msg, "No error message found.")

  def test_parse_http_error_invalid_json(self):
    mock_error = MagicMock()
    mock_error.content = b"Not JSON content"
    mock_error.__str__.return_value = "HTTP 500: Server Error"

    msg = data_stores.parse_http_error(mock_error)
    self.assertIn("HTTP 500", msg)

  @patch('data_stores.build')
  def test_validate_data_store_generic_valid(self, mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_ds_req = mock_service.projects().locations().dataStores().get()
    mock_ds_req.execute.return_value = {
        'name': 'projects/p1/locations/us/dataStores/ds-123',
        'displayName': 'Test DS',
        'industryVertical': 'GENERIC',
        'solutionTypes': ['SOLUTION_TYPE_SEARCH'],
        'cmekConfig': {'kmsKey': 'projects/p1/locations/us/keyRings/kr/cryptoKeys/k1'},
        'aclEnabled': True,
        'contentConfig': 'CONTENT_REQUIRED'
    }

    res = data_stores.validate_data_store(MagicMock(), 'p1', 'ds-123')
    self.assertTrue(res['valid'])
    self.assertEqual(res['id'], 'ds-123')
    self.assertEqual(res['display_name'], 'Test DS')
    self.assertEqual(res['industry_vertical'], 'GENERIC')

  @patch('data_stores.build')
  def test_validate_data_store_non_generic_invalid(self, mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_ds_req = mock_service.projects().locations().dataStores().get()
    mock_ds_req.execute.return_value = {
        'name': 'projects/p1/locations/us/dataStores/ds-456',
        'displayName': 'Media DS',
        'industryVertical': 'MEDIA'
    }

    res = data_stores.validate_data_store(MagicMock(), 'p1', 'ds-456')
    self.assertFalse(res['valid'])
    self.assertEqual(res['id'], 'ds-456')

  @patch('data_stores.build')
  def test_validate_data_store_exception_handling(self, mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_ds_req = mock_service.projects().locations().dataStores().get()
    mock_ds_req.execute.side_effect = Exception("API connection error")

    res = data_stores.validate_data_store(MagicMock(), 'p1', 'ds-error')
    self.assertFalse(res['valid'])
    self.assertEqual(res['id'], 'ds-error')


if __name__ == '__main__':
  unittest.main()
