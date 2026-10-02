# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Optional CI bootstrap for a checksummed, unpinned core wheel candidate."""
import argparse
import json
import os
import re
import subprocess
import sys
from urllib.parse import urlsplit


VERIFY = '''
import json, sys
from importlib.metadata import distribution
expected = json.load(sys.stdin)
core = distribution('gramlot')
assert core.version == expected['version'], 'Installed Gramlot version differs from the candidate wheel'
record = json.loads(core.read_text('direct_url.json') or '{}')
assert record.get('url') == expected['url'], 'Installed Gramlot is not the supplied candidate URL'
archive = record.get('archive_info', {})
digest = archive.get('hashes', {}).get('sha256')
if digest is None and archive.get('hash', '').startswith('sha256='):
    digest = archive['hash'].split('=', 1)[1]
assert digest == expected['sha256'], 'Installed Gramlot candidate checksum differs'
'''



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--verify', action='store_true', help='Recheck the candidate after dependency resolution')
    args = parser.parse_args()
    url = os.environ.get('CORE_WHEEL_URL', '')
    checksum = os.environ.get('CORE_WHEEL_SHA256', '')
    if not url and not checksum:
        return
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.netloc or parsed.fragment
            or not parsed.path.endswith('.whl')
            or not re.fullmatch('[0-9a-fA-F]{64}', checksum)):
        raise SystemExit('Candidate requires an HTTPS wheel URL and its SHA-256 checksum')
    filename = parsed.path.rsplit('/', 1)[-1]
    match = re.fullmatch(r'gramlot-([^-]+)-py3-none-any\.whl', filename)
    if match is None:
        raise SystemExit('Candidate wheel filename must expose the Gramlot version')
    if not args.verify:
        subprocess.run([args.python, '-m', 'pip', 'install', '--only-binary=:all:',
                        f'{url}#sha256={checksum}'], check=True)
    subprocess.run([args.python, '-I', '-c', VERIFY], check=True, text=True,
                   input=json.dumps({'version': match[1], 'url': url,
                                     'sha256': checksum.lower()}))


if __name__ == '__main__':
    main()
