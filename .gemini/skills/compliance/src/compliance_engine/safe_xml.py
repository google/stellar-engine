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

"""Hardened XML parsing facade for the compliance engine.

This module is the single sanctioned entry point for XML deserialization across
the compliance pipeline. It defends against the XML attack classes that matter
for a FedRAMP / NIST SP 800-53 authorization boundary:

* **CWE-611 (XXE / External Entity Injection)** - external entity references and
  external DTD subsets are rejected outright.
* **CWE-776 (XML Entity Expansion / "billion laughs")** - internal entity
  declarations are rejected, so exponential expansion is impossible.
* **CWE-400 (Uncontrolled Resource Consumption)** - hard caps on document size,
  nesting depth, and total element count bound memory and CPU during parsing of
  untrusted OpenXML (`.docx`, `.xlsx`) payloads.
* **CWE-674 (Uncontrolled Recursion)** - traversal is iterative, never recursive,
  so a deeply nested document cannot exhaust the interpreter stack.

Backend selection is explicit and fails closed:

1. If the genuine, independently audited ``defusedxml`` package is installed it is
   used for deserialization and reported via :data:`BACKEND`.
2. Otherwise the in-repo :class:`HardenedXMLParser` (pyexpat with every unsafe
   handler disabled) is used.

The bare standard library ``xml.etree.ElementTree`` parser is never used for
deserialization. Element *construction* and *serialization* helpers are re-exported
from the standard library because they do not process untrusted input.

.. note::
   This module is intentionally **not** named ``defusedxml``. An earlier revision
   vendored a package literally named ``defusedxml`` inside ``scripts/``, which
   silently shadowed the real PyPI distribution on ``sys.path`` and made the
   documented ``pip install defusedxml`` a no-op. Naming the facade ``safe_xml``
   removes that namespace-hijack hazard.
"""

from __future__ import annotations

import io
import logging
import os
import sys
from typing import Any, BinaryIO, Dict, Final, Iterator, List, Optional, Tuple, Union
from xml.etree.ElementTree import (
    Element,
    ElementTree,
    ParseError,
    QName,
    SubElement,
    TreeBuilder,
    iselement,
    register_namespace,
    tostring,
    tostringlist,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BACKEND",
    "DTDForbidden",
    "DefusedXmlException",
    "Element",
    "ElementTree",
    "EntitiesForbidden",
    "ExternalReferenceForbidden",
    "HardenedXMLParser",
    "MAX_XML_BYTES",
    "MAX_XML_DEPTH",
    "MAX_XML_ELEMENTS",
    "ParseError",
    "QName",
    "SubElement",
    "TreeBuilder",
    "XmlLimitExceeded",
    "fromstring",
    "iselement",
    "iterparse",
    "parse",
    "register_namespace",
    "tostring",
    "tostringlist",
]

# ---------------------------------------------------------------------------
# Resource limits (CWE-400). Overridable via environment for large but trusted
# corpora; values are clamped to a sane ceiling so configuration cannot disable
# the protection entirely.
# ---------------------------------------------------------------------------

_DEFAULT_MAX_XML_BYTES: Final[int] = 64 * 1024 * 1024  # 64 MiB
_ABSOLUTE_MAX_XML_BYTES: Final[int] = 512 * 1024 * 1024  # 512 MiB hard ceiling
_DEFAULT_MAX_XML_DEPTH: Final[int] = 256
_ABSOLUTE_MAX_XML_DEPTH: Final[int] = 1024
_DEFAULT_MAX_XML_ELEMENTS: Final[int] = 5_000_000
_ABSOLUTE_MAX_XML_ELEMENTS: Final[int] = 20_000_000

_READ_CHUNK_BYTES: Final[int] = 65536


def _bounded_int_from_env(env_var: str, default: int, ceiling: int) -> int:
    """Reads a positive integer tuning knob from the environment, clamped to a ceiling.

    Args:
        env_var: Name of the environment variable to consult.
        default: Value used when the variable is unset or malformed.
        ceiling: Inclusive maximum; larger configured values are clamped down.

    Returns:
        A positive integer no greater than ``ceiling``.
    """
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning(
            "Ignoring non-integer %s=%r; falling back to default %d", env_var, raw, default
        )
        return default
    if value <= 0:
        logger.warning("Ignoring non-positive %s=%d; falling back to default %d", env_var, value, default)
        return default
    if value > ceiling:
        logger.warning("Clamping %s=%d down to hard ceiling %d", env_var, value, ceiling)
        return ceiling
    return value


