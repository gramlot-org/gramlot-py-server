"""Optional host file access for VisualEditor; never accepts arbitrary browser paths."""
from pathlib import Path
from types import ModuleType
import inspect
from gramlot import endpoint, source
from .filesystem import FileSystemPageMixin


class VisualEditorPageMixin:
    editor_source_files = {}
    remote_edit = False

    def _editor_file(self, key):
        if key not in self.editor_source_files:
            raise ValueError("Unknown editor document")
        file = Path(self.editor_source_files[key]).resolve(strict=True)
        if file.suffix != '.py':
            raise ValueError("Expected a Python page")
        service = FileSystemPageMixin()
        service.filesystem_roots = (str(file.parent),)
        service.remote_edit = self.remote_edit
        return service, file

    def editor_document(self, key):
        service, file = self._editor_file(key)
        return dict(service.document_read(str(file.parent), file.name), key=key, language='python')

    @endpoint
    def editor_document_save(self, key, content, revision):
        service, file = self._editor_file(key)
        return service.document_save(str(file.parent), file.name, content, revision)

    @source
    async def editor_document_preview(self, root, key, revision, data_root):
        service, file = self._editor_file(key)
        if not self.remote_edit:
            raise PermissionError("Remote editing is disabled by the host")
        document = service.document_read(str(file.parent), file.name)
        if document['revision'] != revision:
            raise ValueError("Saved Python changed; reopen the document before previewing")
        module = ModuleType('gramlot_editor_preview')
        module.__file__ = str(file)
        exec(compile(document['content'], str(file), 'exec'), module.__dict__)
        page = module.Page()
        result = page.main(root.div(node_label='pageRoot', datapath=data_root))
        if inspect.isawaitable(result):
            await result
