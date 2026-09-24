# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""A registry/source install must not masquerade as a supplied CI candidate."""
import os
from pathlib import Path
import subprocess
import sys


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/install_core_candidate.py'


def test_verify_rejects_a_different_installed_core_origin():
    env = {**os.environ, 'CORE_WHEEL_URL': 'https://example.invalid/gramlot-0.1.5-py3-none-any.whl',
           'CORE_WHEEL_SHA256': 'a' * 64}
    result = subprocess.run([sys.executable, str(SCRIPT), '--verify'], env=env,
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert 'candidate' in result.stderr


def test_empty_candidate_configuration_uses_normal_package_resolution():
    env = {**os.environ, 'CORE_WHEEL_URL': '', 'CORE_WHEEL_SHA256': ''}
    subprocess.run([sys.executable, str(SCRIPT), '--verify'], env=env, check=True)
