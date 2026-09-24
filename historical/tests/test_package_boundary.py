# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Keep the released adapter on supported core extension points."""
import ast
from pathlib import Path

import gramlot_django


def test_adapter_uses_supported_hosting_contract():
    root = Path(gramlot_django.__file__).parent
    violations = []
    for path in root.glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or '').startswith(
                    'gramlot.contrib._shared'):
                violations.append(f'{path.name}:{node.lineno}: {node.module}')
            if isinstance(node, ast.Attribute) and node.attr in (
                    '_invoke', '_registered_methods', 'page_methods', 'page_classes',
                    'browser_manifest', 'package_directory', 'frontend_directory'):
                violations.append(f'{path.name}:{node.lineno}: {node.attr}')
    assert not violations, '\n'.join(violations)
