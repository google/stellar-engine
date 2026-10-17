#!/usr/bin/env python3
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

"""SBOM ingestion and application codebase discovery scanners."""

import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, Final, Optional, Set, Tuple, Type, Union

from . import safe_xml as ET
from ._tf_hcl_helpers import _find_trusted_binary, safe_run_command
from .file_helpers import (
    is_ignored_traversal_dir,
    read_json_file,
    read_text_file,
)

logger = logging.getLogger("extract_system_data")

_EXTERNAL_TOOL_ERRORS: Final[Tuple[Type[BaseException], ...]] = (
    OSError,
    ValueError,
    MemoryError,
    subprocess.SubprocessError,
)


def _esd_attr(name: str, default: Any) -> Any:
    """Resolves a symbol via extract_system_data if loaded so monkeypatches work."""
    mod = sys.modules.get("compliance_engine.extract_system_data") or sys.modules.get("extract_system_data")
    return getattr(mod, name, default) if mod is not None else default


def _extract_cyclonedx_license(comp: Dict[str, Any]) -> str:
    """Extracts a license identifier or name from a CycloneDX component."""
    lic_str = "Open Source License"
    licenses = comp.get("licenses", [])
    if licenses and isinstance(licenses, list):
        first_lic = licenses[0]
        if isinstance(first_lic, dict):
            if "license" in first_lic and isinstance(first_lic["license"], dict):
                lic_str = first_lic["license"].get("id") or first_lic["license"].get("name", lic_str)
            elif "id" in first_lic:
                lic_str = first_lic.get("id") or lic_str
        elif isinstance(first_lic, str):
            lic_str = first_lic
    return lic_str


def _classify_cyclonedx_ecosystem(purl: str, c_type: str, app_data: Dict[str, Any]) -> str:
    """Classifies ecosystem and records runtime from a CycloneDX purl/type."""
    if "pkg:pypi" in purl or c_type == "python":
        app_data["runtimes"].add("Python")
        return "PyPI (Python)"
    if "pkg:npm" in purl or c_type in ("npm", "nodejs"):
        app_data["runtimes"].add("Node.js")
        return "npm (Node.js)"
    if "pkg:golang" in purl or c_type == "go-module":
        app_data["runtimes"].add("Go")
        return "Go Modules"
    if "pkg:maven" in purl or c_type in ("java", "maven"):
        app_data["runtimes"].add("Java")
        return "Maven (Java)"
    if "pkg:deb" in purl:
        return "Debian OS Package"
    if "pkg:apk" in purl:
        return "Alpine OS Package"
    return "Open Source"


def _classify_cyclonedx_category(name: str, c_type: str, app_data: Dict[str, Any]) -> str:
    """Classifies package category and updates frameworks/database_connectors."""
    n_low = name.lower()
    n_tokens = set(re.split(r"[-_./:@]+", n_low))
    if (
        c_type == "framework"
        or any(k in n_low for k in ("fastapi", "flask", "django", "express", "spring-boot"))
        or any(t in n_tokens for t in ("next", "react", "gin", "spring"))
    ):
        for substr, label in (
            ("fastapi", "FastAPI REST Microservice"),
            ("flask", "Flask Application"),
            ("django", "Django Enterprise Application"),
            ("express", "Express.js REST API"),
        ):
            if substr in n_low:
                app_data["frameworks"].add(label)
                break
        else:
            if "next" in n_tokens:
                app_data["frameworks"].add("Next.js Full-Stack Application")
            elif "react" in n_tokens:
                app_data["frameworks"].add("React Modern Single-Page Application (SPA)")
        return "Application Framework"

    if (
        any(k in n_low for k in ("asyncpg", "psycopg", "mysql", "redis", "mongo", "spanner", "bigquery"))
        or "pg" in n_tokens
    ):
        if any(p in n_low for p in ("asyncpg", "psycopg")) or "pg" in n_tokens:
            app_data["database_connectors"].add("PostgreSQL (asyncpg/psycopg2)")
        elif "redis" in n_low:
            app_data["database_connectors"].add("Redis Client Driver")
        elif "bigquery" in n_low:
            app_data["database_connectors"].add("Google Cloud BigQuery Client")
        return "Database Client Driver"

    if "google-cloud-" in n_low:
        return "Cloud Client SDK"
    return "Third-Party Library"


