#!/usr/bin/env python3

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Recursively check link destination validity in Markdown files.

This tool recursively checks that local links in Markdown files point to valid
destinations. Its main use is in CI pipelines triggered by pull requests.
'''

import collections
import ipaddress
import pathlib
import socket
import requests
import urllib.parse

import click
import marko

BASEDIR = pathlib.Path(__file__).resolve().parents[1]
DOC = collections.namedtuple('DOC', 'path relpath links')
LINK = collections.namedtuple('LINK', 'dest valid')


def check_link(link, readme_path, external):
  'Checks if a link element has a valid destination.'
  link_valid = None
  url = urllib.parse.urlparse(link.dest)
  # If the link is public, say the link is anyway valid
  # if --external is not set; check the link otherwise
  if url.scheme:
    if url.scheme not in ('http', 'https'):
      return LINK(link.dest, False)
    link_valid = True
    if external:
      try:
        hostname = url.hostname
        if not hostname:
          return LINK(link.dest, False)
        for info in socket.getaddrinfo(hostname, None):
          ip = ipaddress.ip_address(info[4][0])
          if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return LINK(link.dest, False)
        response = requests.get(link.dest, timeout=10)
        link_valid = response.ok
      except (requests.exceptions.RequestException, socket.gaierror, ValueError):
        link_valid = False
  # The link is private
  else:
    target = (readme_path.parent / url.path).resolve()
    link_valid = target.is_relative_to(BASEDIR.resolve()) and target.exists()
  return LINK(link.dest, link_valid)


def check_docs(dir_name, external=False):
  'Traverses dir_name and checks for all Markdown files.'
  dir_path = BASEDIR / dir_name
  parser = marko.parser.Parser()
  for readme_path in sorted(dir_path.glob('**/*.md')):
    if '.terraform' in str(readme_path) or '.pytest' in str(readme_path):
      continue

    root = parser.parse(readme_path.read_text())
    elements = collections.deque([root])
    links = []
    while elements:
      el = elements.popleft()
      if isinstance(el, marko.inline.Link):
        links.append(check_link(el, readme_path, external))
      elif hasattr(el, 'children'):
        elements.extend(el.children)

    yield DOC(readme_path, str(readme_path.relative_to(dir_path)), links)


@click.command()
@click.argument('dirs', type=str, nargs=-1)
@click.option('-e', '--external', is_flag=True, default=False,
              help='Whether to test external links.')
@click.option('--show-summary/--no-show-summary', default=True)
def main(dirs, external, show_summary=True):
  'Checks links in Markdown files contained in dirs.'
  errors = []
  for dir_name in dirs:
    if show_summary:
      print(f'----- {dir_name} -----')
    for doc in check_docs(dir_name, external):
      state = '✓' if all(l.valid for l in doc.links) else '✗'
      if show_summary:
        print(f'[{state}] {doc.relpath} ({len(doc.links)})')
      if state == '✗':
        error = [f'{dir_name}/{doc.relpath}']
        for l in doc.links:
          if not l.valid:
            error.append(f'  - {l.dest}')
            if show_summary:
              print(f'  {l.dest}')
        errors.append('\n'.join(error))
  if errors:
    raise SystemExit('Errors found:\n{}'.format('\n'.join(errors)))


if __name__ == '__main__':
  main()
