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
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class TestModuleAndBlueprintHardening(unittest.TestCase):
    def test_networking_vpn_lb_and_cos_modules_hardening(self):
        """Verify VPN, load balancer, firewall, and COS module hardening."""
        for vpn_mod in (
            "net-vpn-dynamic",
            "net-vpn-ha",
            "net-vpn-static",
            "net-ipsec-over-interconnect",
        ):
            vpn_main = (REPO_ROOT / f"modules/{vpn_mod}/main.tf").read_text(
                encoding="utf-8"
            )
            self.assertIn("byte_length = 32", vpn_main)

        for hc_mod in ("compute-mig", "net-lb-ext"):
            hc_tf = (REPO_ROOT / f"modules/{hc_mod}/health-check.tf").read_text(
                encoding="utf-8"
            )
            self.assertIn("local.hc.http2.host", hc_tf)
            self.assertIn("local.hc.ssl.port", hc_tf)

        for lb_mod in (
            "net-lb-app-ext",
            "net-lb-app-ext-regional",
            "net-lb-app-int",
            "net-lb-app-int-cross-region",
        ):
            urlmap_tf = (REPO_ROOT / f"modules/{lb_mod}/urlmap.tf").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                'present_match = h.value.type == "present" ? true : null',
                urlmap_tf,
            )

        fw_rules = (
            REPO_ROOT / "modules/net-vpc-firewall/default-rules.tf"
        ).read_text(encoding="utf-8")
        self.assertIn("length(local.default_rules.http_tags) > 0", fw_rules)
        self.assertIn("length(local.default_rules.https_tags) > 0", fw_rules)
        self.assertIn("length(local.default_rules.ssh_tags) > 0", fw_rules)

        bc_main = (REPO_ROOT / "modules/beyondcorp/main.tf").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("ENCRYPTION_UNSUPPORTED", bc_main)
        self.assertIn("request.auth.access_levels", bc_main)


if __name__ == "__main__":
    unittest.main()
