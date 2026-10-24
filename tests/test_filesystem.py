"""Contract checks shared by every adapter's filesystem endpoint consumer."""
import pytest
from gramlot_py_server.filesystem import FileSystemPageMixin


@pytest.fixture
def workspace(tmp_path):
    page = FileSystemPageMixin()
    page.filesystem_roots = (str(tmp_path),)
    return page, tmp_path


def test_lazy_listing_and_text(workspace):
    page, root = workspace
    (root / 'nested').mkdir()
    (root / 'nested' / 'hidden.txt').write_text('not in root listing')
    (root / 'a,b:c.py').write_text('print(42)\n')
    result = page.workspace_open(str(root))
    nodes = result['entries'].get_nodes()
    assert [n.attr['caption'] for n in nodes] == ['nested', 'a,b:c.py']
    assert nodes[0].value is None
    doc = page.document_read(str(root), 'a,b:c.py')
    assert doc['language'] == 'python'
    assert not doc['writable']
    with pytest.raises(PermissionError):
        page.document_save(str(root), 'a,b:c.py', 'print(43)', doc['revision'])


def test_save_validation_conflict_and_atomic_write(workspace):
    page, root = workspace
    page.remote_edit = True
    file = root / 'code.py'
    file.write_text('value = 1\n')
    doc = page.document_read(str(root), 'code.py')
    with pytest.raises(ValueError, match='Python syntax error'):
        page.document_save(str(root), 'code.py', 'def broken(', doc['revision'])
    assert file.read_text() == 'value = 1\n'
    saved = page.document_save(str(root), 'code.py', 'value = 2\n', doc['revision'])
    assert saved['revision'] != doc['revision']
    assert file.read_text() == 'value = 2\n'
    with pytest.raises(ValueError, match='changed on disk'):
        page.document_save(str(root), 'code.py', 'value = 3\n', doc['revision'])
    assert file.read_text() == 'value = 2\n'
    assert list(root.iterdir()) == [file]


def test_boundaries_symlinks_binary_and_size(workspace, tmp_path_factory):
    page, root = workspace
    outside = tmp_path_factory.mktemp('outside')
    (outside / 'secret').write_text('outside')
    (root / 'link').symlink_to(outside, target_is_directory=True)
    with pytest.raises(PermissionError):
        page.workspace_open(str(outside))
    with pytest.raises(ValueError):
        page.document_read(str(root), '../outside/secret')
    with pytest.raises(PermissionError):
        page.document_read(str(root), 'link/secret')
    assert len(page.directory_tree(str(root))) == 0
    (root / 'binary').write_bytes(b'\0binary')
    with pytest.raises(ValueError):
        page.document_read(str(root), 'binary')
    (root / 'large').write_bytes(b'x' * (page.filesystem_max_bytes + 1))
    with pytest.raises(ValueError):
        page.document_read(str(root), 'large')


def test_typst_document_keeps_source_and_host_write_gate(workspace):
    page, root = workspace
    file = root / 'report.typ'
    file.write_text('= Report\n')
    doc = page.document_read(str(root), 'report.typ')
    assert doc['language'] == 'typst'
    with pytest.raises(PermissionError):
        page.document_save(str(root), 'report.typ', '= Updated\n', doc['revision'])
    page.remote_edit = True
    page.document_save(str(root), 'report.typ', '= Updated\n', doc['revision'])
    assert file.read_text() == '= Updated\n'


def test_create_without_overwrite_and_syntax_validation(workspace):
    page, root = workspace
    with pytest.raises(PermissionError):
        page.document_create(str(root), 'new.py', '')
    page.remote_edit = True
    with pytest.raises(ValueError, match='Python syntax error'):
        page.document_create(str(root), 'new.py', 'def broken(')
    assert not (root / 'new.py').exists()
    result = page.document_create(str(root), 'new.py', 'value = 1\n')
    assert page.document_read(str(root), 'new.py')['revision'] == result['revision']
    with pytest.raises(ValueError, match='already exists'):
        page.document_create(str(root), 'new.py', 'value = 2\n')
    assert (root / 'new.py').read_text() == 'value = 1\n'
    page.document_create(str(root), 'empty.typ', '')
    assert (root / 'empty.typ').read_bytes() == b''
    assert sorted(p.name for p in root.iterdir()) == ['empty.typ', 'new.py']


def test_create_rejects_traversal_symlinks_and_missing_parent(workspace):
    page, root = workspace
    page.remote_edit = True
    (root / 'nested').mkdir()
    (root / 'link').symlink_to(root / 'nested', target_is_directory=True)
    for path in ('../escape.txt', '/absolute.txt', '', 'missing/new.txt'):
        with pytest.raises(ValueError):
            page.document_create(str(root), path, 'draft')
    with pytest.raises(PermissionError):
        page.document_create(str(root), 'link/new.txt', 'draft')
    (root / 'occupied').symlink_to(root / 'absent')
    with pytest.raises(ValueError, match='already exists'):
        page.document_create(str(root), 'occupied', 'draft')
    with pytest.raises(ValueError):
        page.document_create(str(root), 'binary.txt', '\0')
    with pytest.raises(ValueError):
        page.document_create(str(root), 'big.txt', 'x' * (page.filesystem_max_bytes + 1))
    page.document_create(str(root), 'nested/new.md', '# New')
    assert (root / 'nested/new.md').read_text() == '# New'
