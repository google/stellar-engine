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

"""
Pure-Python High-Fidelity Markdown to DOCX Document Generator for RMF / NIST Policy Manuals & SSP

This module converts Markdown policy documents and System Security Plans into executive-ready
Microsoft Word (.docx) documents using pure standard library zipfile and OpenXML XML generation.
Zero external pip dependencies required (runs in restricted / air-gapped environments).

Features:
- Defense / Public Sector typography (Calibri/Arial, Deep Navy #1F4E79 headings, subtle borders).
- Intelligent column width calculation & auto-distribution for 1, 2, 3, 4, and 5-column SCTM matrices.
- High-fidelity tables with Navy header shading, repeating headers (<w:tblHeader/>), and <w:cantSplit/>.
- Header & Footer with Document Title and automated Word Page Numbers (PAGE of NUMPAGES).
- High-visibility RMF Action Required callout cards (yellow fill, red caution left border).
- Inline formatting parser supporting bold (**text**), italic (*text*), code (`text`), and links.
- High-performance streaming builder capable of compiling 10,000+ line SSP documents in seconds.
- Defensive cell padding and escaped pipe handling preventing column shifts or split issues.
- Valid OpenXML archive packaging readable by MS Word, LibreOffice, and Google Docs.
"""

import logging
import math
import os
import re
import sys
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple
import urllib.parse
try:
    from . import safe_xml as ET
except (ImportError, ValueError):
    import safe_xml as ET

try:
    from .file_helpers import (
        ensure_directory,
        ensure_path_within_boundary,
        escape_xml_text,
        resolve_path,
        sanitize_filename,
        split_markdown_table_row,
        scrub_sensitive_data,
    )
except (ImportError, ValueError):
    from file_helpers import (
        ensure_directory,
        ensure_path_within_boundary,
        escape_xml_text,
        resolve_path,
        sanitize_filename,
        split_markdown_table_row,
        scrub_sensitive_data,
    )

try:
    from .audit_log import AuditEvent, AuditOutcome, audit_operation, get_audit_logger
except (ImportError, ValueError):
    from audit_log import AuditEvent, AuditOutcome, audit_operation, get_audit_logger

logger = logging.getLogger(__name__)

# OpenXML Namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_PROPS_APP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
CP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("cp", CP_NS)
ET.register_namespace("dc", DC_NS)
ET.register_namespace("dcterms", DCTERMS_NS)


def w_tag(tag_name: str) -> str:
    """Returns qualified OpenXML WordprocessingML tag name."""
    return f"{{{W_NS}}}{tag_name}"


def r_tag(tag_name: str) -> str:
    """Returns qualified OpenXML Relationships tag name."""
    return f"{{{R_NS}}}{tag_name}"


XML_ILLEGAL_CHARS_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]')


def clean_xml_text(val: Optional[Any]) -> str:
    """Strips characters that are invalid in XML 1.0 documents.

    Args:
        val: Input value or string.

    Returns:
        String with illegal XML 1.0 control characters removed.
    """
    if val is None:
        return ""
    return XML_ILLEGAL_CHARS_PATTERN.sub("", str(val))

# ------------------------------------------------------------------------------
# OpenXML Package Definitions
# ------------------------------------------------------------------------------

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

ROOT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

WORD_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="21"/>
        <w:color w:val="2D3748"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:after="100" w:line="276" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>

  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:pPr>
      <w:spacing w:before="240" w:after="80"/>
      <w:jc w:val="left"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="44"/>
      <w:color w:val="1F4E79"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/>
    <w:pPr>
      <w:spacing w:before="0" w:after="160"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:i/>
      <w:sz w:val="22"/>
      <w:color w:val="4A5568"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/>
    <w:pPr>
      <w:spacing w:before="360" w:after="120"/>
      <w:pBdr>
        <w:bottom w:val="single" w:sz="8" w:space="4" w:color="1F4E79"/>
      </w:pBdr>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="30"/>
      <w:color w:val="1F4E79"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2"/>
    <w:pPr>
      <w:spacing w:before="240" w:after="80"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="25"/>
      <w:color w:val="1F4E79"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="Heading 3"/>
    <w:pPr>
      <w:spacing w:before="160" w:after="60"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="23"/>
      <w:color w:val="2D3748"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Heading4">
    <w:name w:val="Heading 4"/>
    <w:pPr>
      <w:spacing w:before="120" w:after="40"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="21"/>
      <w:color w:val="4A5568"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="CCI">
    <w:name w:val="CCI"/>
    <w:pPr>
      <w:spacing w:before="0" w:after="80"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:i/>
      <w:sz w:val="19"/>
      <w:color w:val="1F4E79"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/>
    <w:pPr>
      <w:spacing w:after="60"/>
    </w:pPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Header1">
    <w:name w:val="Header"/>
    <w:pPr>
      <w:spacing w:after="0"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="16"/>
      <w:color w:val="718096"/>
    </w:rPr>
  </w:style>

  <w:style w:type="paragraph" w:styleId="Footer1">
    <w:name w:val="Footer"/>
    <w:pPr>
      <w:spacing w:after="0"/>
    </w:pPr>
    <w:rPr>
      <w:sz w:val="16"/>
      <w:color w:val="718096"/>
    </w:rPr>
  </w:style>

  <w:style w:type="character" w:styleId="Hyperlink">
    <w:name w:val="Hyperlink"/>
    <w:basedOn w:val="DefaultParagraphFont"/>
    <w:uiPriority w:val="99"/>
    <w:unhideWhenUsed/>
    <w:rPr>
      <w:color w:val="0563C1" w:themeColor="hyperlink"/>
      <w:u w:val="single"/>
    </w:rPr>
  </w:style>