MAX_XML_BYTES: Final[int] = _bounded_int_from_env(
    "COMPLIANCE_MAX_XML_BYTES", _DEFAULT_MAX_XML_BYTES, _ABSOLUTE_MAX_XML_BYTES
)
MAX_XML_DEPTH: Final[int] = _bounded_int_from_env(
    "COMPLIANCE_MAX_XML_DEPTH", _DEFAULT_MAX_XML_DEPTH, _ABSOLUTE_MAX_XML_DEPTH
)
MAX_XML_ELEMENTS: Final[int] = _bounded_int_from_env(
    "COMPLIANCE_MAX_XML_ELEMENTS", _DEFAULT_MAX_XML_ELEMENTS, _ABSOLUTE_MAX_XML_ELEMENTS
)


# ---------------------------------------------------------------------------
# Exception hierarchy (API-compatible with defusedxml)
# ---------------------------------------------------------------------------


class DefusedXmlException(ValueError):
    """Base class for every XML deserialization security violation."""


class DTDForbidden(DefusedXmlException):
    """Raised when a document type declaration is encountered."""

    def __init__(self, name: Optional[str], sysid: Optional[str], pubid: Optional[str]) -> None:
        super().__init__(f"DTDForbidden(name={name!r}, sysid={sysid!r}, pubid={pubid!r})")
        self.name = name
        self.sysid = sysid
        self.pubid = pubid


class EntitiesForbidden(DefusedXmlException):
    """Raised when an entity declaration is encountered (CWE-776)."""

    def __init__(
        self,
        name: Optional[str],
        value: Optional[str],
        base: Optional[str],
        sysid: Optional[str],
        pubid: Optional[str],
        notation_name: Optional[str],
    ) -> None:
        super().__init__(
            f"EntitiesForbidden(name={name!r}, sysid={sysid!r}, pubid={pubid!r})"
        )
        self.name = name
        self.value = value
        self.base = base
        self.sysid = sysid
        self.pubid = pubid
        self.notation_name = notation_name


class ExternalReferenceForbidden(DefusedXmlException):
    """Raised when an external entity reference is encountered (CWE-611)."""

    def __init__(
        self,
        context: Optional[str],
        base: Optional[str],
        sysid: Optional[str],
        pubid: Optional[str],
    ) -> None:
        super().__init__(
            f"ExternalReferenceForbidden(context={context!r}, base={base!r}, "
            f"sysid={sysid!r}, pubid={pubid!r})"
        )
        self.context = context
        self.base = base
        self.sysid = sysid
        self.pubid = pubid


class XmlLimitExceeded(DefusedXmlException):
    """Raised when a document exceeds a configured size, depth, or element budget."""


# ---------------------------------------------------------------------------
# Hardened pyexpat-backed parser (used when defusedxml is unavailable)
# ---------------------------------------------------------------------------