def _ingest_cyclonedx_sbom(sbom_data: Dict[str, Any], app_data: Dict[str, Any]) -> None:
    """Ingests CycloneDX components and metadata into app_data."""
    meta_comp = sbom_data.get("metadata", {}).get("component")
    if meta_comp and isinstance(meta_comp, dict):
        app_name = meta_comp.get("name", "app-service")
        app_data["applications"].append({
            "name": app_name,
            "version": meta_comp.get("version", "1.0.0"),
            "description": meta_comp.get("description", "Application / Service Component"),
            "type": meta_comp.get("type", "application"),
            "framework": "Cloud Native Service",
            "entrypoint": "main",
            "file": "sbom.json",
        })
        app_data["all_resources"].append({
            "type": "Application Service",
            "name": app_name,
            "category": "Application Layer Component",
            "file": "sbom.json",
        })

    for comp in sbom_data.get("components", []):
        name = comp.get("name")
        if not name:
            continue
        ver = comp.get("version", "Latest")
        purl = comp.get("purl", "")
        c_type = comp.get("type", "library")
        eco = _classify_cyclonedx_ecosystem(purl, c_type, app_data)
        cat = _classify_cyclonedx_category(name, c_type, app_data)
        app_data["software_packages"].append({
            "name": name,
            "version": ver,
            "ecosystem": eco,
            "category": cat,
            "license": _extract_cyclonedx_license(comp),
            "purl": purl,
            "description": comp.get("description", ""),
            "file": "sbom.json",
        })
        if c_type == "container":
            app_data["container_images"].append({
                "image": f"{name}:{ver}",
                "base_os": eco,
                "file": "sbom.json",
            })


def _extract_syft_license(art: Dict[str, Any]) -> str:
    """Extracts a license string from a Syft artifact."""
    lic_list = art.get("licenses", [])
    if isinstance(lic_list, list) and lic_list:
        first_lic = lic_list[0]
        if isinstance(first_lic, str):
            return first_lic
        if isinstance(first_lic, dict):
            return (
                first_lic.get("value")
                or first_lic.get("spdxExpression")
                or first_lic.get("id")
                or "Open Source License"
            )
    return "Open Source License"


def _ingest_syft_sbom(sbom_data: Dict[str, Any], app_data: Dict[str, Any]) -> None:
    """Ingests Syft artifact records into app_data."""
    for art in sbom_data.get("artifacts", []):
        name = art.get("name")
        if not name:
            continue
        ver = art.get("version", "Latest")
        purl = art.get("purl", "")
        a_type = art.get("type", "library")
        a_low = a_type.lower()
        eco = f"{a_type.title()} Package" if a_type else "Open Source"
        if "python" in a_low or "pypi" in purl:
            app_data["runtimes"].add("Python")
            eco = "PyPI (Python)"
        elif "npm" in a_low or "javascript" in a_low:
            app_data["runtimes"].add("Node.js")
            eco = "npm (Node.js)"
        elif "go" in a_low:
            app_data["runtimes"].add("Go")
            eco = "Go Modules"
        elif "java" in a_low or "maven" in a_low:
            app_data["runtimes"].add("Java")
            eco = "Maven (Java)"

        cat = "Third-Party Library"
        n_low = name.lower()
        n_tokens = set(re.split(r"[-_./:@]+", n_low))
        if (
            any(k in n_low for k in ("fastapi", "flask", "django", "express"))
            or any(t in n_tokens for t in ("next", "react"))
        ):
            cat = "Application Framework"
            if "fastapi" in n_low:
                app_data["frameworks"].add("FastAPI REST Microservice")
            elif "flask" in n_low:
                app_data["frameworks"].add("Flask Application")
        elif (
            any(k in n_low for k in ("asyncpg", "psycopg", "mysql", "redis", "bigquery"))
            or "pg" in n_tokens
        ):
            cat = "Database Client Driver"
            if "asyncpg" in n_low or "psycopg" in n_low or "pg" in n_tokens:
                app_data["database_connectors"].add("PostgreSQL (asyncpg/psycopg2)")

        app_data["software_packages"].append({
            "name": name,
            "version": ver,
            "ecosystem": eco,
            "category": cat,
            "license": _extract_syft_license(art),
            "purl": purl,
            "file": "sbom.json",
        })


def _ingest_spdx_sbom(sbom_data: Dict[str, Any], app_data: Dict[str, Any]) -> None:
    """Ingests SPDX package records into app_data."""
    for pkg in sbom_data.get("packages", []):
        name = pkg.get("name")
        if not name:
            continue
        app_data["software_packages"].append({
            "name": name,
            "version": pkg.get("versionInfo", "Latest"),
            "ecosystem": "Open Source Package",
            "category": "Third-Party Library",
            "license": pkg.get("licenseConcluded") or "Open Source License",
            "description": pkg.get("summary", ""),
            "file": "sbom.json",
        })


