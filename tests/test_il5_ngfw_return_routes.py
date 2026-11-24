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

"""Checks the NGFW return routes to the spoke VPC ranges in Stage 2b.

The firewalls have a default route on the DMZ interface only, so every range
that a spoke can send traffic from needs a static route on the trusted
interface. The rendering tests run the stage's route locals and the bootstrap
template through the real Terraform binary, with a stub in place of the spoke
VPC module so that no provider or credential is needed.
"""

import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest
from xml.etree import ElementTree

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_IL5_NET_DIR = _REPO_ROOT / "fast/stages-aw/2-networking-b-il5-ngfw"
_ROUTES_TF = _IL5_NET_DIR / "ngfw-routes.tf"
_TEMPLATE = _IL5_NET_DIR / "templates/bootstrap.xml.tpl"
_NET_VPC_OUTPUTS = (
    "subnet_ips",
    "subnet_secondary_ranges",
    "subnets_proxy_only",
)
_GATEWAY = "10.64.0.1"
# PAN-OS accepts up to 31 characters for a static route name.
_MAX_ROUTE_NAME = 31

# Stands in for modules/net-vpc: the same three outputs, fed from variables.
_NET_VPC_STUB = """
variable "subnet_ips" {
  type = map(string)
}

variable "subnet_secondary_ranges" {
  type = map(map(string))
}

variable "proxy_only" {
  type = map(string)
}

output "subnet_ips" {
  value = var.subnet_ips
}

output "subnet_secondary_ranges" {
  value = var.subnet_secondary_ranges
}

output "subnets_proxy_only" {
  value = { for k, v in var.proxy_only : k => { ip_cidr_range = v } }
}
"""

# Supplies what ngfw-routes.tf reads, and renders the template the way the
# bootstrap_xml object in ngfw.tf does.
_HARNESS = (
    """
variable "envs_folders" {
  type = map(object({ admin = string }))
}

variable "spokes" {
  type = map(object({
    subnet_ips              = map(string)
    subnet_secondary_ranges = map(map(string))
    proxy_only              = map(string)
  }))
}

variable "template" {
  type = string
}

module "env-spoke-vpc" {
  source                  = "./net-vpc-stub"
  for_each                = var.envs_folders
  subnet_ips              = var.spokes[each.key].subnet_ips
  subnet_secondary_ranges = var.spokes[each.key].subnet_secondary_ranges
  proxy_only              = var.spokes[each.key].proxy_only
}

output "bootstrap_xml" {
  value = templatefile(var.template, {
    password_hash            = "hash"
    ssh_pubkey               = "ssh-rsa key"
    healthcheck_cidrs        = ["35.191.0.0/16"]
    iap_cidrs                = ["35.235.240.0/20"]
    return_routes            = local.ngfw_return_routes
    lz_gateway_ip            = "%s"
    min_password_length      = 12
    timezone                 = "US/Pacific"
    login_banner             = ""
    enable_https_healthcheck = false
  })
}
"""
    % _GATEWAY
)


def _spoke(subnet_ips=None, secondary=None, proxy_only=None):
    """Returns the outputs of one spoke VPC, keyed the way net-vpc does."""
    return {
        "subnet_ips": subnet_ips or {},
        "subnet_secondary_ranges": secondary or {},
        "proxy_only": proxy_only or {},
    }


class TestIl5NgfwReturnRouteWiring(unittest.TestCase):
    def test_bootstrap_xml_renders_the_route_locals(self):
        ngfw_tf = (_IL5_NET_DIR / "ngfw.tf").read_text(encoding="utf-8")
        self.assertRegex(
            ngfw_tf, r"(?m)^\s*return_routes\s*=\s*local\.ngfw_return_routes$"
        )
        # The lookup that kept only the first tenant subnet of an environment.
        self.assertNotIn("tenants_subnets", ngfw_tf)
        self.assertNotIn("tenants_subnets", _TEMPLATE.read_text("utf-8"))

    def test_routes_read_every_kind_of_spoke_range(self):
        routes_tf = _ROUTES_TF.read_text(encoding="utf-8")
        outputs_tf = (_REPO_ROOT / "modules/net-vpc/outputs.tf").read_text(
            encoding="utf-8"
        )
        for output in _NET_VPC_OUTPUTS:
            with self.subTest(output=output):
                self.assertIn(f"module.env-spoke-vpc[k].{output}", routes_tf)
                # The stub in this file mirrors these net-vpc outputs.
                self.assertIn(f'output "{output}"', outputs_tf)

    def test_trusted_interface_has_no_default_route(self):
        # This is why the static routes matter: without one, a reply follows
        # the DMZ interface's default route.
        text = re.sub(r"%\{[^}]*\}", "", _TEMPLATE.read_text("utf-8"))
        root = ElementTree.fromstring(re.sub(r"\$\{[^}]*\}", "x", text))
        interfaces = root.find(".//network/interface/ethernet")
        trusted = interfaces.find("entry[@name='ethernet1/2']/layer3")
        self.assertEqual(
            trusted.findtext("dhcp-client/create-default-route"), "no"
        )
        self.assertEqual(
            [e.text for e in root.findall(".//static-route/entry/interface")],
            ["ethernet1/2"],
        )


