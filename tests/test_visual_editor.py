"""The editor writes only its configured file and never bypasses remote_edit."""
import asyncio
import pytest
from gramlot import GramlotBuilder
from gramlot_py_server.visual_editor import VisualEditorPageMixin

@pytest.fixture
def editor(tmp_path):
    path=tmp_path/'page.py'
    path.write_text("from gramlot import Page as BasePage\nclass Page(BasePage):\n    def main(self, root):\n        root.h2('Initial')\n")
    page=VisualEditorPageMixin()
    page.editor_source_files={'page':str(path)}
    return page,path

def test_host_gate_revision_syntax_and_saved_preview(editor):
    page,path=editor
    original=page.editor_document('page')
    assert original['writable'] is False
    changed=original['content'].replace('Initial','Updated')
    with pytest.raises(PermissionError): page.editor_document_save('page',changed,original['revision'])
    with pytest.raises(ValueError,match='Unknown'): page.editor_document('../page.py')
    page.remote_edit=True
    with pytest.raises(ValueError,match='syntax'): page.editor_document_save('page','class Broken:',original['revision'])
    assert path.read_text()==original['content']
    saved=page.editor_document_save('page',changed,original['revision'])
    with pytest.raises(ValueError,match='changed on disk'): page.editor_document_save('page',original['content'],original['revision'])
    builder=GramlotBuilder()
    asyncio.run(page.editor_document_preview(builder.root,'page',saved['revision'],'documentData'))
    assert builder.source.get_node('pageRoot.h2_0').value=='Updated'
    assert builder.source.get_node('pageRoot').attr['datapath']=='documentData'
    path.write_text(changed+'\n# External change')
    with pytest.raises(ValueError,match='changed'): asyncio.run(page.editor_document_preview(builder.root,'page',saved['revision'],'documentData'))

def test_preview_is_disabled_without_remote_edit(editor):
    page,path=editor
    document=page.editor_document('page')
    with pytest.raises(PermissionError): asyncio.run(page.editor_document_preview(GramlotBuilder().root,'page',document['revision'],'data'))