def ingest_sbom_json(sbom_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ingests and translates CycloneDX, SPDX, or Syft SBOM JSON into application components."""
    app_data: Dict[str, Any] = {
        "applications": [],
        "software_packages": [],
        "container_images": [],
        "exposed_ports": [],
        "frameworks": set(),
        "runtimes": set(),
        "database_connectors": set(),
        "all_resources": [],
    }
    if "components" in sbom_data or sbom_data.get("bomFormat") == "CycloneDX":
        _ingest_cyclonedx_sbom(sbom_data, app_data)
    elif "artifacts" in sbom_data:
        _ingest_syft_sbom(sbom_data, app_data)
    elif "packages" in sbom_data:
        _ingest_spdx_sbom(sbom_data, app_data)
    return app_data


def _discover_existing_sbom_file(
    target_path: Path, user_config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Checks explicit sbom_path and standard SBOM filenames under target_path."""
    explicit_sbom = user_config.get("sbom_path")
    if explicit_sbom:
        p = Path(explicit_sbom)
        resolved_p = p if p.is_absolute() else (target_path / p)
        if not resolved_p.is_file():
            resolved_p = target_path / "app" / p
        if resolved_p.is_symlink():
            logger.warning("Skipping symlinked SBOM file: '%s'", resolved_p)
        elif resolved_p.is_file():
            try:
                data = read_json_file(str(resolved_p), allowed_boundary=target_path)
                if isinstance(data, dict):
                    logger.info("Ingesting user-configured SBOM: '%s'", resolved_p)
                    return data
            except (OSError, ValueError, PermissionError) as err:
                logger.warning("Failed loading user-configured SBOM '%s': %s", resolved_p, err)

    candidate_names = ["sbom.json", "bom.json", "cyclonedx.json", "spdx.json", "app_sbom.json"]
    search_dirs = [target_path]
    if (target_path / "app").is_dir() and not (target_path / "app").is_symlink():
        search_dirs.append(target_path / "app")

    for s_dir in search_dirs:
        for fname in candidate_names:
            c_file = s_dir / fname
            if c_file.is_symlink():
                logger.warning("Skipping symlinked SBOM candidate: '%s'", c_file)
                continue
            if not c_file.is_file():
                continue
            try:
                data = read_json_file(str(c_file), allowed_boundary=target_path)
                if isinstance(data, dict) and (
                    "components" in data or "packages" in data or "artifacts" in data
                ):
                    logger.info("Auto-discovered SBOM file at '%s'", c_file)
                    return data
            except (OSError, ValueError, PermissionError) as err:
                logger.debug("Candidate file '%s' is not valid SBOM JSON: %s", c_file, err)
    return None


def _generate_sbom_with_cli(app_dir: Path) -> Optional[Dict[str, Any]]:
    """Generates a CycloneDX SBOM via Syft or Trivy when scanners are explicitly enabled."""
    find_bin = _esd_attr("_find_trusted_binary", _find_trusted_binary)
    run_cmd = _esd_attr("safe_run_command", safe_run_command)

    syft_bin = find_bin("syft")
    if syft_bin:
        syft_env = dict(os.environ, SYFT_CHECK_FOR_APP_UPDATE="false")
        try:
            res = run_cmd([syft_bin, f"dir:{app_dir}", "-o", "cyclonedx-json"], timeout=60, env=syft_env)
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict) and data.get("components"):
                    logger.info("Auto-generated SBOM via 'syft dir:%s'", app_dir)
                    return data
        except _EXTERNAL_TOOL_ERRORS as err:
            logger.warning("Syft SBOM generation failed: %s", err)

    trivy_bin = find_bin("trivy")
    if trivy_bin:
        try:
            res = run_cmd(
                [trivy_bin, "fs", "--format", "cyclonedx", "--offline-scan", "--skip-db-update", "--", str(app_dir)],
                timeout=60,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict) and data.get("components"):
                    logger.info("Auto-generated SBOM via 'trivy fs %s'", app_dir)
                    return data
        except _EXTERNAL_TOOL_ERRORS as err:
            logger.warning("Trivy SBOM generation failed: %s", err)
    return None


