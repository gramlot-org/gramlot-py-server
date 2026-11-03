"""Opt-in editing of catalogued gallery source files."""
from gramlot import endpoint
from gramlot_py_server.filesystem import FileSystemPageMixin


class GallerySourceEditing:
    remote_edit = False

    def _gallery_source(self, key):
        item = self.gallery_item(key)
        if 'children' in item:
            raise ValueError('Expected a gallery lesson')
        path = item['path'] / f"{item['folder']}.py"
        service = FileSystemPageMixin()
        service.filesystem_roots = (str(path.parent),)
        service.remote_edit = self.remote_edit
        return service, str(path.parent), path.name

    def source_document(self, key):
        if not self.remote_edit:
            return super().source_document(key)
        service, root, name = self._gallery_source(key)
        return service.document_read(root, name)

    @endpoint
    def gallery_source_save(self, key, content, revision):
        if not self.remote_edit:
            raise PermissionError('Remote editing is disabled by the host')
        service, root, name = self._gallery_source(key)
        return service.document_save(root, name, content, revision)
