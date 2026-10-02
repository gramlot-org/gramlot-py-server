# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Candidate overrides fail closed before any package installation."""
import importlib.util
from pathlib import Path
import sys

import pytest


@pytest.fixture
def candidate(monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'scripts' / 'install_core_candidate.py'
    spec = importlib.util.spec_from_file_location('candidate', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(sys, 'argv', [str(path)])
    monkeypatch.delenv('CORE_WHEEL_URL', raising=False)
    monkeypatch.delenv('CORE_WHEEL_SHA256', raising=False)
    return module


def test_no_override_uses_normal_resolution(candidate, monkeypatch):
    calls = []
    monkeypatch.setattr(candidate.subprocess, 'run', lambda *a, **kw: calls.append(a))
    candidate.main()
    assert calls == []


def test_candidate_filename_supplies_version_for_verification(candidate, monkeypatch):
    import json
    monkeypatch.setenv('CORE_WHEEL_URL', 'https://example.com/gramlot-0.1.5-py3-none-any.whl')
    monkeypatch.setenv('CORE_WHEEL_SHA256', 'a' * 64)
    calls = []
    monkeypatch.setattr(candidate.subprocess, 'run', lambda *a, **kw: calls.append((a, kw)))
    candidate.main()
    assert len(calls) == 2
    expected = json.loads(calls[1][1]['input'])
    assert expected['version'] == '0.1.5'
    assert expected['sha256'] == 'a' * 64


@pytest.mark.parametrize('url,digest', [
    ('https://example.com/core.whl', ''), ('', 'a' * 64),
    ('http://example.com/core.whl', 'a' * 64),
    ('https://example.com/core.whl#anything', 'a' * 64),
    ('https://example.com/core.tar.gz', 'a' * 64),
    ('https://example.com/core.whl', 'not-a-checksum'),
])
def test_invalid_override_never_installs(candidate, monkeypatch, url, digest):
    monkeypatch.setenv('CORE_WHEEL_URL', url)
    monkeypatch.setenv('CORE_WHEEL_SHA256', digest)
    calls = []
    monkeypatch.setattr(candidate.subprocess, 'run', lambda *a, **kw: calls.append(a))
    with pytest.raises(SystemExit, match='HTTPS wheel URL'):
        candidate.main()
    assert calls == []


def test_provenance_rejects_another_wheel(candidate, monkeypatch):
    import importlib.metadata
    import io
    import json
    class Distribution:
        version = '0.1.5'
        def read_text(self, name):
            return json.dumps({'url': 'https://example.com/wrong.whl',
                               'archive_info': {'hashes': {'sha256': 'a' * 64}}})
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: Distribution())
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps({
        'version': '0.1.5', 'url': 'https://example.com/core.whl', 'sha256': 'a' * 64,
    })))
    with pytest.raises(AssertionError, match='supplied candidate URL'):
        exec(candidate.VERIFY, {})


def test_consumer_probe_preserves_virtualenv_python_symlink(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'scripts' / 'verify_installation.py'
    spec = importlib.util.spec_from_file_location('consumer_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    python = tmp_path / 'venv-python'
    try:
        python.symlink_to(sys.executable)
    except OSError:
        pytest.skip('Creating symlinks is not available')
    monkeypatch.setattr(sys, 'argv', [str(path), '--python', str(python)])
    calls = []
    monkeypatch.setattr(module.subprocess, 'run', lambda args, **kw: calls.append(args))
    module.main()
    assert calls and all(args[0] == str(python) for args in calls)