class TestIl5NgfwReturnRouteRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("terraform"):
            raise unittest.SkipTest("terraform is required to render routes")
        cls._tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._tmp.cleanup)
        cls.workdir = pathlib.Path(cls._tmp.name)
        shutil.copy(_ROUTES_TF, cls.workdir / "ngfw-routes.tf")
        (cls.workdir / "harness.tf").write_text(_HARNESS, encoding="utf-8")
        stub = cls.workdir / "net-vpc-stub"
        stub.mkdir()
        (stub / "main.tf").write_text(_NET_VPC_STUB, encoding="utf-8")
        cls._terraform("init", "-backend=false", "-input=false")

    @classmethod
    def _terraform(cls, *args):
        result = subprocess.run(
            ["terraform", *args],
            cwd=cls.workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"terraform {args[0]} failed:\n{result.stdout}{result.stderr}"
            )
        return result.stdout

    def _render(self, spokes):
        """Plans the harness and returns the (name, CIDR) of each route."""
        variables = {
            "envs_folders": {env: {"admin": "admin"} for env in spokes},
            "spokes": spokes,
            "template": str(_TEMPLATE),
        }
        (self.workdir / "case.tfvars.json").write_text(
            json.dumps(variables), encoding="utf-8"
        )
        self._terraform(
            "plan", "-input=false", "-var-file=case.tfvars.json", "-out=plan"
        )
        plan = json.loads(self._terraform("show", "-json", "plan"))
        xml = plan["planned_values"]["outputs"]["bootstrap_xml"]["value"]
        root = ElementTree.fromstring(xml)
        entries = root.findall(".//routing-table/ip/static-route/entry")
        for entry in entries:
            self.assertEqual(entry.findtext("interface"), "ethernet1/2")
            self.assertEqual(entry.findtext("nexthop/ip-address"), _GATEWAY)
        return [(e.get("name"), e.findtext("destination")) for e in entries]

    def _assert_valid_names(self, routes):
        names = [name for name, _ in routes]
        self.assertEqual(len(names), len(set(names)))
        for name in names:
            with self.subTest(name=name):
                self.assertLessEqual(len(name), _MAX_ROUTE_NAME)
                self.assertRegex(name, r"^[A-Za-z0-9][A-Za-z0-9-]*$")

    def test_every_spoke_range_gets_a_route(self):
        routes = self._render(
            {
                "Dev": _spoke(
                    subnet_ips={"us-east4/dev-tenant-1": "10.150.0.0/16"},
                    proxy_only={"us-east4/proxy-us-east4": "10.1.2.0/24"},
                ),
                "Prod": _spoke(
                    subnet_ips={
                        "us-east4/prod-tenant-1": "10.250.0.0/16",
                        "us-east4/prod-tenant-2": "10.200.0.0/16",
                        # Not shared with a tenant, and in another region.
                        "us-central1/prod-shared": "10.201.0.0/24",
                    },
                    secondary={
                        "us-east4/prod-tenant-1": {},
                        "us-east4/prod-tenant-2": {
                            "pods": "100.64.0.0/14",
                            "services": "100.68.0.0/20",
                        },
                        "us-central1/prod-shared": {},
                    },
                    proxy_only={"us-east4/proxy-us-east4": "10.1.1.0/24"},
                ),
            }
        )
        self.assertEqual(
            sorted(routes),
            [
                ("Dev-10-1-2-0-24", "10.1.2.0/24"),
                ("Dev-10-150-0-0-16", "10.150.0.0/16"),
                ("Prod-10-1-1-0-24", "10.1.1.0/24"),
                ("Prod-10-200-0-0-16", "10.200.0.0/16"),
                ("Prod-10-201-0-0-24", "10.201.0.0/24"),
                ("Prod-10-250-0-0-16", "10.250.0.0/16"),
                ("Prod-100-64-0-0-14", "100.64.0.0/14"),
                ("Prod-100-68-0-0-20", "100.68.0.0/20"),
            ],
        )
        self._assert_valid_names(routes)

    def test_long_environment_names_stay_within_the_name_limit(self):
        # Both names share their first 12 characters, which is all that an
        # 18-character CIDR, the longest possible, leaves free.
        routes = self._render(
            {
                "Preproduction-East": _spoke(
                    subnet_ips={"us-east4/a": "192.168.100.128/25"},
                    proxy_only={"us-east4/proxy": "192.168.101.128/25"},
                ),
                "Preproduction-West": _spoke(
                    subnet_ips={"us-west1/a": "192.168.102.128/25"},
                    proxy_only={"us-west1/proxy": "10.0.0.0/8"},
                ),
            }
        )
        self.assertEqual(
            sorted(routes),
            [
                ("Preproductio-192-168-100-128-25", "192.168.100.128/25"),
                ("Preproductio-192-168-101-128-25", "192.168.101.128/25"),
                ("Preproductio-192-168-102-128-25", "192.168.102.128/25"),
                # A shorter CIDR leaves room for the whole name.
                ("Preproduction-West-10-0-0-0-8", "10.0.0.0/8"),
            ],
        )
        self.assertEqual(max(len(name) for name, _ in routes), _MAX_ROUTE_NAME)
        self._assert_valid_names(routes)

    def test_missing_and_repeated_ranges_do_not_break_the_routes(self):
        routes = self._render(
            {
                # No subnet at all.
                "Empty": _spoke(),
                "Int": _spoke(
                    subnet_ips={
                        "us-east4/int-tenant-1": "10.160.0.0/16",
                        # An IPv6-only subnet has no IPv4 range.
                        "us-east4/int-ipv6": None,
                    },
                    proxy_only={"us-east4/proxy": "10.1.3.0/24"},
                ),
                # The same range again resolves to a single route.
                "Test": _spoke(
                    subnet_ips={"us-east4/test-tenant-1": "10.160.0.0/16"},
                ),
            }
        )
        self.assertEqual(
            sorted(routes),
            [
                ("Int-10-1-3-0-24", "10.1.3.0/24"),
                ("Int-10-160-0-0-16", "10.160.0.0/16"),
            ],
        )
        self._assert_valid_names(routes)


if __name__ == "__main__":
    unittest.main()