def discover_or_generate_sbom(
    target_dir: Union[str, Path],
    user_config: Optional[Dict[str, Any]] = None,
    allow_scanners: bool = False,
) -> Optional[Dict[str, Any]]:
    """Discovers pre-existing SBOM JSON, or generates it via Syft / Trivy when allowed."""
    target_path = Path(target_dir).resolve()
    found = _discover_existing_sbom_file(target_path, user_config or {})
    if found is not None:
        return found
    if not allow_scanners:
        logger.info("Skipping dynamic SBOM generation via Syft/Trivy (not explicitly allowed)")
        return None
    app_dir = target_path / "app" if (target_path / "app").is_dir() else target_path
    return _generate_sbom_with_cli(app_dir)


def merge_app_data(
    base_app_data: Dict[str, Any],
    sbom_app_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Merges SBOM discovered dependencies and packages into static code app data."""
    merged: Dict[str, Any] = {
        "applications": list(base_app_data.get("applications", [])),
        "software_packages": list(base_app_data.get("software_packages", [])),
        "container_images": list(base_app_data.get("container_images", [])),
        "exposed_ports": list(base_app_data.get("exposed_ports", [])),
        "frameworks": set(base_app_data.get("frameworks", set())),
        "runtimes": set(base_app_data.get("runtimes", set())),
        "database_connectors": set(base_app_data.get("database_connectors", set())),
        "all_resources": list(base_app_data.get("all_resources", [])),
    }

    existing_pkg_keys = {
        (p.get("name", "").lower(), p.get("version", ""))
        for p in merged["software_packages"]
    }
    for p in sbom_app_data.get("software_packages", []):
        pkg_key = (p.get("name", "").lower(), p.get("version", ""))
        if pkg_key not in existing_pkg_keys:
            merged["software_packages"].append(p)
            existing_pkg_keys.add(pkg_key)

    merged["runtimes"].update(sbom_app_data.get("runtimes", set()))
    merged["frameworks"].update(sbom_app_data.get("frameworks", set()))
    merged["database_connectors"].update(sbom_app_data.get("database_connectors", set()))

    existing_app_names = {a.get("name") for a in merged["applications"]}
    for app in sbom_app_data.get("applications", []):
        if app.get("name") not in existing_app_names:
            merged["applications"].append(app)
            existing_app_names.add(app.get("name"))

    existing_imgs = {c.get("image") for c in merged["container_images"]}
    for img in sbom_app_data.get("container_images", []):
        if img.get("image") not in existing_imgs:
            merged["container_images"].append(img)
            existing_imgs.add(img.get("image"))

    return merged


def _detect_nodejs_framework(all_deps: Dict[str, Any], app_data: Dict[str, Any]) -> str:
    """Detects primary Node.js framework from package.json dependencies."""
    framework_rules = (
        (("next",), "Next.js Full-Stack Application", "Next.js"),
        (("express",), "Express.js Web Application", "Express.js"),
        (("fastify",), "Fastify High-Performance API", "Fastify"),
        (("@nestjs/core", "nestjs"), "NestJS Enterprise Backend", "NestJS"),
        (("react",), "React Frontend Application", "React"),
        (("vue",), "Vue.js Frontend Application", "Vue.js"),
        (("@angular/core",), "Angular Application", "Angular"),
    )
    for keys, label, short_name in framework_rules:
        if any(k in all_deps for k in keys):
            app_data["frameworks"].add(short_name)
            return label
    return "Node.js Service"


def _scan_nodejs_package_json(
    filepath: str, rel_path: str, boundary_dir: str, app_data: Dict[str, Any]
) -> None:
    """Scans a package.json file for Node.js application metadata and npm dependencies."""
    try:
        pkg_json = read_json_file(filepath, allowed_boundary=boundary_dir)
        pkg_name = pkg_json.get("name") or os.path.basename(os.path.dirname(filepath)) or "node-application"
        pkg_version = pkg_json.get("version", "1.0.0")
        pkg_desc = pkg_json.get("description", "Node.js Application / Service")
        entrypoint = pkg_json.get("main", "index.js")

        app_data["runtimes"].add("Node.js")
        deps = pkg_json.get("dependencies", {})
        dev_deps = pkg_json.get("devDependencies", {})
        detected_framework = _detect_nodejs_framework({**dev_deps, **deps}, app_data)

        app_data["applications"].append({
            "name": pkg_name,
            "type": detected_framework,
            "language": "JavaScript / TypeScript (Node.js)",
            "framework": detected_framework,
            "version": pkg_version,
            "description": pkg_desc,
            "entrypoint": entrypoint,
            "file": rel_path,
        })
        app_data["all_resources"].append({
            "type": "application_service",
            "name": pkg_name,
            "category": "Application Component",
            "file": rel_path,
        })

        for dep_name, dep_ver in deps.items():
            dep_ver_clean = str(dep_ver).lstrip("^~=>=< ")
            cat = "Third-Party Library"
            dep_tokens = set(re.split(r"[-_./:@]+", dep_name.lower()))
            if (
                any(k in dep_name for k in ("express", "fastify", "nestjs"))
                or any(t in dep_tokens for t in ("react", "next", "vue", "angular", "koa"))
            ):
                cat = "Application Framework"
            elif (
                any(k in dep_name for k in ("mysql", "mongo", "redis", "sequelize", "prisma", "typeorm", "spanner", "bigquery"))
                or "pg" in dep_tokens
            ):
                cat = "Database Client Driver"
                app_data["database_connectors"].add(dep_name)
            elif "@google-cloud" in dep_name:
                cat = "Cloud Client SDK"

            app_data["software_packages"].append({
                "name": dep_name,
                "version": dep_ver_clean or "Latest",
                "ecosystem": "npm (Node.js)",
                "category": cat,
                "file": rel_path,
            })
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, PermissionError) as err:
        logger.warning("Failed reading package.json %s: %s", filepath, err)


def _scan_python_manifests(
    filename: str, filepath: str, rel_path: str, boundary_dir: str, app_data: Dict[str, Any]
) -> None:
    """Scans Python requirements.txt and pyproject.toml files."""
    if filename == "requirements.txt":
        try:
            app_data["runtimes"].add("Python")
            req_text = read_text_file(filepath, allowed_boundary=boundary_dir)
            for line in req_text.splitlines():
                line = line.split("#")[0].strip()
                if not line or line.startswith(("-", "git+", "http")):
                    continue
                parts = re.split(r"[=<>!~]", line, maxsplit=1)
                pkg_name = parts[0].strip()
                pkg_ver = parts[1].strip(" =") if len(parts) > 1 else "Latest"

                cat = "Third-Party Library"
                p_low = pkg_name.lower()
                if p_low in ("fastapi", "flask", "django", "tornado", "aiohttp", "starlette"):
                    cat = "Application Framework"
                    app_data["frameworks"].add(pkg_name.title())
                elif p_low in ("psycopg2", "asyncpg", "pymysql", "pymongo", "redis", "sqlalchemy", "tortoise-orm"):
                    cat = "Database Client Driver"
                    app_data["database_connectors"].add(pkg_name)
                elif "google-cloud" in p_low:
                    cat = "Cloud Client SDK"

                app_data["software_packages"].append({
                    "name": pkg_name,
                    "version": pkg_ver,
                    "ecosystem": "PyPI (Python)",
                    "category": cat,
                    "file": rel_path,
                })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.warning("Failed reading requirements.txt %s: %s", filepath, err)

    elif filename == "pyproject.toml":
        try:
            app_data["runtimes"].add("Python")
            content = read_text_file(filepath, allowed_boundary=boundary_dir)
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if name_match:
                p_name = name_match.group(1)
                p_ver = ver_match.group(1) if ver_match else "1.0.0"
                app_data["applications"].append({
                    "name": p_name,
                    "type": "Python Application / Service",
                    "language": "Python",
                    "framework": "Python Service",
                    "version": p_ver,
                    "description": "Python Backend Application",
                    "entrypoint": "main.py",
                    "file": rel_path,
                })
                app_data["all_resources"].append({
                    "type": "application_service",
                    "name": p_name,
                    "category": "Application Component",
                    "file": rel_path,
                })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.warning("Failed reading pyproject.toml %s: %s", filepath, err)


def _scan_go_and_maven_manifests(
    filename: str, filepath: str, rel_path: str, boundary_dir: str, app_data: Dict[str, Any]
) -> None:
    """Scans Go go.mod and Java/Maven pom.xml manifests."""
    if filename == "go.mod":
        try:
            app_data["runtimes"].add("Go")
            content = read_text_file(filepath, allowed_boundary=boundary_dir)
            mod_match = re.search(r"module\s+([^\s]+)", content)
            go_ver_match = re.search(r"go\s+([0-9\.]+)", content)
            mod_name = mod_match.group(1) if mod_match else "go-module"
            go_ver = go_ver_match.group(1) if go_ver_match else "1.21"

            app_data["applications"].append({
                "name": os.path.basename(mod_name),
                "type": "Go Microservice",
                "language": f"Go ({go_ver})",
                "framework": "Go Native / Microservice",
                "version": "1.0.0",
                "description": f"Go Service ({mod_name})",
                "entrypoint": "main.go",
                "file": rel_path,
            })
            app_data["all_resources"].append({
                "type": "application_service",
                "name": os.path.basename(mod_name),
                "category": "Application Component",
                "file": rel_path,
            })

            for req in re.finditer(r"^[ \t]*([a-zA-Z0-9_\-\.\/]+)[ \t]+v([0-9a-zA-Z_\-\.]+)", content, re.MULTILINE):
                if "indirect" not in req.group(0):
                    app_data["software_packages"].append({
                        "name": req.group(1),
                        "version": f"v{req.group(2)}",
                        "ecosystem": "Go Modules",
                        "category": "Third-Party Library",
                        "file": rel_path,
                    })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.warning("Failed reading go.mod %s: %s", filepath, err)

    elif filename == "pom.xml":
        try:
            app_data["runtimes"].add("Java / JVM")
            content = read_text_file(filepath, allowed_boundary=boundary_dir)
            art_id, app_ver = "java-application", "1.0.0"
            try:
                xml_root = ET.fromstring(content)
                for elem in xml_root.iter():
                    if "}" in elem.tag:
                        elem.tag = elem.tag.split("}", 1)[1]
                art_elem = xml_root.find("artifactId")
                ver_elem = xml_root.find("version")
                if art_elem is not None and art_elem.text and art_elem.text.strip():
                    art_id = art_elem.text.strip()
                if ver_elem is not None and ver_elem.text and ver_elem.text.strip():
                    app_ver = ver_elem.text.strip()
            except (ET.ParseError, getattr(ET, "DefusedXmlException", Exception), ValueError) as e:
                logger.warning("XML parsing failed for %s: %s. Falling back to regex.", filepath, e)
                art_match = re.search(r"<artifactId>([^<]+)</artifactId>", content)
                ver_match = re.search(r"<version>([^<]+)</version>", content)
                if art_match:
                    art_id = art_match.group(1).strip()
                if ver_match:
                    app_ver = ver_match.group(1).strip()

            f_name = "Spring Boot Application" if "spring-boot" in content else "Java Application"
            if "spring-boot" in content:
                app_data["frameworks"].add("Spring Boot")

            app_data["applications"].append({
                "name": art_id,
                "type": f_name,
                "language": "Java (JVM)",
                "framework": f_name,
                "version": app_ver,
                "description": "Java Enterprise Application",
                "entrypoint": "Application.java",
                "file": rel_path,
            })
            app_data["all_resources"].append({
                "type": "application_service",
                "name": art_id,
                "category": "Application Component",
                "file": rel_path,
            })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.warning("Failed reading pom.xml %s: %s", filepath, err)


def _scan_dockerfile_manifest(
    filepath: str, rel_path: str, boundary_dir: str, found_ports: Set[str], app_data: Dict[str, Any]
) -> None:
    """Scans a Dockerfile or Containerfile for base images and EXPOSE directives."""
    try:
        content = read_text_file(filepath, allowed_boundary=boundary_dir)
        docker_args = {
            arg_m.group(1): (arg_m.group(2) or "").strip("\"'")
            for arg_m in re.finditer(r"^[ \t]*ARG[ \t]+([a-zA-Z0-9_]+)(?:=([^\s#]+))?", content, re.MULTILINE)
        }
        stage_aliases: Set[str] = set()
        for from_match in re.finditer(
            r"^[ \t]*FROM[ \t]+(?:--platform=\S+[ \t]+)?([^\s#]+)(?:[ \t]+AS[ \t]+([a-zA-Z0-9._-]+))?",
            content,
            re.MULTILINE | re.IGNORECASE,
        ):
            base_img = from_match.group(1).strip()
            stage_alias = from_match.group(2)
            if stage_alias:
                stage_aliases.add(stage_alias.lower())
            if base_img.lower() in stage_aliases or base_img.lower() == "scratch" or base_img.startswith("--"):
                continue
            for ak, av in docker_args.items():
                if av:
                    base_img = base_img.replace(f"${{{ak}}}", av).replace(f"${ak}", av)
            if "${" in base_img or "$" in base_img:
                base_img = re.sub(r"\$\{[^}]+\}", "latest", base_img)
                base_img = re.sub(r"\$[a-zA-Z0-9_]+", "latest", base_img)

            base_ver = base_img.split(":")[-1] if ":" in base_img else "latest"
            if not base_ver or "${" in base_ver or "$" in base_ver:
                base_ver = "latest"

            app_data["container_images"].append({"image": base_img, "base_image": base_img, "file": rel_path})
            app_data["software_packages"].append({
                "name": base_img,
                "version": base_ver,
                "ecosystem": "OCI / Docker Container",
                "category": "Container Base Image",
                "file": rel_path,
            })

        for exp_match in re.finditer(r"^[ \t]*EXPOSE[ \t]+([0-9 \t/tcpudp]+)", content, re.MULTILINE | re.IGNORECASE):
            for p_item in exp_match.group(1).split():
                p_clean = p_item.split("/")[0].strip()
                proto = "UDP" if "udp" in p_item.lower() else "TCP"
                if p_clean.isdigit() and 1 <= int(p_clean) <= 65535 and p_clean not in found_ports:
                    found_ports.add(p_clean)
                    app_data["exposed_ports"].append({
                        "port": p_clean,
                        "protocol": proto,
                        "service_name": f"Container Ingress ({p_clean}/{proto})",
                        "source": f"Dockerfile EXPOSE {p_item}",
                        "file": rel_path,
                    })
    except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
        logger.warning("Failed reading container manifest %s: %s", filepath, err)


def _scan_compose_and_k8s_manifests(
    filename: str, filepath: str, rel_path: str, boundary_dir: str, found_ports: Set[str], app_data: Dict[str, Any]
) -> None:
    """Scans docker-compose and Kubernetes YAML manifests for ports and container images."""
    if filename in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        try:
            content = read_text_file(filepath, allowed_boundary=boundary_dir)
            for port_m in re.finditer(
                r'^[ \t]*-[ \t]*["\']?(?:\d{1,3}(?:\.\d{1,3}){3}:)?(\d{1,5}):(\d{1,5})(?:/(?:tcp|udp))?["\']?[ \t]*(?:#.*)?$',
                content,
                re.MULTILINE,
            ):
                host_p, container_p = port_m.group(1), port_m.group(2)
                if 1 <= int(host_p) <= 65535 and 1 <= int(container_p) <= 65535 and host_p not in found_ports:
                    found_ports.add(host_p)
                    app_data["exposed_ports"].append({
                        "port": host_p,
                        "protocol": "TCP",
                        "service_name": f"Docker Compose Ingress ({host_p}->{container_p})",
                        "source": "docker-compose port mapping",
                        "file": rel_path,
                    })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.warning("Failed reading compose file %s: %s", filepath, err)

    elif filename.endswith((".yaml", ".yml")) and not any(
        k in filename.lower() for k in ("compliance", "variables", "system_", "tdd_")
    ):
        try:
            content = read_text_file(filepath, allowed_boundary=boundary_dir)
            if "kind: Service" in content:
                for port_match in re.finditer(r"port:\s*(\d{1,5})\b", content):
                    p_val = port_match.group(1)
                    if 1 <= int(p_val) <= 65535 and p_val not in found_ports:
                        found_ports.add(p_val)
                        app_data["exposed_ports"].append({
                            "port": p_val,
                            "protocol": "TCP",
                            "service_name": f"Kubernetes Service Endpoint ({p_val}/TCP)",
                            "source": "K8s Service Manifest",
                            "file": rel_path,
                        })
            if "kind: Deployment" in content or "kind: StatefulSet" in content:
                for img_match in re.finditer(r'image:\s*["\']?([a-zA-Z0-9_\-\.\/:]+)["\']?', content):
                    img_val = img_match.group(1).strip()
                    if "${" in img_val or "$" in img_val:
                        img_val = re.sub(r"\$\{[^}]+\}", "latest", img_val)
                        img_val = re.sub(r"\$[a-zA-Z0-9_]+", "latest", img_val)
                    app_data["container_images"].append({"image": img_val, "base_image": img_val, "file": rel_path})
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.debug("Failed parsing potential K8s manifest %s: %s", filepath, err)


def _scan_source_listener_ports(
    filename: str, filepath: str, rel_path: str, boundary_dir: str, found_ports: Set[str], app_data: Dict[str, Any]
) -> None:
    """Scans JavaScript/TypeScript and Python source files for listener port declarations."""
    if filename.endswith((".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")):
        try:
            code_txt = read_text_file(filepath, allowed_boundary=boundary_dir)
            for listener_m in re.finditer(r"\.listen\(\s*(\d{2,5})\b", code_txt):
                p_num = listener_m.group(1)
                if 1 <= int(p_num) <= 65535 and p_num not in found_ports:
                    found_ports.add(p_num)
                    app_data["exposed_ports"].append({
                        "port": p_num,
                        "protocol": "TCP",
                        "service_name": f"Node.js Listener ({p_num}/TCP)",
                        "source": f"Code Listener in {os.path.basename(filepath)}",
                        "file": rel_path,
                    })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.debug("Failed parsing JS listener in %s: %s", filepath, err)

    elif filename.endswith(".py"):
        try:
            code_txt = read_text_file(filepath, allowed_boundary=boundary_dir)
            for py_port in re.finditer(
                (
                    r"(?:(?:\.run|uvicorn\.run|gunicorn|serve|listen|HTTPServer|TCPServer)\s*\([^)]*?\bport\s*=\s*(\d{2,5})\b"
                    r"|\.listen\(\s*(\d{2,5})\b|^[ \t]*PORT[ \t]*=[ \t]*(\d{2,5})\b)"
                ),
                code_txt,
                re.MULTILINE | re.DOTALL,
            ):
                p_num = py_port.group(1) or py_port.group(2) or py_port.group(3)
                if p_num and 1 <= int(p_num) <= 65535 and p_num not in found_ports:
                    found_ports.add(p_num)
                    app_data["exposed_ports"].append({
                        "port": p_num,
                        "protocol": "TCP",
                        "service_name": f"Python Service Listener ({p_num}/TCP)",
                        "source": f"Code Listener in {os.path.basename(filepath)}",
                        "file": rel_path,
                    })
        except (OSError, UnicodeDecodeError, ValueError, PermissionError) as err:
            logger.debug("Failed parsing Python listener in %s: %s", filepath, err)


def deep_scan_app_files(target_dir: str) -> Dict[str, Any]:
    """Scans for application-tier codebases, runtimes, containers, dependencies, and ports."""
    app_data: Dict[str, Any] = {
        "applications": [],
        "software_packages": [],
        "container_images": [],
        "exposed_ports": [],
        "frameworks": set(),
        "runtimes": set(),
        "database_connectors": set(),
        "all_resources": [],
    }
    scan_targets = [target_dir]
    target_path = Path(target_dir).resolve()
    boundary_dir = str(target_path)
    if target_path.name == "terraform":
        sibling_app = target_path.parent / "app"
        if sibling_app.is_dir() and not sibling_app.is_symlink():
            scan_targets.append(str(sibling_app))
            boundary_dir = str(target_path.parent)

    scanned_files: Set[str] = set()
    found_ports: Set[str] = set()

    for scan_root in scan_targets:
        for root, dirs, files in os.walk(scan_root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not is_ignored_traversal_dir(d) and not d.startswith("."))
            for filename in sorted(files):
                raw_filepath = os.path.join(root, filename)
                if os.path.islink(raw_filepath):
                    continue
                filepath = os.path.abspath(raw_filepath)
                if filepath in scanned_files:
                    continue
                scanned_files.add(filepath)
                rel_path = os.path.relpath(filepath, target_dir)

                if filename == "package.json":
                    _scan_nodejs_package_json(filepath, rel_path, boundary_dir, app_data)
                elif filename in ("requirements.txt", "pyproject.toml"):
                    _scan_python_manifests(filename, filepath, rel_path, boundary_dir, app_data)
                elif filename in ("go.mod", "pom.xml"):
                    _scan_go_and_maven_manifests(filename, filepath, rel_path, boundary_dir, app_data)
                elif filename in ("Dockerfile", "Containerfile") or filename.endswith(".dockerfile"):
                    _scan_dockerfile_manifest(filepath, rel_path, boundary_dir, found_ports, app_data)
                else:
                    _scan_compose_and_k8s_manifests(filename, filepath, rel_path, boundary_dir, found_ports, app_data)

                _scan_source_listener_ports(filename, filepath, rel_path, boundary_dir, found_ports, app_data)

    logger.info(
        "Discovered %d applications, %d software packages, %d container images, and %d exposed ports.",
        len(app_data["applications"]),
        len(app_data["software_packages"]),
        len(app_data["container_images"]),
        len(app_data["exposed_ports"]),
    )
    return app_data
