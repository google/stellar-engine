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

# flake8: noqa
# Intentionally insecure scanner fixture for `semgrep --test`; never imported or executed.
# A "ruleid" annotation marks the next line as a required match; an "ok" annotation marks it as forbidden.

import xml.dom.minidom
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring as et_fromstring

import defusedxml.ElementTree as DET
import lxml.etree

data = b"<a/>"
# ruleid: python-xxe-unsafe-xml-parser
x1 = ET.fromstring(data)
# ruleid: python-xxe-unsafe-xml-parser
x2 = et_fromstring(data)
# ruleid: python-xxe-unsafe-xml-parser
x3 = xml.dom.minidom.parseString(data)
# ruleid: python-xxe-unsafe-xml-parser
x4 = lxml.etree.XMLParser(resolve_entities=True)
# ok: python-xxe-unsafe-xml-parser
x5 = DET.fromstring(data)
# ok: python-xxe-unsafe-xml-parser
x6 = ET.tostring(ET.Element("a"))
