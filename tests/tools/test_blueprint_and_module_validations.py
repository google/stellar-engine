# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for blueprint API enablement and module ID length preconditions."""

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class TestBlueprintAndModuleValidations(unittest.TestCase):
  """Verify API enablement in blueprints and 30-char ID preconditions in modules."""

  def test_blueprints_enable_required_project_services(self):
    """Ensure app-engine and postgresql blueprints enable required APIs (#104)."""
    ae_tf = (
        REPO_ROOT / "blueprints/fedramp-high/app-engine/main.tf"
    ).read_text(encoding="utf-8")
    self.assertIn('resource "google_project_service" "appengine"', ae_tf)
    self.assertIn('service            = "appengine.googleapis.com"', ae_tf)
    self.assertIn("depends_on  = [google_project_service.appengine]", ae_tf)

    pg_tf = (
        REPO_ROOT / "blueprints/il5/postgresql/main.tf"
    ).read_text(encoding="utf-8")
    self.assertIn('resource "google_project_service" "sqladmin"', pg_tf)
    self.assertIn('service            = "sqladmin.googleapis.com"', pg_tf)
    self.assertIn("google_project_service.sqladmin", pg_tf)

  def test_modules_enforce_30_char_id_preconditions(self):
    """Ensure project and iam-service-account modules enforce 30-character ID preconditions (#228)."""
    proj_tf = (REPO_ROOT / "modules/project/main.tf").read_text(encoding="utf-8")
    self.assertIn('condition     = length("${local.prefix}${var.name}") <= 30', proj_tf)
    self.assertIn("exceeding the 30-character GCP project ID limit", proj_tf)

    sa_tf = (REPO_ROOT / "modules/iam-service-account/main.tf").read_text(
        encoding="utf-8"
    )
    self.assertIn('condition     = length("${local.prefix}${local.name}") <= 30', sa_tf)
    self.assertIn(
        "exceeding the 30-character GCP service account ID limit", sa_tf
    )

  def _iter_terraform_dirs(self):
    """Yield every directory under fast/, modules/, and blueprints/ containing .tf files."""
    seen = set()
    for root_name in ("fast", "blueprints"):
      base = REPO_ROOT / root_name
      for tf_file in base.rglob("*.tf"):
        if ".terraform" in tf_file.parts:
          continue
        parent = tf_file.parent
        if parent not in seen:
          seen.add(parent)
          yield parent

  @staticmethod
  def _strip_comments_and_moved(text: str) -> str:
    import re
    lines = []
    in_block = False
    for line in text.splitlines():
      stripped = line.strip()
      if in_block:
        if "*/" in stripped:
          in_block = False
        continue
      if stripped.startswith("/*"):
        if "*/" not in stripped:
          in_block = True
        continue
      if stripped.startswith("#") or stripped.startswith("//"):
        continue
      line = re.sub(r"\s+#.*$", "", line)
      lines.append(line)
    cleaned = "\n".join(lines)
    # Remove moved { ... } blocks and description = "..." strings
    cleaned = re.sub(r"moved\s*\{[^}]*\}", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'description\s*=\s*"[^"]*"', "", cleaned)
    return cleaned

  def test_all_terraform_dirs_have_valid_variable_and_resource_references(self):
    """Ensure every Terraform directory declares all referenced vars, resources, data sources, and modules."""
    import re
    errors = []
    for tf_dir in sorted(self._iter_terraform_dirs()):
      rel_dir = tf_dir.relative_to(REPO_ROOT)
      raw_combined = "\n".join(
          p.read_text(encoding="utf-8") for p in sorted(tf_dir.glob("*.tf"))
      )
      cleaned = self._strip_comments_and_moved(raw_combined)

      # Catch common HCL prefix typos like vvar. or lcoal.
      for typo in re.findall(r"\b(?:vvar|lcoal| moudle)\.[a-zA-Z0-9_-]+", cleaned):
        errors.append(f"{rel_dir}: suspicious typo reference '{typo}'")

      decl_vars = set(re.findall(r'variable\s+"([^"]+)"', raw_combined))
      ref_vars = set(re.findall(r"\bvar\.([a-zA-Z0-9_-]+)", cleaned))
      missing_vars = sorted(ref_vars - decl_vars)
      if missing_vars:
        errors.append(f"{rel_dir}: undeclared var reference(s): {missing_vars}")

      decl_res = {
          f"{m.group(1)}.{m.group(2)}"
          for m in re.finditer(r'resource\s+"([^"]+)"\s+"([^"]+)"', raw_combined)
      }
      ref_res = set()
      for m in re.finditer(
          r'(?<!\.)(?<!data\.)(?<!")\b(google_[a-zA-Z0-9_]+)\.([a-zA-Z0-9_-]+)\b',
          cleaned,
      ):
        prefix = cleaned[max(0, m.start() - 45) : m.start()]
        if re.search(r"module\.[a-zA-Z0-9_-]+(?:\[[^\]]+\])?\.$", prefix):
          continue
        ref_res.add(f"{m.group(1)}.{m.group(2)}")
      missing_res = sorted(ref_res - decl_res)
      if missing_res:
        errors.append(f"{rel_dir}: undeclared resource reference(s): {missing_res}")

      decl_mods = set(re.findall(r'module\s+"([^"]+)"', raw_combined))
      ref_mods = set(re.findall(r"\bmodule\.([a-zA-Z0-9_-]+)\b", cleaned))
      missing_mods = sorted(ref_mods - decl_mods)
      if missing_mods:
        errors.append(f"{rel_dir}: undeclared module reference(s): {missing_mods}")

      decl_locals = set()
      pos = 0
      while True:
        m = re.search(r"\blocals\s*\{", cleaned[pos:])
        if not m:
          break
        start = pos + m.end()
        depth = 1
        i = start
        while i < len(cleaned) and depth > 0:
          if cleaned[i] == "{":
            depth += 1
          elif cleaned[i] == "}":
            depth -= 1
          i += 1
        block = cleaned[start : i - 1]
        b_depth = 0
        for bline in block.splitlines():
          if b_depth == 0:
            km = re.match(r"^\s*([a-zA-Z0-9_-]+)\s*=", bline)
            if km:
              decl_locals.add(km.group(1))
          b_depth += bline.count("{") + bline.count("[") + bline.count("(")
          b_depth -= bline.count("}") + bline.count("]") + bline.count(")")
        pos = i
      ref_locals = set(re.findall(r"(?<!\.)\blocal\.([a-zA-Z0-9_-]+)", cleaned))
      missing_locals = sorted(ref_locals - decl_locals)
      if missing_locals:
        errors.append(f"{rel_dir}: undeclared local reference(s): {missing_locals}")

    self.assertEqual(
        errors,
        [],
        "Broken HCL references detected:\n" + "\n".join(errors),
    )

  def test_no_invalid_sensitive_type_constructors_in_variables(self):
    """Ensure variable type definitions do not use sensitive(...) as a type constructor."""
    import re
    offenders = []
    for tf_dir in sorted(self._iter_terraform_dirs()):
      for tf_file in sorted(tf_dir.glob("*.tf")):
        content = self._strip_comments_and_moved(tf_file.read_text(encoding="utf-8"))
        if re.search(r"optional\(\s*sensitive\(", content):
          offenders.append(str(tf_file.relative_to(REPO_ROOT)))
    self.assertEqual(
        offenders,
        [],
        f"Invalid optional(sensitive(...)) type constructor in: {offenders}",
    )

  def test_all_blueprint_sample_tfvars_match_declared_variables(self):
    """Ensure every blueprint terraform.tfvars.sample only sets declared variables and covers required ones."""
    import re
    errors = []
    for sample in sorted(REPO_ROOT.glob("blueprints/**/terraform.tfvars.sample")):
      bp_dir = sample.parent
      rel = bp_dir.relative_to(REPO_ROOT)
      raw_vars = "\n".join(
          p.read_text(encoding="utf-8") for p in sorted(bp_dir.glob("*.tf"))
      )
      decl_vars = set()
      req_vars = set()
      pos = 0
      while True:
        m = re.search(r'variable\s+"([^"]+)"\s*\{', raw_vars[pos:])
        if not m:
          break
        vname = m.group(1)
        decl_vars.add(vname)
        start = pos + m.end()
        depth = 1
        i = start
        while i < len(raw_vars) and depth > 0:
          if raw_vars[i] == "{":
            depth += 1
          elif raw_vars[i] == "}":
            depth -= 1
          i += 1
        vbody = raw_vars[start : i - 1]
        if not re.search(r"^\s*default\s*=", vbody, flags=re.M):
          req_vars.add(vname)
        pos = i

      stext = sample.read_text(encoding="utf-8")
      slines = [
          re.sub(r"(#|//).*$", "", l)
          for l in stext.splitlines()
          if not l.strip().startswith(("#", "//"))
      ]
      s_depth = 0
      assigned = set()
      for l in slines:
        if re.search(r"=\s*base64encode\(", l):
          errors.append(f"{rel}: function call not allowed in tfvars: {l.strip()}")
        if s_depth == 0:
          am = re.match(r"^\s*([a-zA-Z0-9_-]+)\s*=", l)
          if am:
            assigned.add(am.group(1))
        s_depth += l.count("{") + l.count("[") + l.count("(")
        s_depth -= l.count("}") + l.count("]") + l.count(")")
      undecl = sorted(assigned - decl_vars)
      missing_req = sorted(req_vars - assigned)
      if undecl:
        errors.append(f"{rel}: undeclared variable(s) in sample tfvars: {undecl}")
      if missing_req:
        errors.append(f"{rel}: missing required variable(s) in sample tfvars: {missing_req}")

    self.assertEqual(
        errors,
        [],
        "Invalid blueprint terraform.tfvars.sample files:\n" + "\n".join(errors),
    )



  def test_custom_stellar_engine_modules_validations(self):
    """Verify hardening and logic fixes across custom Stellar Engine modules."""
    alerts_main = (REPO_ROOT / "modules/cis-log-alerts/main.tf").read_text(encoding="utf-8")
    self.assertIn("concat([google_monitoring_notification_channel.email.name], var.notification_channels)", alerts_main)
    self.assertIn("display_name = each.key", alerts_main)
    self.assertNotIn('display_name = "each.key"', alerts_main)

    alerts_vars = (REPO_ROOT / "modules/cis-log-alerts/variables.tf").read_text(encoding="utf-8")
    self.assertIn('variable "notification_channels"', alerts_vars)

    metrics_main = (REPO_ROOT / "modules/cis-log-metrics/main.tf").read_text(encoding="utf-8")
    self.assertIn("AND ((ProjectOwnership OR projectOwnerInvitee)", metrics_main)

    ids_main = (REPO_ROOT / "modules/intrusion-detection-system/main.tf").read_text(encoding="utf-8")
    self.assertIn("count = var.create_service_networking_connection ? 1 : 0", ids_main)

    org_se_iam = (REPO_ROOT / "modules/organization-se/iam.tf").read_text(encoding="utf-8")
    self.assertIn('"iam-bpa:${principal}//${role}"', org_se_iam)
    org_se_vars = (REPO_ROOT / "modules/organization-se/variables.tf").read_text(encoding="utf-8")
    self.assertIn('can(regex("^organizations/[0-9]+$", var.organization_id))', org_se_vars)

    spanner_se_iam = (REPO_ROOT / "modules/spanner-instance-se/iam.tf").read_text(encoding="utf-8")
    self.assertIn('dynamic "condition"', spanner_se_iam)
    spanner_se_vars = (REPO_ROOT / "modules/spanner-instance-se/variables.tf").read_text(encoding="utf-8")
    self.assertIn("condition = optional(object({", spanner_se_vars)



  def test_synced_upstream_cff_modules_fixes(self):
    """Verify upstream CFF fixes in synced folder, net-lb-int, net-lb-proxy-int, spanner-instance, and cloud-run-v2 modules."""
    self.assertFalse((REPO_ROOT / "modules/cloud-run").exists())
    self.assertTrue((REPO_ROOT / "modules/cloud-run-v2").exists())

    folder_vars = (REPO_ROOT / "modules/folder/variables.tf").read_text(encoding="utf-8")
    self.assertNotIn('"CA_PROTECTED_B, IL5, HIPAA, HITRUST"', folder_vars)
    self.assertIn('"IL5"', folder_vars)

    nlb_hc = (REPO_ROOT / "modules/net-lb-int/health-check.tf").read_text(encoding="utf-8")
    self.assertIn("local.hc.http2.host", nlb_hc)
    self.assertIn("local.hc.ssl.port", nlb_hc)

    proxy_bs = (REPO_ROOT / "modules/net-lb-proxy-int/backend-service.tf").read_text(encoding="utf-8")
    self.assertNotIn(" ar.backend_service_config", proxy_bs)
    self.assertNotIn("local.bs_conntrack", proxy_bs)

    spanner_iam = (REPO_ROOT / "modules/spanner-instance/iam.tf").read_text(encoding="utf-8")
    self.assertIn('dynamic "condition"', spanner_iam)


if __name__ == "__main__":
  unittest.main()
