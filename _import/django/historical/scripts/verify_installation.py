# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Verify installed wheels in an external project, optionally through a real browser.

The runner may have Playwright; the target Python environment needs only the
installed application dependencies. No repository is put on its import path.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PROBE = '''import importlib.util, json, sys
from pathlib import Path
from importlib.metadata import version
import gramlot, gramlot_django
from gramlot.hosting import RuntimeAssets
for module in (gramlot, gramlot_django):
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), module.__file__
assert importlib.util.find_spec('gramlot.contrib.django') is None
assert importlib.util.find_spec('fastapi') is None
assert importlib.util.find_spec('wagtail') is None
runtime = RuntimeAssets('/tools/ui')
mounts = runtime.asset_mounts()
assert len(mounts) == 1 and mounts[0].immutable, 'Compiled browser payload required'
print(json.dumps({'gramlot': version('gramlot'), 'gramlot-django': version('gramlot-django'),
                  'runtime_url': runtime.entry_url}))
'''


def check_browser(url):
    from playwright.sync_api import expect, sync_playwright

    errors, external, bad_responses = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text)
                if message.type == 'error' else None)
        page.on('response', lambda response: bad_responses.append(
            f'{response.status}: {response.url}') if response.status >= 400 else None)

        def local_only(route):
            if urlsplit(route.request.url)[:2] == urlsplit(url)[:2]:
                route.continue_()
            else:
                external.append(route.request.url)
                route.abort()

        # All off-site browser requests are blocked during the complete smoke.
        page.route('**/*', local_only)
        page.goto(url + '/tools/ui/hello/')
        expect(page.locator('#server-greeting')).to_have_text('Hello, Ada!')
        expect(page.locator('#remote-note')).to_have_text('Built in Python for Ada.')
        expect(page.locator('gnr-codemirror .cm-editor')).to_be_visible(timeout=20000)
        field = page.get_by_label('Name', exact=True)
        field.fill('Grace')
        field.press('Tab')
        expect(page.locator('#bound-name')).to_have_text('Grace')
        expect(page.locator('#server-greeting')).to_have_text('Hello, Grace!')
        expect(page.locator('#remote-note')).to_have_text('Built in Python for Grace.')
        page.goto(url + '/tools/ui/editors/')
        html_editor = page.locator('#html-editor')
        html_editor.get_by_role('button', name='Rich text', exact=True).click()
        expect(html_editor.locator('.jodit-container')).to_be_visible(timeout=20000)
        # These controls come from optional Jodit plugins, not its bare ESM core.
        expect(html_editor.get_by_label('Clear Formatting', exact=True).first).to_be_visible()
        expect(html_editor.get_by_label('Find', exact=True).first).to_be_visible()
        markdown_editor = page.locator('#markdown-editor')
        markdown_editor.get_by_role('button', name='Rich text', exact=True).click()
        expect(markdown_editor.locator('.ProseMirror')).to_be_visible(timeout=20000)
        assert not errors, errors
        assert not external, external
        assert not bad_responses, bad_responses
        browser.close()


def check_polls_browser(url):
    from playwright.sync_api import expect, sync_playwright

    failures = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on('pageerror', lambda error: failures.append(str(error)))
        page.on('console', lambda message: failures.append(message.text)
                if message.type == 'error' else None)
        page.on('response', lambda response: failures.append(str(response.status))
                if response.status >= 400 else None)

        def local_only(route):
            if urlsplit(route.request.url)[:2] == urlsplit(url)[:2]:
                route.continue_()
            else:
                failures.append(route.request.url)
                route.abort()

        page.route('**/*', local_only)
        page.goto(url + '/polls/')
        expect(page.get_by_role('heading', name='Polls', exact=True)).to_be_visible()
        page.get_by_role('link', name='What would you like to build with Gramlot?').click()
        page.get_by_label('A dashboard', exact=True).check()
        page.get_by_role('button', name='Vote', exact=True).click()
        expect(page.locator('#standard-result-1')).to_have_text('A dashboard: 1')
        page.get_by_role('link', name='Interactive workspace').click()
        expect(page.get_by_role('heading', name='Interactive polls')).to_be_visible()
        expect(page.get_by_role('navigation', name='Site navigation')).to_be_visible()
        result = page.locator('#result-1')
        expect(result).to_have_text('A dashboard: 1')
        page.get_by_role('button', name='A dashboard', exact=True).click()
        expect(result).to_have_text('A dashboard: 2')
        page.reload()
        expect(result).to_have_text('A dashboard: 2')
        page.get_by_role('link', name='Polls home').click()
        page.get_by_role('link', name='What would you like to build with Gramlot?').click()
        page.get_by_role('link', name='View results').click()
        expect(page.locator('#standard-result-1')).to_have_text('A dashboard: 2')
        assert not failures, failures
        browser.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True, help='Python executable in the target environment')
    parser.add_argument('--browser', action='store_true', help='Use Playwright from the runner environment')
    parser.add_argument('--demo', action='store_true', help='Verify the installed Polls CLI')
    args = parser.parse_args()
    python = str(Path(args.python).absolute())
    environment = os.environ.copy()
    for name in ('PYTHONPATH', 'PYTHONHOME', 'DJANGO_SETTINGS_MODULE'):
        environment.pop(name, None)
    # Only the target Python directory is needed to run Django; no Node/npm on PATH.
    environment['PATH'] = str(Path(python).parent)
    environment['PYTHONUNBUFFERED'] = '1'
    with tempfile.TemporaryDirectory(prefix='gramlot-consumer-') as directory:
        project = Path(directory) / 'project'
        if args.demo:
            project.mkdir()
        else:
            shutil.copytree(ROOT / 'examples/quickstart', project,
                            ignore=shutil.ignore_patterns('__pycache__', '*.sqlite3'))
        subprocess.run([python, '-I', '-m', 'pip', 'check'], cwd=project,
                       env=environment, check=True)
        result = subprocess.run([python, '-I', '-c', PROBE], cwd=project,
                                env=environment, check=True, capture_output=True, text=True)
        print(result.stdout.strip(), flush=True)
        if not args.demo:
            subprocess.run([python, 'manage.py', 'check'], cwd=project,
                           env=environment, check=True)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        url = f'http://127.0.0.1:{port}'
        command = [python, 'manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload']
        if args.demo:
            executable = Path(python).parent / ('gramlot-django.exe' if os.name == 'nt'
                                               else 'gramlot-django')
            command = [str(executable), 'demo', 'polls', '--port', str(port),
                       '--data-dir', str(Path(directory) / 'data')]
        with (Path(directory) / 'server.log').open('w+') as log:
            server = subprocess.Popen(
                command,
                cwd=project, env=environment, stdout=log, stderr=subprocess.STDOUT,
            )
            try:
                # Fresh CI runners can take longer to import Django and start.
                deadline = time.monotonic() + 90
                while True:
                    try:
                        with urlopen(url + ('/polls/' if args.demo else '/tools/ui/hello/'), timeout=1) as response:
                            assert response.status == 200
                        break
                    except (URLError, TimeoutError):
                        if server.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError('Django did not start')
                        time.sleep(0.1)
                if args.browser:
                    (check_polls_browser if args.demo else check_browser)(url)
                print(json.dumps({'project': 'passed', 'browser': args.browser, 'demo': args.demo}), flush=True)
            except BaseException:
                log.flush()
                log.seek(0)
                print(log.read(), flush=True)
                raise
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == '__main__':
    main()
