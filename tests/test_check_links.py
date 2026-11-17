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

import pathlib
import types
import unittest
import unittest.mock

import check_links


def _fake_link(dest):
    return types.SimpleNamespace(dest=dest)


def _fake_response(status_code=200, location=None):
    headers = {"Location": location} if location is not None else {}
    return types.SimpleNamespace(
        status_code=status_code,
        ok=(200 <= status_code < 400),
        is_redirect=(status_code in (301, 302, 303, 307, 308)),
        headers=headers,
    )


class CheckLinksRedirectTest(unittest.TestCase):
    def test_follows_validated_public_redirect(self):
        readme = pathlib.Path("/tmp/README.md")

        def fake_addrinfo(host, _port):
            return [(0, 0, 0, "", ("93.184.216.34", 0))]

        responses = [
            _fake_response(302, "https://example.org/target"),
            _fake_response(200),
        ]
        with (
            unittest.mock.patch(
                "socket.getaddrinfo", side_effect=fake_addrinfo
            ),
            unittest.mock.patch(
                "requests.get", side_effect=responses
            ) as mock_get,
        ):
            res = check_links.check_link(
                _fake_link("https://example.com/start"), readme, external=True
            )

        self.assertTrue(res.valid)
        self.assertEqual(mock_get.call_count, 2)
        for call in mock_get.call_args_list:
            self.assertFalse(call.kwargs["allow_redirects"])

    def test_blocks_redirect_to_private_or_link_local_ip(self):
        readme = pathlib.Path("/tmp/README.md")

        def fake_addrinfo(host, _port):
            if host == "example.com":
                return [(0, 0, 0, "", ("93.184.216.34", 0))]
            return [(0, 0, 0, "", ("169.254.169.254", 0))]

        with (
            unittest.mock.patch(
                "socket.getaddrinfo", side_effect=fake_addrinfo
            ),
            unittest.mock.patch(
                "requests.get",
                return_value=_fake_response(
                    302, "http://metadata.internal/computeMetadata/v1/"
                ),
            ) as mock_get,
        ):
            res = check_links.check_link(
                _fake_link("https://example.com/start"), readme, external=True
            )

        self.assertFalse(res.valid)
        self.assertEqual(mock_get.call_count, 1)

    def test_blocks_redirect_to_non_http_scheme_and_excess_hops(self):
        readme = pathlib.Path("/tmp/README.md")
        public_ip = [(0, 0, 0, "", ("93.184.216.34", 0))]

        with (
            unittest.mock.patch("socket.getaddrinfo", return_value=public_ip),
            unittest.mock.patch(
                "requests.get",
                return_value=_fake_response(302, "file:///etc/passwd"),
            ),
        ):
            res = check_links.check_link(
                _fake_link("https://example.com/start"), readme, external=True
            )
        self.assertFalse(res.valid)

        with (
            unittest.mock.patch("socket.getaddrinfo", return_value=public_ip),
            unittest.mock.patch(
                "requests.get",
                return_value=_fake_response(302, "https://example.com/loop"),
            ) as loop_get,
        ):
            loop_res = check_links.check_link(
                _fake_link("https://example.com/start"), readme, external=True
            )
        self.assertFalse(loop_res.valid)
        self.assertEqual(loop_get.call_count, check_links.MAX_REDIRECTS + 1)


if __name__ == "__main__":
    unittest.main()