class HardenedXMLParser:
    """Incremental XML parser with all unsafe expat features disabled.

    Every hazardous expat callback is wired to a handler that raises, so the
    parser fails closed rather than degrading to permissive behavior. Depth,
    element count, and cumulative byte budgets are enforced while feeding, which
    means an abusive document is rejected mid-stream instead of after it has
    already been buffered into memory.
    """

    def __init__(
        self,
        *,
        target: Optional[TreeBuilder] = None,
        encoding: Optional[str] = None,
        max_depth: int = MAX_XML_DEPTH,
        max_elements: int = MAX_XML_ELEMENTS,
        max_bytes: int = MAX_XML_BYTES,
    ) -> None:
        """Initializes the hardened parser.

        Args:
            target: Optional tree builder receiving parse events.
            encoding: Optional explicit document encoding.
            max_depth: Maximum permitted element nesting depth.
            max_elements: Maximum permitted total element count.
            max_bytes: Maximum permitted cumulative input size in bytes.
        """
        # Imported lazily so that environments without pyexpat surface a clear
        # error only when the fallback parser is actually needed.
        import pyexpat

        self._pyexpat = pyexpat
        self.target: TreeBuilder = target if target is not None else TreeBuilder()
        self.max_depth = max_depth
        self.max_elements = max_elements
        self.max_bytes = max_bytes

        self._depth = 0
        self._elements = 0
        self._bytes_seen = 0
        self._closed = False

        parser = pyexpat.ParserCreate(encoding=encoding, namespace_separator=" ")
        # Coalesce character data so the tree builder sees whole text nodes.
        parser.buffer_text = True
        # Never resolve anything outside the document.
        parser.SetParamEntityParsing(pyexpat.XML_PARAM_ENTITY_PARSING_NEVER)
        parser.StartElementHandler = self._start_element
        parser.EndElementHandler = self._end_element
        parser.CharacterDataHandler = self._character_data
        parser.EntityDeclHandler = self._entity_decl
        parser.UnparsedEntityDeclHandler = self._unparsed_entity_decl
        parser.StartDoctypeDeclHandler = self._start_doctype_decl
        parser.ExternalEntityRefHandler = self._external_entity_ref
        self._parser = parser

    @staticmethod
    def _qualify(name: str) -> str:
        """Converts an expat space-separated namespace name into ElementTree form."""
        if " " in name:
            uri, local = name.split(" ", 1)
            return f"{{{uri}}}{local}"
        return name

    def _start_element(self, name: str, attrs: Dict[str, str]) -> None:
        self._depth += 1
        self._elements += 1
        if self._depth > self.max_depth:
            raise XmlLimitExceeded(
                f"XML nesting depth exceeded the configured maximum of {self.max_depth}"
            )
        if self._elements > self.max_elements:
            raise XmlLimitExceeded(
                f"XML element count exceeded the configured maximum of {self.max_elements}"
            )
        qualified_attrs = {self._qualify(k): v for k, v in attrs.items()}
        self.target.start(self._qualify(name), qualified_attrs)

    def _end_element(self, name: str) -> None:
        self._depth -= 1
        self.target.end(self._qualify(name))

    def _character_data(self, data: str) -> None:
        self.target.data(data)

    def _entity_decl(
        self,
        name: str,
        is_parameter_entity: int,
        value: Optional[str],
        base: Optional[str],
        sysid: Optional[str],
        pubid: Optional[str],
        notation_name: Optional[str],
    ) -> None:
        raise EntitiesForbidden(name, value, base, sysid, pubid, notation_name)

    def _unparsed_entity_decl(
        self,
        name: str,
        base: Optional[str],
        sysid: Optional[str],
        pubid: Optional[str],
        notation_name: Optional[str],
    ) -> None:
        raise EntitiesForbidden(name, None, base, sysid, pubid, notation_name)

    def _start_doctype_decl(
        self,
        name: Optional[str],
        sysid: Optional[str],
        pubid: Optional[str],
        has_internal_subset: int,
    ) -> None:
        raise DTDForbidden(name, sysid, pubid)

    def _external_entity_ref(
        self,
        context: Optional[str],
        base: Optional[str],
        sysid: Optional[str],
        pubid: Optional[str],
    ) -> int:
        raise ExternalReferenceForbidden(context, base, sysid, pubid)

    def feed(self, data: Union[str, bytes]) -> None:
        """Feeds a chunk of document data into the parser.

        Args:
            data: Raw XML bytes, or text that will be encoded as UTF-8.

        Raises:
            XmlLimitExceeded: If the cumulative byte budget is exhausted.
            ParseError: If the chunk is not well-formed XML.
            DefusedXmlException: If a forbidden XML construct is encountered.
        """
        if self._closed:
            raise ParseError("Cannot feed data to a parser that has already been closed")
        payload = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        self._bytes_seen += len(payload)
        if self._bytes_seen > self.max_bytes:
            raise XmlLimitExceeded(
                f"XML document exceeded the configured maximum size of {self.max_bytes} bytes"
            )
        try:
            self._parser.Parse(payload, False)
        except self._pyexpat.ExpatError as err:
            raise ParseError(str(err)) from err

    def close(self) -> Element:
        """Finalizes parsing and returns the root element.

        Returns:
            The root :class:`~xml.etree.ElementTree.Element` of the document.

        Raises:
            ParseError: If the document is truncated or not well-formed.
        """
        if self._closed:
            raise ParseError("Parser has already been closed")
        self._closed = True
        try:
            self._parser.Parse(b"", True)
        except self._pyexpat.ExpatError as err:
            raise ParseError(str(err)) from err
        finally:
            # Break expat's reference cycle back into this object so the parser
            # and its buffers are reclaimed promptly rather than waiting on GC.
            self._release_handlers()
        return self.target.close()

    def _release_handlers(self) -> None:
        """Detaches bound-method handlers to drop the parser reference cycle."""
        for attr in (
            "StartElementHandler",
            "EndElementHandler",
            "CharacterDataHandler",
            "EntityDeclHandler",
            "UnparsedEntityDeclHandler",
            "StartDoctypeDeclHandler",
            "ExternalEntityRefHandler",
        ):
            try:
                setattr(self._parser, attr, None)
            except (AttributeError, TypeError):  # pragma: no cover - defensive
                logger.debug("Could not detach expat handler %s", attr)


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------