</w:styles>"""

def build_app_xml(org_name: str = "Enterprise Organization") -> str:
    """Builds the docProps/app.xml OpenXML metadata manifest using ElementTree DOM.

    Args:
        org_name: Organization or company name to embed in properties.

    Returns:
        Formatted XML string conforming to OpenXML extended properties schema.
    """
    props = ET.Element(f"{{{DOC_PROPS_APP_NS}}}Properties")
    app = ET.SubElement(props, f"{{{DOC_PROPS_APP_NS}}}Application")
    app.text = "Automated Compliance & Authorization Engine"
    company = ET.SubElement(props, f"{{{DOC_PROPS_APP_NS}}}Company")
    company.text = clean_xml_text(org_name if org_name else "Enterprise Organization")
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(props, encoding="unicode")


def build_core_xml(title: str, org: str) -> str:
    """Builds the docProps/core.xml OpenXML metadata manifest using ElementTree DOM.

    Args:
        title: Document title.
        org: Originating organization or department name.

    Returns:
        Formatted XML string conforming to OpenXML core properties schema.
    """
    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"
    core = ET.Element(f"{{{CP_NS}}}coreProperties")
    
    dc_title = ET.SubElement(core, f"{{{DC_NS}}}title")
    dc_title.text = clean_xml_text(title or "")
    
    dc_creator = ET.SubElement(core, f"{{{DC_NS}}}creator")
    dc_creator.text = clean_xml_text(org or "")
    
    last_mod = ET.SubElement(core, f"{{{CP_NS}}}lastModifiedBy")
    last_mod.text = "Gemini Compliance Engine"
    
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    created = ET.SubElement(core, f"{{{DCTERMS_NS}}}created", {f"{{{xsi_ns}}}type": "dcterms:W3CDTF"})
    created.text = now_str
    
    modified = ET.SubElement(core, f"{{{DCTERMS_NS}}}modified", {f"{{{xsi_ns}}}type": "dcterms:W3CDTF"})
    modified.text = now_str
    
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(core, encoding="unicode")


def build_header_xml(doc_title: str, org_name: str) -> str:
    """Builds the word/header1.xml OpenXML header component using ElementTree DOM.

    Args:
        doc_title: Title string to display in header.
        org_name: Originating organization string.

    Returns:
        Formatted OpenXML header XML string.
    """
    hdr = ET.Element(w_tag("hdr"))
    p = ET.SubElement(hdr, w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))
    ET.SubElement(p_pr, w_tag("pStyle"), {w_tag("val"): "Header1"})
    ET.SubElement(p_pr, w_tag("jc"), {w_tag("val"): "right"})
    
    r = ET.SubElement(p, w_tag("r"))
    r_pr = ET.SubElement(r, w_tag("rPr"))
    ET.SubElement(r_pr, w_tag("sz"), {w_tag("val"): "15"})
    ET.SubElement(r_pr, w_tag("color"), {w_tag("val"): "A0AEC0"})
    
    t = ET.SubElement(r, w_tag("t"))
    t.text = clean_xml_text(doc_title or "")
    
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(hdr, encoding="unicode")


def build_footer_xml(doc_title: str, org_name: str) -> str:
    """Builds the word/footer1.xml OpenXML footer with automated page numbering using ElementTree DOM.

    Args:
        doc_title: Title string to display in footer.
        org_name: Originating organization string.

    Returns:
        Formatted OpenXML footer XML string with PAGE and NUMPAGES fields.
    """
    ftr = ET.Element(w_tag("ftr"))
    p = ET.SubElement(ftr, w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))
    ET.SubElement(p_pr, w_tag("pStyle"), {w_tag("val"): "Footer1"})
    tabs = ET.SubElement(p_pr, w_tag("tabs"))
    ET.SubElement(tabs, w_tag("tab"), {w_tag("val"): "right", w_tag("pos"): "9360"})
    
    r1 = ET.SubElement(p, w_tag("r"))
    r1_pr = ET.SubElement(r1, w_tag("rPr"))
    ET.SubElement(r1_pr, w_tag("sz"), {w_tag("val"): "16"})
    ET.SubElement(r1_pr, w_tag("color"), {w_tag("val"): "718096"})
    t1 = ET.SubElement(r1, w_tag("t"))
    t1.text = clean_xml_text(doc_title or "")
    
    r_tab = ET.SubElement(p, w_tag("r"))
    ET.SubElement(r_tab, w_tag("tab"))
    
    r2 = ET.SubElement(p, w_tag("r"))
    r2_pr = ET.SubElement(r2, w_tag("rPr"))
    ET.SubElement(r2_pr, w_tag("sz"), {w_tag("val"): "16"})
    ET.SubElement(r2_pr, w_tag("color"), {w_tag("val"): "718096"})
    t2 = ET.SubElement(r2, w_tag("t"))
    t2.text = "Page "
    
    ET.SubElement(p, w_tag("fldSimple"), {w_tag("instr"): "PAGE"})
    
    r3 = ET.SubElement(p, w_tag("r"))
    r3_pr = ET.SubElement(r3, w_tag("rPr"))
    ET.SubElement(r3_pr, w_tag("sz"), {w_tag("val"): "16"})
    ET.SubElement(r3_pr, w_tag("color"), {w_tag("val"): "718096"})
    t3 = ET.SubElement(r3, w_tag("t"))
    t3.text = " of "
    
    ET.SubElement(p, w_tag("fldSimple"), {w_tag("instr"): "NUMPAGES"})
    
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(ftr, encoding="unicode")


# ------------------------------------------------------------------------------
# OpenXML Markdown Parser & Node Builder
# ------------------------------------------------------------------------------

def escape_xml(text: Optional[Any]) -> str:
    """Escape XML special characters for safe insertion into XML nodes.

    Args:
        text: Input string or object to convert and escape.

    Returns:
        Escaped string safe for OpenXML text elements.
    """
    return escape_xml_text(text)



class DocxRelationshipManager:
    """Manages OpenXML relationships for a Word document, including external hyperlinks.

    Maintains document-level relationships for styles, headers, footers, and dynamically
    registers external hyperlinks with unique relationship IDs conforming to ECMA-376.
    """

    HYPERLINK_REL_TYPE = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
    )

    def __init__(self) -> None:
        self._counter: int = 0
        self._url_to_rid: Dict[str, str] = {}
        self._relationships: List[Dict[str, str]] = [
            {
                "id": "rId1",
                "type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
                "target": "styles.xml",
                "target_mode": "",
            },
            {
                "id": "rIdHeader",
                "type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header",
                "target": "header1.xml",
                "target_mode": "",
            },
            {
                "id": "rIdFooter",
                "type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer",
                "target": "footer1.xml",
                "target_mode": "",
            },
        ]

    def add_hyperlink(self, url: str) -> str:
        """Registers a hyperlink target URL and returns its unique relationship ID (rId).

        Enforces strict scheme whitelisting to prevent NTLM credential harvesting via SMB UNC paths
        and arbitrary protocol execution handlers (CWE-20 / CWE-611).

        Args:
            url: Target URL string (web URL or relative document path).

        Returns:
            The relationship identifier string (e.g., 'rIdLink1'), or empty string if URL is unsafe.
        """
        if not url:
            return ""
        
        # Remove all whitespace and control characters to prevent parser bypass
        clean_url = re.sub(r'[\x00-\x20\x7f]', '', url)
        if not clean_url:
            return ""

        parsed = urllib.parse.urlparse(clean_url)
        scheme = parsed.scheme.lower()

        # Reject dangerous schemes and UNC paths
        if clean_url.startswith(("\\\\", "//")):
            logger.warning("Unsafe UNC path rejected: '%s'", clean_url)
            get_audit_logger().emit(AuditEvent.SECURITY_VIOLATION, outcome=AuditOutcome.DENIED, detail={"reason": "unsafe_hyperlink", "url": clean_url})
            return ""

        if scheme and scheme not in ("http", "https", "mailto"):
            logger.warning("Disallowed hyperlink scheme rejected: '%s'", clean_url)
            get_audit_logger().emit(AuditEvent.SECURITY_VIOLATION, outcome=AuditOutcome.DENIED, detail={"reason": "disallowed_scheme", "url": clean_url})
            return ""

        # Relative paths must be internal anchors (#...) or safe document extensions
        if not scheme:
            if not clean_url.startswith("#") and not clean_url.lower().endswith((".docx", ".pdf", ".html")):
                logger.warning("Unsafe relative hyperlink path rejected: '%s'", clean_url)
                get_audit_logger().emit(AuditEvent.SECURITY_VIOLATION, outcome=AuditOutcome.DENIED, detail={"reason": "unsafe_relative_path", "url": clean_url})
                return ""

        if clean_url in self._url_to_rid:
            return self._url_to_rid[clean_url]

        self._counter += 1
        rid = f"rIdLink{self._counter}"
        self._url_to_rid[clean_url] = rid
        self._relationships.append({
            "id": rid,
            "type": self.HYPERLINK_REL_TYPE,
            "target": clean_url,
            "target_mode": "External",
        })
        return rid

    def build_rels_xml(self) -> str:
        """Builds word/_rels/document.xml.rels OpenXML manifest using ElementTree DOM.

        Returns:
            Formatted XML string conforming to OpenXML package relationships schema.
        """
        root = ET.Element(f"{{{PKG_RELS_NS}}}Relationships")
        for rel in self._relationships:
            attrib = {
                "Id": rel["id"],
                "Type": rel["type"],
                "Target": rel["target"],
            }
            if rel.get("target_mode"):
                attrib["TargetMode"] = rel["target_mode"]
            ET.SubElement(root, f"{{{PKG_RELS_NS}}}Relationship", attrib)
        return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(root, encoding="unicode")


def trim_trailing_punctuation(raw_url: str) -> Tuple[str, str]:
    """Separates trailing punctuation from a bare URL.

    Handles ending punctuation such as '.', ',', ';', ':', '!', '?', ''', '"',
    and unbalanced trailing parentheses while preserving balanced parentheses.

    Args:
        raw_url: URL string potentially followed by trailing punctuation.

    Returns:
        Tuple of (clean_url, trailing_punctuation).
    """
    url = raw_url
    while True:
        prev_len = len(url)
        # Trim standard trailing punctuation
        while url and url[-1] in ".,;:!?'\"":
            url = url[:-1]

        # Trim unbalanced trailing parentheses
        while url and url.endswith(")"):
            # Count only once per right paren we consider removing
            open_count = url.count("(")
            close_count = url.count(")")
            if open_count < close_count:
                url = url[:-1]
            else:
                break
                
        if len(url) == prev_len:
            break

    trailing = raw_url[len(url):]
    return url, trailing


def build_text_run_element(
    text: str,
    bold: bool = False,
    italic: bool = False,
    color: Optional[str] = None,
    font_name: Optional[str] = None,
    size: Optional[int] = None,
) -> ET.Element:
    """Builds a formatted OpenXML text run element using ElementTree DOM.

    Args:
        text: Text content.
        bold: Whether run text is bold.
        italic: Whether run text is italic.
        color: Optional hex color code.
        font_name: Optional font face name (e.g. 'Consolas').
        size: Optional font size in half-points (e.g. 19 for 9.5pt).

    Returns:
        <w:r> ElementTree node.
    """
    r = ET.Element(w_tag("r"))
    if bold or italic or color or font_name or size:
        r_pr = ET.SubElement(r, w_tag("rPr"))
        if font_name:
            ET.SubElement(r_pr, w_tag("rFonts"), {w_tag("ascii"): font_name, w_tag("hAnsi"): font_name})
        if bold:
            ET.SubElement(r_pr, w_tag("b"))
        if italic:
            ET.SubElement(r_pr, w_tag("i"))
        if size:
            ET.SubElement(r_pr, w_tag("sz"), {w_tag("val"): str(size)})
        if color:
            ET.SubElement(r_pr, w_tag("color"), {w_tag("val"): color})
    t = ET.SubElement(r, w_tag("t"), {f"{{{XML_NS}}}space": "preserve"})
    t.text = clean_xml_text(text)
    return r


def build_text_run(
    text: str,
    bold: bool = False,
    italic: bool = False,
    color: Optional[str] = None,
) -> str:
    """Builds a formatted OpenXML text run element returning XML string.

    Args:
        text: Text content.
        bold: Whether run text is bold.
        italic: Whether run text is italic.
        color: Optional hex color code.

    Returns:
        Formatted <w:r> OpenXML string.
    """
    elem = build_text_run_element(text, bold=bold, italic=italic, color=color)
    return ET.tostring(elem, encoding="unicode")


def build_hyperlink_run_element(
    url: str,
    text: str,
    rels_mgr: Optional[DocxRelationshipManager] = None,
    bold: bool = False,
    italic: bool = False,
) -> ET.Element:
    """Builds a styled OpenXML hyperlink element or styled run fallback using ElementTree DOM.

    Args:
        url: Destination URL or relative target.
        text: Visible anchor text.
        rels_mgr: Optional relationship manager registering the link.
        bold: Whether run text is bold.
        italic: Whether run text is italic.

    Returns:
        <w:hyperlink> or <w:r> ElementTree node.
    """
    clean_url = (url or "").strip()
    display_text = clean_xml_text(text if text else clean_url)

    if rels_mgr is not None and clean_url:
        r_id = rels_mgr.add_hyperlink(clean_url)
        if r_id:
            hl = ET.Element(w_tag("hyperlink"), {r_tag("id"): r_id, w_tag("history"): "1"})
            r = ET.SubElement(hl, w_tag("r"))
            r_pr = ET.SubElement(r, w_tag("rPr"))
            ET.SubElement(r_pr, w_tag("rStyle"), {w_tag("val"): "Hyperlink"})
            if bold:
                ET.SubElement(r_pr, w_tag("b"))
            if italic:
                ET.SubElement(r_pr, w_tag("i"))
            ET.SubElement(r_pr, w_tag("color"), {w_tag("val"): "0563C1"})
            ET.SubElement(r_pr, w_tag("u"), {w_tag("val"): "single"})
            t = ET.SubElement(r, w_tag("t"), {f"{{{XML_NS}}}space": "preserve"})
            t.text = display_text
            return hl

    # Fallback if no relationship manager or link registration failed
    r = ET.Element(w_tag("r"))
    r_pr = ET.SubElement(r, w_tag("rPr"))
    if bold:
        ET.SubElement(r_pr, w_tag("b"))
    if italic:
        ET.SubElement(r_pr, w_tag("i"))
    ET.SubElement(r_pr, w_tag("color"), {w_tag("val"): "0563C1"})
    ET.SubElement(r_pr, w_tag("u"), {w_tag("val"): "single"})
    t = ET.SubElement(r, w_tag("t"), {f"{{{XML_NS}}}space": "preserve"})
    t.text = display_text
    return r


def build_hyperlink_run(
    url: str,
    text: str,
    rels_mgr: Optional[DocxRelationshipManager] = None,
    bold: bool = False,
    italic: bool = False,
) -> str:
    """Builds a styled OpenXML hyperlink element returning XML string.

    Args:
        url: Destination URL or relative target.
        text: Visible anchor text.
        rels_mgr: Optional relationship manager registering the link.
        bold: Whether run text is bold.
        italic: Whether run text is italic.

    Returns:
        Formatted OpenXML XML snippet (<w:hyperlink> or <w:r> fallback).
    """
    elem = build_hyperlink_run_element(url, text, rels_mgr=rels_mgr, bold=bold, italic=italic)
    return ET.tostring(elem, encoding="unicode")


def append_plain_text_with_urls_to_element(
    parent: ET.Element,
    text: str,
    rels_mgr: Optional[DocxRelationshipManager] = None,
    bold: bool = False,
    italic: bool = False,
) -> None:
    """Splits plain text into formatted text runs and hyperlink elements for bare URLs, appending to parent."""
    if not text:
        return

    if len(text) > 10000:
        logger.warning("Truncating massive text block to 10000 characters to prevent ReDoS.")
        text = text[:10000]

    url_pattern = re.compile(r'https?://[^\s<>"\'`]+')
    last_end = 0

    for match in url_pattern.finditer(text):
        start, end = match.span()
        if start > last_end:
            before_text = text[last_end:start]
            parent.append(build_text_run_element(before_text, bold=bold, italic=italic))

        raw_url = match.group(0)
        clean_url, trailing_punct = trim_trailing_punctuation(raw_url)

        if clean_url:
            parent.append(
                build_hyperlink_run_element(
                    clean_url, clean_url, rels_mgr=rels_mgr, bold=bold, italic=italic
                )
            )

        if trailing_punct:
            parent.append(build_text_run_element(trailing_punct, bold=bold, italic=italic))

        last_end = end

    if last_end < len(text):
        remaining = text[last_end:]
        parent.append(build_text_run_element(remaining, bold=bold, italic=italic))


def parse_plain_text_with_urls(
    text: str,
    rels_mgr: Optional[DocxRelationshipManager] = None,
    bold: bool = False,
    italic: bool = False,
) -> List[str]:
    """Splits plain text into formatted text runs and hyperlink elements for bare URLs.

    Args:
        text: Text string containing plain text and possible bare URLs.
        rels_mgr: Optional relationship manager to register hyperlinks.
        bold: Whether text runs should be bold.
        italic: Whether text runs should be italic.

    Returns:
        List of OpenXML run and hyperlink strings.
    """
    temp_p = ET.Element(w_tag("p"))
    append_plain_text_with_urls_to_element(temp_p, text, rels_mgr=rels_mgr, bold=bold, italic=italic)
    return [ET.tostring(child, encoding="unicode") for child in temp_p]


def append_inline_formatting_to_paragraph(
    p: ET.Element,
    text: Optional[str],
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> None:
    """Parses inline Markdown formatting into structured OpenXML text runs and appends to paragraph."""
    if not text:
        r = ET.SubElement(p, w_tag("r"))
        t = ET.SubElement(r, w_tag("t"), {f"{{{XML_NS}}}space": "preserve"})
        t.text = ""
        return

    # Bound input size to prevent ReDoS on massive paragraphs
    text_str = str(text)
    if len(text_str) > 10000:
        logger.warning("Truncating massive paragraph to 10000 characters to prevent ReDoS.")
        text_str = text_str[:10000]

    # Clean any html mark tags
    text_str = re.sub(r'</?mark\b[^>]*>', '', text_str)

    pattern = re.compile(
        r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|(?<!\*)\*[^*]+?\*(?!\*)|`[^`]+`|\[[^\]]+\]\([^)]+\))'
    )
    parts = pattern.split(text_str)

    initial_child_count = len(p)
    for part in parts:
        if not part:
            continue
        if part.startswith('***') and part.endswith('***') and len(part) >= 6:
            clean = part[3:-3]
            append_plain_text_with_urls_to_element(p, clean, rels_mgr=rels_mgr, bold=True, italic=True)
        elif part.startswith('**') and part.endswith('**') and len(part) >= 4:
            clean = part[2:-2]
            append_plain_text_with_urls_to_element(p, clean, rels_mgr=rels_mgr, bold=True, italic=False)
        elif part.startswith('*') and part.endswith('*') and len(part) >= 2:
            clean = part[1:-1]
            append_plain_text_with_urls_to_element(p, clean, rels_mgr=rels_mgr, bold=False, italic=True)
        elif part.startswith('`') and part.endswith('`') and len(part) >= 2:
            clean = part[1:-1]
            p.append(build_text_run_element(clean, font_name="Consolas", size=19, color="1F4E79", bold=True))
        elif part.startswith('[') and '](' in part and part.endswith(')'):
            link_text = part[1 : part.index('](')]
            raw_url = part[part.index('](') + 2 : -1].strip()
            if raw_url.startswith('<') and raw_url.endswith('>'):
                raw_url = raw_url[1:-1].strip()
            if ' ' in raw_url:
                raw_url = raw_url.split(None, 1)[0]
            p.append(build_hyperlink_run_element(raw_url, link_text, rels_mgr=rels_mgr))
        else:
            append_plain_text_with_urls_to_element(p, part, rels_mgr=rels_mgr)

    if len(p) == initial_child_count:
        p.append(build_text_run_element(text))


def parse_inline_formatting(
    text: Optional[str],
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> str:
    """Parses inline Markdown formatting into structured OpenXML text runs using DOM.

    Handles bold (***text***, **text**), italic (*text*), code (`text`),
    markdown links ([text](url)), and bare URLs (https://...).

    Args:
        text: Raw Markdown text containing inline formatting tokens.
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.

    Returns:
        Concatenated <w:r> and <w:hyperlink> OpenXML run elements.
    """
    temp_p = ET.Element(w_tag("p"))
    append_inline_formatting_to_paragraph(temp_p, text, rels_mgr=rels_mgr)
    raw = "".join(ET.tostring(child, encoding="unicode") for child in temp_p)
    return re.sub(r'<w:([a-zA-Z0-9]+)\s*/>', r'<w:\1/>', raw)


def build_paragraph_element(
    text: str,
    style: str = "Normal",
    align: Optional[str] = None,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> ET.Element:
    """Builds a styled OpenXML paragraph element using ElementTree DOM.
    
    Args:
        text: Paragraph text.
        style: OpenXML style identifier.
        align: Optional text justification.
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.
        
    Returns:
        <w:p> ElementTree node.
    """
    p = ET.Element(w_tag("p"))
    if (style and style != "Normal") or align:
        p_pr = ET.SubElement(p, w_tag("pPr"))
        if style and style != "Normal":
            ET.SubElement(p_pr, w_tag("pStyle"), {w_tag("val"): style})
        if align:
            ET.SubElement(p_pr, w_tag("jc"), {w_tag("val"): align})
    append_inline_formatting_to_paragraph(p, text, rels_mgr=rels_mgr)
    return p


def build_paragraph(
    text: str,
    style: str = "Normal",
    align: Optional[str] = None,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> str:
    """Builds a styled OpenXML paragraph element string using ElementTree DOM.

    Args:
        text: Paragraph text or formatted Markdown line.
        style: OpenXML style identifier (e.g., 'Normal', 'Title', 'Heading1').
        align: Optional text justification ('left', 'center', 'right').
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.

    Returns:
        Formatted <w:p> XML element string.
    """
    p = build_paragraph_element(text, style=style, align=align, rels_mgr=rels_mgr)
    return ET.tostring(p, encoding="unicode")


def build_bullet_item_element(
    text: str,
    level: int = 0,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> ET.Element:
    """Builds a bullet list item paragraph with proper hanging indent and symbol bullet.
    
    Args:
        text: The text for the bullet item.
        level: List indentation level (0-indexed).
        rels_mgr: Optional relationship manager for hyperlinks.
        
    Returns:
        <w:p> ElementTree node representing a bullet item.
    """
    indent = 360 * (level + 1)
    p = ET.Element(w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))
    ET.SubElement(p_pr, w_tag("pStyle"), {w_tag("val"): "ListParagraph"})
    ET.SubElement(p_pr, w_tag("ind"), {w_tag("left"): str(indent), w_tag("hanging"): "240"})

    r_bullet = ET.SubElement(p, w_tag("r"))
    r_bullet_pr = ET.SubElement(r_bullet, w_tag("rPr"))
    ET.SubElement(r_bullet_pr, w_tag("rFonts"), {w_tag("ascii"): "Symbol", w_tag("hAnsi"): "Symbol"})
    ET.SubElement(r_bullet_pr, w_tag("sz"), {w_tag("val"): "18"})
    ET.SubElement(r_bullet_pr, w_tag("color"), {w_tag("val"): "1F4E79"})
    t_bullet = ET.SubElement(r_bullet, w_tag("t"))
    t_bullet.text = "· "

    append_inline_formatting_to_paragraph(p, text, rels_mgr=rels_mgr)
    return p


def build_bullet_item(
    text: str,
    level: int = 0,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> str:
    """Builds a bullet list item paragraph string using ElementTree DOM."""
    p = build_bullet_item_element(text, level=level, rels_mgr=rels_mgr)
    return ET.tostring(p, encoding="unicode")


def build_number_item_element(
    text: str,
    prefix: str = "1.",
    level: int = 0,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> ET.Element:
    """Builds a numbered list item paragraph with clean indentation using ElementTree DOM.
    
    Args:
        text: The text for the numbered item.
        prefix: The numbering prefix (e.g., '1.').
        level: List indentation level (0-indexed).
        rels_mgr: Optional relationship manager for hyperlinks.
        
    Returns:
        <w:p> ElementTree node representing a numbered item.
    """
    indent = 420 * (level + 1)
    p = ET.Element(w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))
    ET.SubElement(p_pr, w_tag("pStyle"), {w_tag("val"): "ListParagraph"})
    ET.SubElement(p_pr, w_tag("ind"), {w_tag("left"): str(indent), w_tag("hanging"): "300"})

    r_num = ET.SubElement(p, w_tag("r"))
    r_num_pr = ET.SubElement(r_num, w_tag("rPr"))
    ET.SubElement(r_num_pr, w_tag("b"))
    ET.SubElement(r_num_pr, w_tag("sz"), {w_tag("val"): "20"})
    ET.SubElement(r_num_pr, w_tag("color"), {w_tag("val"): "1F4E79"})
    t_num = ET.SubElement(r_num, w_tag("t"))
    t_num.text = f"{prefix} "

    append_inline_formatting_to_paragraph(p, text, rels_mgr=rels_mgr)
    return p


def build_number_item(
    text: str,
    prefix: str = "1.",
    level: int = 0,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> str:
    """Builds a numbered list item paragraph string using ElementTree DOM."""
    p = build_number_item_element(text, prefix=prefix, level=level, rels_mgr=rels_mgr)
    return ET.tostring(p, encoding="unicode")

def build_divider_element() -> ET.Element:
    """Builds a horizontal divider paragraph element using ElementTree DOM.
    
    Returns:
        <w:p> ElementTree node representing a horizontal line.
    """
    p = ET.Element(w_tag("p"))
    p_pr = ET.SubElement(p, w_tag("pPr"))
    p_bdr = ET.SubElement(p_pr, w_tag("pBdr"))
    ET.SubElement(p_bdr, w_tag("bottom"), {
        w_tag("val"): "single",
        w_tag("sz"): "6",
        w_tag("space"): "4",
        w_tag("color"): "CBD5E0",
    })
    return p


def build_callout_box_elements(
    text: str,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> List[ET.Element]:
    """Builds a high-visibility styled callout box using ElementTree DOM.

    Args:
        text: Callout body text with optional alert annotations.
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.

    Returns:
        List of [tbl, spacer_p] ElementTree elements.
    """
    clean_text = text.strip()

    if "RMF TEAM" in clean_text.upper() or "[!IMPORTANT]" in clean_text or "ACTION REQUIRED" in clean_text.upper():
        title = "RMF TEAM / HUMAN ACTION REQUIRED"
        fill_color = "FEFCBF"
        border_color = "9B2C2C"
        title_color = "9B2C2C"
    elif "[!WARNING]" in clean_text or "CAUTION" in clean_text.upper():
        title = "WARNING / SECURITY NOTICE"
        fill_color = "FFF5F5"
        border_color = "DD6B20"
        title_color = "C53030"
    elif "[!TIP]" in clean_text:
        title = "BEST PRACTICE & RECOMMENDATION"
        fill_color = "E6FFFA"
        border_color = "319795"
        title_color = "234E52"
    else:
        title = "ARCHITECTURE & POLICY NOTE"
        fill_color = "EDF2F7"
        border_color = "1F4E79"
        title_color = "1F4E79"

    clean_text = re.sub(r'\[!(IMPORTANT|WARNING|NOTE|TIP|CAUTION)\]', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)
    clean_text = re.sub(r'\s*\*?\*?RMF TEAM[^:]+\*?\*?:?', '', clean_text, flags=re.IGNORECASE)
    clean_text = clean_text.replace(">", "").strip()

    tbl = ET.Element(w_tag("tbl"))
    tbl_pr = ET.SubElement(tbl, w_tag("tblPr"))
    ET.SubElement(tbl_pr, w_tag("tblW"), {w_tag("w"): "9360", w_tag("type"): "dxa"})

    borders = ET.SubElement(tbl_pr, w_tag("tblBorders"))
    ET.SubElement(borders, w_tag("top"), {w_tag("val"): "single", w_tag("sz"): "4", w_tag("space"): "0", w_tag("color"): "E2E8F0"})
    ET.SubElement(borders, w_tag("left"), {w_tag("val"): "single", w_tag("sz"): "24", w_tag("space"): "0", w_tag("color"): border_color})
    ET.SubElement(borders, w_tag("bottom"), {w_tag("val"): "single", w_tag("sz"): "4", w_tag("space"): "0", w_tag("color"): "E2E8F0"})
    ET.SubElement(borders, w_tag("right"), {w_tag("val"): "single", w_tag("sz"): "4", w_tag("space"): "0", w_tag("color"): "E2E8F0"})

    cell_mar = ET.SubElement(tbl_pr, w_tag("tblCellMar"))
    ET.SubElement(cell_mar, w_tag("top"), {w_tag("w"): "120", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("left"), {w_tag("w"): "200", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("bottom"), {w_tag("w"): "120", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("right"), {w_tag("w"): "200", w_tag("type"): "dxa"})

    tr = ET.SubElement(tbl, w_tag("tr"))
    tc = ET.SubElement(tr, w_tag("tc"))
    tc_pr = ET.SubElement(tc, w_tag("tcPr"))
    ET.SubElement(tc_pr, w_tag("tcW"), {w_tag("w"): "9360", w_tag("type"): "dxa"})
    ET.SubElement(tc_pr, w_tag("shd"), {w_tag("val"): "clear", w_tag("color"): "auto", w_tag("fill"): fill_color})

    p_title = ET.SubElement(tc, w_tag("p"))
    p_title_pr = ET.SubElement(p_title, w_tag("pPr"))
    ET.SubElement(p_title_pr, w_tag("spacing"), {w_tag("before"): "40", w_tag("after"): "40"})
    r_title = ET.SubElement(p_title, w_tag("r"))
    r_title_pr = ET.SubElement(r_title, w_tag("rPr"))
    ET.SubElement(r_title_pr, w_tag("b"))
    ET.SubElement(r_title_pr, w_tag("color"), {w_tag("val"): title_color})
    ET.SubElement(r_title_pr, w_tag("sz"), {w_tag("val"): "21"})
    t_title = ET.SubElement(r_title, w_tag("t"))
    t_title.text = clean_xml_text(title)

    p_body = ET.SubElement(tc, w_tag("p"))
    p_body_pr = ET.SubElement(p_body, w_tag("pPr"))
    ET.SubElement(p_body_pr, w_tag("spacing"), {w_tag("before"): "0", w_tag("after"): "60"})
    append_inline_formatting_to_paragraph(p_body, clean_text, rels_mgr=rels_mgr)

    spacer_p = ET.Element(w_tag("p"))
    spacer_p_pr = ET.SubElement(spacer_p, w_tag("pPr"))
    ET.SubElement(spacer_p_pr, w_tag("spacing"), {w_tag("after"): "100"})

    return [tbl, spacer_p]


def build_callout_box(
    text: str,
    rels_mgr: Optional[DocxRelationshipManager] = None,
) -> str:
    """Builds a high-visibility styled callout box returning XML string.
    
    Args:
        text: Callout body text with optional alert annotations.
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.
        
    Returns:
        Formatted XML string for the callout box elements.
    """
    elements = build_callout_box_elements(text, rels_mgr=rels_mgr)
    return "".join(ET.tostring(elem, encoding="unicode") for elem in elements)


def is_table_separator(line: str) -> bool:
    """Checks if a line is a markdown table separator row.

    Supports standard Markdown table separators with or without outer pipes.

    Args:
        line: Raw text line to inspect.

    Returns:
        True if the line conforms to Markdown separator syntax, else False.
    """
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    if not stripped:
        return False
    parts = [p.strip() for p in stripped.split("|")]
    return len(parts) > 0 and all(bool(re.match(r"^:?-+:?$", p)) for p in parts)


def build_code_box_elements(code_lines: List[str], language: str = "") -> List[ET.Element]:
    """Builds a styled, bordered preformatted code box using ElementTree DOM.

    Args:
        code_lines: Lines of source code or preformatted text.
        language: Optional language identifier for styling.

    Returns:
        List of [tbl, spacer_p] ElementTree elements.
    """
    tbl = ET.Element(w_tag("tbl"))
    tbl_pr = ET.SubElement(tbl, w_tag("tblPr"))
    ET.SubElement(tbl_pr, w_tag("tblW"), {w_tag("w"): "9360", w_tag("type"): "dxa"})

    borders = ET.SubElement(tbl_pr, w_tag("tblBorders"))
    for b_side in ["top", "left", "bottom", "right"]:
        ET.SubElement(borders, w_tag(b_side), {
            w_tag("val"): "single",
            w_tag("sz"): "6",
            w_tag("space"): "0",
            w_tag("color"): "CBD5E0",
        })

    cell_mar = ET.SubElement(tbl_pr, w_tag("tblCellMar"))
    ET.SubElement(cell_mar, w_tag("top"), {w_tag("w"): "120", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("left"), {w_tag("w"): "180", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("bottom"), {w_tag("w"): "120", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("right"), {w_tag("w"): "180", w_tag("type"): "dxa"})

    tr = ET.SubElement(tbl, w_tag("tr"))
    tc = ET.SubElement(tr, w_tag("tc"))
    tc_pr = ET.SubElement(tc, w_tag("tcPr"))
    ET.SubElement(tc_pr, w_tag("tcW"), {w_tag("w"): "9360", w_tag("type"): "dxa"})
    ET.SubElement(tc_pr, w_tag("shd"), {w_tag("val"): "clear", w_tag("color"): "auto", w_tag("fill"): "F7FAFC"})

    lines_to_render = code_lines if code_lines else [""]
    for cl in lines_to_render:
        p = ET.SubElement(tc, w_tag("p"))
        p_pr = ET.SubElement(p, w_tag("pPr"))
        ET.SubElement(p_pr, w_tag("spacing"), {
            w_tag("before"): "0",
            w_tag("after"): "0",
            w_tag("line"): "220",
            w_tag("lineRule"): "exact",
        })
        r = ET.SubElement(p, w_tag("r"))
        r_pr = ET.SubElement(r, w_tag("rPr"))
        ET.SubElement(r_pr, w_tag("rFonts"), {w_tag("ascii"): "Consolas", w_tag("hAnsi"): "Consolas"})
        ET.SubElement(r_pr, w_tag("sz"), {w_tag("val"): "17"})
        ET.SubElement(r_pr, w_tag("color"), {w_tag("val"): "2D3748"})
        t = ET.SubElement(r, w_tag("t"), {f"{{{XML_NS}}}space": "preserve"})
        t.text = clean_xml_text(cl)

    spacer_p = ET.Element(w_tag("p"))
    spacer_p_pr = ET.SubElement(spacer_p, w_tag("pPr"))
    ET.SubElement(spacer_p_pr, w_tag("spacing"), {w_tag("after"): "100"})

    return [tbl, spacer_p]


def build_code_box(code_lines: List[str], language: str = "") -> str:
    """Builds a styled, bordered preformatted code box returning XML string.
    
    Args:
        code_lines: Lines of source code or preformatted text.
        language: Optional language identifier for styling.
        
    Returns:
        Formatted XML string for the code box elements.
    """
    elements = build_code_box_elements(code_lines, language=language)
    return "".join(ET.tostring(elem, encoding="unicode") for elem in elements)


def calculate_optimal_column_widths(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    explicit_widths: Optional[Sequence[int]] = None,
) -> List[int]:
    """Calculates column widths in dxa (total exactly 9360 dxa) based on content weighting or explicit specs.

    Relying exclusively on dynamic content-weighted length analysis without brittle semantic keyword
    guessing, or scaling explicitly provided column-width arrays to match page margins.

    Args:
        headers: List or tuple of header column titles.
        rows: Sequence of table rows containing cell strings.
        explicit_widths: Optional explicit list of column widths in dxa.

    Returns:
        List of integer column widths in dxa totaling exactly 9360 dxa.
    """
    TOTAL_WIDTH = 9360
    col_count = len(headers) if headers else (max([len(r) for r in rows]) if rows else 1)
    if col_count <= 1:
        return [TOTAL_WIDTH]

    # 1. Honor explicit column width specifications if provided
    if explicit_widths and len(explicit_widths) == col_count and all(w > 0 for w in explicit_widths):
        raw_sum = sum(explicit_widths)
        scaled = [int((w / raw_sum) * TOTAL_WIDTH) for w in explicit_widths]
        rem = TOTAL_WIDTH - sum(scaled)
        scaled[-1] += rem
        return scaled

    # 2. Dynamic content-weighted length allocation algorithm
    base_min = max(400, TOTAL_WIDTH // (col_count * 3))
    col_scores: List[float] = []
    min_widths: List[int] = []

    for i in range(col_count):
        h_len = len(str(headers[i]).strip()) if i < len(headers) else 0
        cell_lens = [len(str(r[i]).strip()) for r in rows if i < len(r)]
        avg_len = sum(cell_lens) / len(cell_lens) if cell_lens else 0.0
        max_len = max(cell_lens) if cell_lens else 0

        # Dynamic content weighting: square-root dampened max length + average + header length
        weight = max(1.0, (math.sqrt(max_len) * 3.0) + (avg_len * 0.7) + (h_len * 0.4))
        col_scores.append(weight)

        c_min = min(base_min, max(400, int((h_len + avg_len) * 35))) if (max_len < 12 and avg_len < 8) else base_min
        min_widths.append(c_min)

    total_min = sum(min_widths)
    if total_min >= TOTAL_WIDTH:
        base = TOTAL_WIDTH // col_count
        rem = TOTAL_WIDTH % col_count
        widths = [base] * col_count
        widths[-1] += rem
        return widths

    avail_w = TOTAL_WIDTH - total_min
    total_score = sum(col_scores) or 1.0
    addl_w = [int((s / total_score) * avail_w) for s in col_scores]
    widths = [min_w + a for min_w, a in zip(min_widths, addl_w)]

    # Distribute rounding remainder to largest column
    rem = TOTAL_WIDTH - sum(widths)
    max_idx = widths.index(max(widths))
    widths[max_idx] += rem
    return widths


def build_table_elements(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    rels_mgr: Optional[DocxRelationshipManager] = None,
    col_widths: Optional[Sequence[int]] = None,
) -> List[ET.Element]:
    """Builds a high-fidelity OpenXML table with Navy header shading and alternating rows using ElementTree DOM.

    Args:
        headers: Table header column titles.
        rows: Sequence of table data rows.
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.
        col_widths: Optional explicit column widths in dxa.

    Returns:
        List of [tbl, spacer_p] ElementTree elements.
    """
    col_widths = calculate_optimal_column_widths(headers, rows, explicit_widths=col_widths)
    col_count = len(col_widths)

    tbl = ET.Element(w_tag("tbl"))
    tbl_pr = ET.SubElement(tbl, w_tag("tblPr"))
    ET.SubElement(tbl_pr, w_tag("tblW"), {w_tag("w"): "9360", w_tag("type"): "dxa"})

    borders = ET.SubElement(tbl_pr, w_tag("tblBorders"))
    for b_side, (sz, color) in [
        ("top", ("6", "CBD5E0")),
        ("left", ("6", "CBD5E0")),
        ("bottom", ("6", "CBD5E0")),
        ("right", ("6", "CBD5E0")),
        ("insideH", ("4", "E2E8F0")),
        ("insideV", ("4", "E2E8F0")),
    ]:
        ET.SubElement(borders, w_tag(b_side), {
            w_tag("val"): "single",
            w_tag("sz"): sz,
            w_tag("space"): "0",
            w_tag("color"): color,
        })

    cell_mar = ET.SubElement(tbl_pr, w_tag("tblCellMar"))
    ET.SubElement(cell_mar, w_tag("top"), {w_tag("w"): "100", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("left"), {w_tag("w"): "140", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("bottom"), {w_tag("w"): "100", w_tag("type"): "dxa"})
    ET.SubElement(cell_mar, w_tag("right"), {w_tag("w"): "140", w_tag("type"): "dxa"})

    tbl_grid = ET.SubElement(tbl, w_tag("tblGrid"))
    for w in col_widths:
        ET.SubElement(tbl_grid, w_tag("gridCol"), {w_tag("w"): str(w)})

    # Header Row
    if headers:
        tr = ET.SubElement(tbl, w_tag("tr"))
        tr_pr = ET.SubElement(tr, w_tag("trPr"))
        ET.SubElement(tr_pr, w_tag("tblHeader"))
        ET.SubElement(tr_pr, w_tag("cantSplit"))
        for idx in range(col_count):
            w_val = col_widths[idx]
            h_clean = headers[idx].strip() if idx < len(headers) else ""
            tc = ET.SubElement(tr, w_tag("tc"))
            tc_pr = ET.SubElement(tc, w_tag("tcPr"))
            ET.SubElement(tc_pr, w_tag("tcW"), {w_tag("w"): str(w_val), w_tag("type"): "dxa"})
            ET.SubElement(tc_pr, w_tag("shd"), {w_tag("val"): "clear", w_tag("color"): "auto", w_tag("fill"): "1F4E79"})
            ET.SubElement(tc_pr, w_tag("vAlign"), {w_tag("val"): "center"})

            p = ET.SubElement(tc, w_tag("p"))
            p_pr = ET.SubElement(p, w_tag("pPr"))
            ET.SubElement(p_pr, w_tag("spacing"), {w_tag("before"): "40", w_tag("after"): "40"})

            r = ET.SubElement(p, w_tag("r"))
            r_pr = ET.SubElement(r, w_tag("rPr"))
            ET.SubElement(r_pr, w_tag("b"))
            ET.SubElement(r_pr, w_tag("color"), {w_tag("val"): "FFFFFF"})
            ET.SubElement(r_pr, w_tag("sz"), {w_tag("val"): "19"})
            t = ET.SubElement(r, w_tag("t"))
            t.text = clean_xml_text(h_clean)

    # Data Rows
    for r_idx, row in enumerate(rows):
        row_cells = list(row)
        if len(row_cells) < col_count:
            row_cells.extend([""] * (col_count - len(row_cells)))
        elif len(row_cells) > col_count:
            row_cells = row_cells[:col_count - 1] + [" - ".join(row_cells[col_count - 1:])]

        fill_color = "F9FAFC" if (r_idx % 2 == 1) else "FFFFFF"
        tr = ET.SubElement(tbl, w_tag("tr"))
        tr_pr = ET.SubElement(tr, w_tag("trPr"))
        ET.SubElement(tr_pr, w_tag("cantSplit"))

        for idx in range(col_count):
            w_val = col_widths[idx]
            c_clean = row_cells[idx].strip()
            cell_paragraphs = re.split(r'<br\s*/?>', c_clean, flags=re.IGNORECASE)

            tc = ET.SubElement(tr, w_tag("tc"))
            tc_pr = ET.SubElement(tc, w_tag("tcPr"))
            ET.SubElement(tc_pr, w_tag("tcW"), {w_tag("w"): str(w_val), w_tag("type"): "dxa"})
            ET.SubElement(tc_pr, w_tag("shd"), {w_tag("val"): "clear", w_tag("color"): "auto", w_tag("fill"): fill_color})
            ET.SubElement(tc_pr, w_tag("vAlign"), {w_tag("val"): "top"})

            for cp in cell_paragraphs:
                p = ET.SubElement(tc, w_tag("p"))
                p_pr = ET.SubElement(p, w_tag("pPr"))
                ET.SubElement(p_pr, w_tag("spacing"), {w_tag("before"): "30", w_tag("after"): "30"})
                append_inline_formatting_to_paragraph(p, cp.strip(), rels_mgr=rels_mgr)

    spacer_p = ET.Element(w_tag("p"))
    spacer_p_pr = ET.SubElement(spacer_p, w_tag("pPr"))
    ET.SubElement(spacer_p_pr, w_tag("spacing"), {w_tag("after"): "100"})

    return [tbl, spacer_p]


def build_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    rels_mgr: Optional[DocxRelationshipManager] = None,
    col_widths: Optional[Sequence[int]] = None,
) -> str:
    """Builds a high-fidelity OpenXML table returning XML string.
    
    Args:
        headers: Table header column titles.
        rows: Sequence of table data rows.
        rels_mgr: Optional DocxRelationshipManager to register hyperlinks.
        col_widths: Optional explicit column widths in dxa.
        
    Returns:
        Formatted XML string for the table elements.
    """
    elements = build_table_elements(headers, rows, rels_mgr=rels_mgr, col_widths=col_widths)
    return "".join(ET.tostring(elem, encoding="unicode") for elem in elements)


# ------------------------------------------------------------------------------
# Master Conversion Engine
# ------------------------------------------------------------------------------

def convert_markdown_to_docx(
    markdown_content: str,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    allowed_boundary: Optional[str] = None,
) -> str:
    """Converts a Markdown policy or SSP document into a full .docx Word document using ElementTree DOM.

    Args:
        markdown_content: Markdown formatted text content.
        output_path: Target filesystem path for the output .docx document.
        metadata: Optional dictionary with system information and organizational metadata.
        allowed_boundary: Optional root directory that output_path must be confined inside.

    Returns:
        The path to the generated .docx file.
    """
    if metadata is not None:
        metadata = scrub_sensitive_data(metadata)
    lines = markdown_content.splitlines()
    doc_root = ET.Element(w_tag("document"))
    body = ET.SubElement(doc_root, w_tag("body"))
    rels_mgr = DocxRelationshipManager()

    # Extract Document Title from first Heading
    doc_title = "Enterprise Security Policy and Procedures"
    for line in lines:
        if line.startswith("# "):
            doc_title = line[2:].strip()
            break

    org_name = "Department of Defense / Enterprise"
    if metadata:
        org_name = metadata.get("system_information", {}).get("organization") or org_name

    in_table = False
    table_headers: List[str] = []
    table_rows: List[List[str]] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for Markdown Table Rows
        if "|" in stripped and not stripped.startswith(">"):
            if not in_table:
                # Lookahead to verify if next line is a table header separator
                if i + 1 < len(lines) and is_table_separator(lines[i+1]):
                    in_table = True
                    table_headers = split_markdown_table_row(stripped)
                    i += 2
                    table_rows = []
                    continue
            else:
                row_cells = split_markdown_table_row(stripped)
                if row_cells and not all(c.startswith("---") or c == "" for c in row_cells):
                    table_rows.append(row_cells)
                i += 1
                continue

        # If we reached the end of a table block
        if in_table:
            body.extend(build_table_elements(table_headers, table_rows, rels_mgr=rels_mgr))
            in_table = False
            table_headers = []
            table_rows = []

        # Handle Fenced Code Blocks (```)
        if stripped.startswith("```"):
            lang = stripped[3:].strip().lower()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            body.extend(build_code_box_elements(code_lines, language=lang))
            i += 1
            continue

        # Handle Callout Banners and Blockquotes
        if stripped.startswith(">"):
            callout_lines = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip().startswith(">"):
                callout_lines.append(lines[i].strip())
                i += 1
            cleaned_lines = [re.sub(r'^>\s*', '', cl).strip() for cl in callout_lines]
            callout_text = " ".join([cl for cl in cleaned_lines if cl])
            if callout_text:
                body.extend(build_callout_box_elements(callout_text, rels_mgr=rels_mgr))
            continue

        # Handle Headings
        if stripped.startswith("# "):
            title_text = stripped[2:].strip()
            body.append(build_paragraph_element(title_text, style="Title", rels_mgr=rels_mgr))
            t_lower = title_text.lower()
            if "runbook" in t_lower:
                sub_txt = "Tactical Incident Response Operational Runbook & Remediation Procedure"
            elif "authorization" in t_lower:
                sub_txt = "Master Authorization Roadmap & RMF Governance Strategy"
            elif "security plan" in t_lower or "ssp" in t_lower:
                sys_inf = (metadata or {}).get("system_information", {})
                b_line = sys_inf.get("compliance_baseline", "NIST SP 800-53 Rev. 5")
                imp_lvl = sys_inf.get("impact_level", "IL5")
                sub_txt = f"System Security Plan (SSP) & Control Implementation Specification ({b_line} / {imp_lvl})"
            elif "fips" in t_lower or "cryptographic" in t_lower:
                sub_txt = "FIPS 140-2 / FIPS 140-3 Cryptographic Module Validation Matrix"
            else:
                b_line = (metadata or {}).get("system_information", {}).get("compliance_baseline", "NIST SP 800-53 Rev. 5")
                sub_txt = f"{b_line} Compliance Policy & Technical Controls Manual"
            body.append(build_paragraph_element(sub_txt, style="Subtitle", rels_mgr=rels_mgr))
        elif stripped.startswith("## "):
            h_text = stripped[3:].strip()
            body.append(build_paragraph_element(h_text, style="Heading1", rels_mgr=rels_mgr))
        elif stripped.startswith("### "):
            h_text = stripped[4:].strip()
            body.append(build_paragraph_element(h_text, style="Heading2", rels_mgr=rels_mgr))
        elif stripped.startswith("#### "):
            h_text = stripped[5:].strip()
            body.append(build_paragraph_element(h_text, style="Heading3", rels_mgr=rels_mgr))
        elif stripped.startswith("##### "):
            h_text = stripped[6:].strip()
            body.append(build_paragraph_element(h_text, style="Heading4", rels_mgr=rels_mgr))
        elif stripped.startswith("(CCIs:") or stripped.startswith("(CCI-"):
            body.append(build_paragraph_element(stripped, style="CCI", rels_mgr=rels_mgr))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            body.append(build_bullet_item_element(stripped[2:].strip(), rels_mgr=rels_mgr))
        elif re.match(r'^\d+\.\s+', stripped):
            m = re.match(r'^(\d+\.)\s+(.*)', stripped)
            if m:
                prefix = m.group(1)
                item_text = m.group(2)
                body.append(build_number_item_element(item_text, prefix=prefix, rels_mgr=rels_mgr))
            else:
                body.append(build_bullet_item_element(stripped, rels_mgr=rels_mgr))
        elif stripped == "---":
            body.append(build_divider_element())
        elif stripped:
            body.append(build_paragraph_element(stripped, style="Normal", rels_mgr=rels_mgr))

        i += 1

    if in_table:
        body.extend(build_table_elements(table_headers, table_rows, rels_mgr=rels_mgr))

    # Assemble section properties & header/footer bindings using ElementTree DOM
    sect_pr = ET.SubElement(body, w_tag("sectPr"))
    ET.SubElement(sect_pr, w_tag("headerReference"), {w_tag("type"): "default", r_tag("id"): "rIdHeader"})
    ET.SubElement(sect_pr, w_tag("footerReference"), {w_tag("type"): "default", r_tag("id"): "rIdFooter"})
    ET.SubElement(sect_pr, w_tag("pgSz"), {w_tag("w"): "12240", w_tag("h"): "15840"})
    ET.SubElement(sect_pr, w_tag("pgMar"), {
        w_tag("top"): "1440",
        w_tag("right"): "1440",
        w_tag("bottom"): "1440",
        w_tag("left"): "1440",
        w_tag("header"): "720",
        w_tag("footer"): "720",
        w_tag("gutter"): "0",
    })

    raw_doc_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + ET.tostring(doc_root, encoding="unicode")
    document_xml = re.sub(r'<w:([a-zA-Z0-9]+)\s*/>', r'<w:\1/>', raw_doc_xml)

    # Write OpenXML ZIP package
    if allowed_boundary:
        out_target = ensure_path_within_boundary(output_path, allowed_boundary, allow_symlinks=False)
    else:
        out_target = resolve_path(output_path)
    ensure_directory(out_target.parent)
    
    with audit_operation(
        AuditEvent.ARTIFACT_GENERATED,
        obj=str(out_target),
        detail={"format": "docx"}
    ):
        with zipfile.ZipFile(str(out_target), 'w', compression=zipfile.ZIP_DEFLATED) as docx_zip:
            docx_zip.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
            docx_zip.writestr("_rels/.rels", ROOT_RELS_XML)
            docx_zip.writestr("word/_rels/document.xml.rels", rels_mgr.build_rels_xml())
            docx_zip.writestr("word/styles.xml", STYLES_XML)
            docx_zip.writestr("word/header1.xml", build_header_xml(doc_title, org_name))
            docx_zip.writestr("word/footer1.xml", build_footer_xml(doc_title, org_name))
            docx_zip.writestr("word/document.xml", document_xml)
            docx_zip.writestr("docProps/core.xml", build_core_xml(doc_title, org_name))
            docx_zip.writestr("docProps/app.xml", build_app_xml(org_name))

    logger.debug("Successfully created OpenXML Word document: %s", out_target)
    return str(out_target)


def batch_convert_policies_to_docx(
    policies_dir: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Converts all .md policy manuals in policies_dir to .docx documents.

    Args:
        policies_dir: Path to directory containing .md policy files.
        metadata: Optional system metadata for headers, footers, and properties.

    Returns:
        List of generated .docx file paths.
    """
    policies_path = resolve_path(policies_dir)
    generated: List[str] = []
    for filename in sorted(os.listdir(policies_dir)):
        if filename.endswith(".md"):
            md_path = os.path.join(policies_dir, filename)
            with open(md_path, "r", encoding="utf-8") as file_handle:
                content = file_handle.read()
            sanitized_stem = sanitize_filename(filename[:-3])
            docx_name = f"{sanitized_stem}.docx"
            docx_path = ensure_path_within_boundary(policies_path / docx_name, policies_path)
            convert_markdown_to_docx(content, str(docx_path), metadata)
            generated.append(str(docx_path))

    return generated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    if len(sys.argv) > 2:
        src_md = sys.argv[1]
        dest_docx = sys.argv[2]
        with open(src_md, "r", encoding="utf-8") as f_in:
            md_raw = f_in.read()
        convert_markdown_to_docx(md_raw, dest_docx)
        logger.info("Successfully converted %s -> %s", src_md, dest_docx)
    elif len(sys.argv) > 1:
        batch = batch_convert_policies_to_docx(sys.argv[1])
        logger.info("Batch converted %d policy manuals to .docx", len(batch))
    else:
        logger.info("Usage: docx_generator.py <source.md> <dest.docx> OR docx_generator.py <policies_dir>")
