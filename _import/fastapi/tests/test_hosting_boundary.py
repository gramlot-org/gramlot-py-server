# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Keep the extracted adapter on the supported core contract."""
import ast
from pathlib import Path

import gramlot_fastapi


def test_adapter_uses_public_hosting_contract():
    violations = []
    for path in Path(gramlot_fastapi.__file__).parent.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or '').startswith(
                    'gramlot.contrib._shared'):
                violations.append(f'{path.name}:{node.lineno}: {node.module}')
            if isinstance(node, ast.Attribute) and node.attr in (
                    '_invoke', '_registered_methods', 'page_methods', 'page_classes'):
                violations.append(f'{path.name}:{node.lineno}: {node.attr}')
    assert not violations, '\n'.join(violations)