def _load_defusedxml_backend() -> Optional[Any]:
    """Imports the genuine defusedxml ElementTree backend when it is installed.

    Returns:
        The ``defusedxml.ElementTree`` module, or None when unavailable or when
        the resolved module is not the authentic distribution.
    """
    try:
        import defusedxml  # noqa: F401  (presence check)
        import defusedxml.ElementTree as defused_etree
    except ImportError:
        return None

    # Verify the resolved module genuinely exposes the defusedxml contract rather
    # than being an unrelated module that happens to occupy the name.
    #
    # Probe only attributes the real distribution actually exports from the
    # ElementTree submodule. Notably `DefusedXmlException` lives in
    # `defusedxml.common`, not here, and the builder helpers (`Element`,
    # `SubElement`, `register_namespace`) are deliberately absent because
    # defusedxml wraps the *parsing* surface only. Requiring either of those
    # rejects the authentic library and silently downgrades to the fallback.
    required = (
        "fromstring",
        "parse",
        "iterparse",
        "DTDForbidden",
        "EntitiesForbidden",
        "ExternalReferenceForbidden",
    )
    missing = [attr for attr in required if not hasattr(defused_etree, attr)]
    if missing:
        logger.warning(
            "Module named 'defusedxml.ElementTree' is missing %s; falling back to "
            "the in-repo hardened parser.",
            ", ".join(missing),
        )
        return None
    return defused_etree


_DEFUSED = _load_defusedxml_backend()

BACKEND: Final[str] = "defusedxml.ElementTree" if _DEFUSED is not None else "safe_xml.HardenedXMLParser"

if _DEFUSED is not None:
    # Adopt the upstream exception classes as the facade's own. Without this the
    # taxonomy silently changes with the backend: callers writing
    # `except safe_xml.DTDForbidden` would keep working against the in-repo parser
    # but stop catching anything once the genuine library is installed, turning a
    # handled rejection into an uncaught crash.
    _defused_common = sys.modules.get("defusedxml.common")
    DefusedXmlException = getattr(  # type: ignore[misc] - dynamically aliasing upstream exception classes at runtime to preserve unified exception taxonomy
        _defused_common, "DefusedXmlException", DefusedXmlException
    )
    DTDForbidden = getattr(_DEFUSED, "DTDForbidden", DTDForbidden)  # type: ignore[misc] - dynamically aliasing upstream exception classes at runtime to preserve unified exception taxonomy
    EntitiesForbidden = getattr(  # type: ignore[misc] - dynamically aliasing upstream exception classes at runtime to preserve unified exception taxonomy
        _DEFUSED, "EntitiesForbidden", EntitiesForbidden
    )
    ExternalReferenceForbidden = getattr(  # type: ignore[misc] - dynamically aliasing upstream exception classes at runtime to preserve unified exception taxonomy
        _DEFUSED, "ExternalReferenceForbidden", ExternalReferenceForbidden
    )


def _enforce_depth_budget(root: Element) -> Element:
    """Rejects a parsed tree whose nesting exceeds :data:`MAX_XML_DEPTH`.

    Upstream defusedxml defends against DTDs, entity expansion, and external
    references, but it does not bound nesting depth. A deeply nested document is
    therefore parsed successfully and only detonates later, in whatever consumer
    walks it recursively (CWE-400 / stack exhaustion). Adopting the genuine library
    must not silently drop a protection the in-repo parser already provided, so the
    budget is enforced here instead.

    The traversal uses an explicit stack; validating a depth bomb must not itself
    recurse.

    Args:
        root: The parsed document root.

    Returns:
        The same root element, when it is within budget.

    Raises:
        XmlLimitExceeded: If nesting exceeds :data:`MAX_XML_DEPTH`.
    """
    stack: List[Tuple[Element, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_XML_DEPTH:
            raise XmlLimitExceeded(
                f"XML nesting depth exceeds the configured maximum of {MAX_XML_DEPTH}"
            )
        next_depth = depth + 1
        for child in node:
            stack.append((child, next_depth))
    return root


# ---------------------------------------------------------------------------
# Public parsing API
# ---------------------------------------------------------------------------


def fromstring(text: Union[str, bytes]) -> Element:
    """Parses an XML document from an in-memory string or byte buffer.

    DTDs, entity declarations, and external references are rejected. Size, depth,
    and element-count budgets are enforced.

    Args:
        text: The XML document as text or bytes.

    Returns:
        The root :class:`~xml.etree.ElementTree.Element`.

    Raises:
        XmlLimitExceeded: If the document exceeds a configured resource budget.
        DefusedXmlException: If a forbidden XML construct is present.
        ParseError: If the document is not well-formed XML.
    """
    raw = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    if len(raw) > MAX_XML_BYTES:
        raise XmlLimitExceeded(
            f"XML document of {len(raw)} bytes exceeds the configured maximum of {MAX_XML_BYTES} bytes"
        )
    if _DEFUSED is not None:
        root = _DEFUSED.fromstring(
            raw, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
        return _enforce_depth_budget(root)
    parser = HardenedXMLParser()
    parser.feed(raw)
    return parser.close()


# Alias matching the ElementTree/defusedxml convention.
XML = fromstring


def _iter_source_chunks(
    source: Union[str, bytes, "os.PathLike[str]", BinaryIO]
) -> Iterator[bytes]:
    """Yields bounded byte chunks from a filename or binary file-like object.

    Args:
        source: A filesystem path or an already-open binary stream.

    Yields:
        Byte chunks of at most :data:`_READ_CHUNK_BYTES`.
    """
    if isinstance(source, (str, bytes, os.PathLike)):
        with open(source, "rb") as handle:
            while True:
                chunk = handle.read(_READ_CHUNK_BYTES)
                if not chunk:
                    return
                yield chunk
    else:
        while True:
            chunk = source.read(_READ_CHUNK_BYTES)
            if not chunk:
                return
            yield chunk.encode("utf-8") if isinstance(chunk, str) else chunk


def parse(source: Union[str, bytes, "os.PathLike[str]", BinaryIO]) -> ElementTree:
    """Parses an XML document from a filesystem path or binary stream.

    The document is streamed in bounded chunks so an oversized file is rejected
    before it is fully buffered in memory.

    Args:
        source: A filesystem path or an open binary file-like object.

    Returns:
        An :class:`~xml.etree.ElementTree.ElementTree` wrapping the parsed root.

    Raises:
        XmlLimitExceeded: If the document exceeds a configured resource budget.
        DefusedXmlException: If a forbidden XML construct is present.
        ParseError: If the document is not well-formed XML.
        OSError: If the source path cannot be opened.
    """
    if _DEFUSED is not None:
        # Enforce the size budget ourselves; defusedxml does not bound file size.
        buffered = io.BytesIO()
        total = 0
        for chunk in _iter_source_chunks(source):
            total += len(chunk)
            if total > MAX_XML_BYTES:
                raise XmlLimitExceeded(
                    f"XML document exceeds the configured maximum of {MAX_XML_BYTES} bytes"
                )
            buffered.write(chunk)
        root = _DEFUSED.fromstring(
            buffered.getvalue(), forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
        return ElementTree(_enforce_depth_budget(root))

    parser = HardenedXMLParser()
    for chunk in _iter_source_chunks(source):
        parser.feed(chunk)
    return ElementTree(parser.close())


def iterparse(
    source: Union[str, bytes, "os.PathLike[str]", BinaryIO],
    events: Optional[Tuple[str, ...]] = None,
) -> Iterator[Tuple[str, Element]]:
    """Iteratively yields ``(event, element)`` pairs for a parsed XML document.

    Traversal is performed with an explicit stack rather than recursion so that a
    maliciously deep document cannot exhaust the interpreter stack (CWE-674).

    Args:
        source: A filesystem path or an open binary file-like object.
        events: Event names to emit; defaults to ``("end",)``.

    Yields:
        Tuples of ``(event_name, element)``.

    Raises:
        XmlLimitExceeded: If the document exceeds a configured resource budget.
        DefusedXmlException: If a forbidden XML construct is present.
        ParseError: If the document is not well-formed XML.
    """
    wanted = tuple(events) if events else ("end",)
    root = parse(source).getroot()

    emit_start = "start" in wanted
    emit_end = "end" in wanted

    # Explicit stack of (element, children_visited) frames.
    stack: List[Tuple[Element, bool]] = [(root, False)]
    while stack:
        element, expanded = stack.pop()
        if expanded:
            if emit_end:
                yield ("end", element)
            continue
        if emit_start:
            yield ("start", element)
        stack.append((element, True))
        for child in reversed(list(element)):
            stack.append((child, False))


logger.debug("safe_xml initialized with backend %s", BACKEND)
