"""Host filesystem endpoints for the reusable Gramlot filesystem tree and IDE."""
from pathlib import Path, PurePosixPath
import base64
import hashlib
import os
import stat
import tempfile
import threading

from genro_bag import Bag
from genro_tytx import from_tytx, to_tytx
from gramlot import endpoint, upload
from gramlot.server import UploadTarget

_WRITE_LOCK = threading.Lock()
_IMAGE_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
_LANGUAGES = {'.py':'python', '.js':'javascript', '.mjs':'javascript', '.ts':'typescript',
              '.json':'json', '.html':'html', '.css':'css', '.xml':'xml', '.md':'markdown',
              '.markdown':'markdown', '.sql':'sql', '.typ':'typst'}


class WorkspaceImageTarget(UploadTarget):
    """Write one image atomically into the selected workspace without replacement."""
    def __init__(self, root, name, max_bytes):
        super().__init__(max_bytes=max_bytes)
        self.root = root
        self.name = name
        self.file = tempfile.NamedTemporaryFile(dir=root, prefix='.gramlot-upload-', delete=False)
        self.temporary = Path(self.file.name)
        self.outcome = {'state': 'pending'}

    def write(self, chunk):
        self.file.write(chunk)

    def finish(self):
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
        try:
            os.link(self.temporary, self.root / self.name)
        except FileExistsError:
            self.outcome = {'state': 'unsaved'}
            raise ValueError('File already exists. Choose another image name.')
        finally:
            self.temporary.unlink(missing_ok=True)
        self.outcome = {'state': 'completed', 'result': {'root': str(self.root), 'path': self.name}}
        return self.outcome

    def abort(self):
        if self.outcome['state'] != 'completed':
            self.file.close()
            self.temporary.unlink(missing_ok=True)
            self.outcome = {'state': 'unsaved'}
        return self.outcome

    def status(self):
        return self.outcome


class FileSystemPageMixin:
    """Expose roots explicitly allowed by the host; writes are disabled by default."""
    filesystem_roots = ()
    filesystem_max_bytes = 2 * 1024 * 1024
    remote_edit = False

    def _root(self, root):
        if not isinstance(root, str) or not Path(root).is_absolute():
            raise ValueError('Choose an absolute directory path on the server')
        path = Path(root).resolve(strict=True)
        allowed = tuple(Path(item).resolve(strict=True) for item in self.filesystem_roots)
        if not path.is_dir() or not any(path.is_relative_to(item) for item in allowed):
            raise PermissionError('Directory is outside the configured filesystem roots')
        return path

    def _path(self, root, path, *, directory=False):
        base = self._root(root)
        if not isinstance(path, str) or '\\' in path:
            raise ValueError('Expected a relative POSIX path')
        relative = PurePosixPath(path)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Path must remain inside the workspace')
        current = base
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise PermissionError('Symbolic links are not exposed')
        if directory:
            if not current.is_dir():
                raise ValueError('Not a directory')
        elif not current.is_file():
            raise ValueError('Not a regular file')
        return current

    @upload
    def workspace_upload(self, metadata):
        if not self.remote_edit:
            raise PermissionError('Remote editing is disabled by the host')
        root = self._root(metadata['context']['root'])
        name = metadata['name']
        if not isinstance(name, str) or not name or name in {'.', '..'} or '/' in name or '\\' in name:
            raise ValueError('Expected an image file name')
        suffix = Path(name).suffix.lower()
        if suffix not in _IMAGE_TYPES or metadata['mediaType'].lower() != _IMAGE_TYPES[suffix]:
            raise ValueError('Choose a PNG, JPEG or WebP image')
        if (root / name).exists() or (root / name).is_symlink():
            raise ValueError('File already exists. Choose another image name.')
        return WorkspaceImageTarget(root, name, self.filesystem_max_bytes)

    @endpoint
    def workspace_open(self, root):
        root = str(self._root(root))
        return dict(root=root, entries=self.directory_tree(root), writable=bool(self.remote_edit))

    @endpoint
    def directory_tree(self, root, path=''):
        directory = self._path(root, path, directory=True)
        rows = []
        for child in directory.iterdir():
            if child.is_symlink():
                continue
            info = child.stat()
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                continue
            rows.append((child, info))
        rows.sort(key=lambda row: (not stat.S_ISDIR(row[1].st_mode), row[0].name.casefold(), row[0].name))
        result = Bag()
        for child, info in rows:
            result.set_item('n_' + child.name.encode('utf-8').hex(), None, _attributes=dict(
                path=(PurePosixPath(path) / child.name).as_posix(), caption=child.name,
                is_directory=stat.S_ISDIR(info.st_mode), size=info.st_size, modified=info.st_mtime))
        return result

    def _read(self, file):
        with file.open('rb') as stream:
            raw = stream.read(self.filesystem_max_bytes + 1)
        if len(raw) > self.filesystem_max_bytes or b'\0' in raw:
            raise ValueError('Only UTF-8 text documents up to 2 MiB are supported')
        return raw, raw.decode('utf-8')

    @endpoint
    def document_read(self, root, path):
        file = self._path(root, path)
        media_type = _IMAGE_TYPES.get(file.suffix.lower())
        if media_type:
            with file.open('rb') as stream:
                raw = stream.read(self.filesystem_max_bytes + 1)
            if len(raw) > self.filesystem_max_bytes:
                raise ValueError('Image exceeds the workspace size limit')
            relative = PurePosixPath(path)
            companion = relative.with_name(relative.stem + '_' + relative.suffix[1:] + '.ant.tytx')
            companion_file = file.with_name(companion.name)
            if companion_file.is_symlink():
                raise PermissionError('Symbolic links are not exposed')
            if companion_file.exists():
                companion_raw, content = self._read(self._path(root, companion.as_posix()))
                revision = hashlib.sha256(companion_raw).hexdigest()
            else:
                content = to_tytx(Bag())
                revision = None
            image = 'data:' + media_type + ';base64,' + base64.b64encode(raw).decode('ascii')
            return dict(path=path, content=from_tytx(content), revision=revision, writable=bool(self.remote_edit),
                        language='image', image=image, annotationPath=companion.as_posix())
        raw, content = self._read(file)
        return dict(path=path, content=content, revision=hashlib.sha256(raw).hexdigest(),
                    writable=bool(self.remote_edit), language=_LANGUAGES.get(file.suffix.lower(), 'text'))

    @endpoint
    def document_create(self, root, path, content):
        """Publish a new text file atomically without replacing an existing entry."""
        if not self.remote_edit:
            raise PermissionError('Remote editing is disabled by the host')
        if isinstance(path, str) and path.endswith('.ant.tytx') and isinstance(content, Bag):
            content = to_tytx(content)
        if not isinstance(content, str) or '\0' in content:
            raise ValueError('Expected UTF-8 text')
        raw = content.encode('utf-8')
        if len(raw) > self.filesystem_max_bytes:
            raise ValueError('Document is too large')
        if not isinstance(path, str) or not path or '\\' in path:
            raise ValueError('Expected a relative file name')
        relative = PurePosixPath(path)
        if relative.is_absolute() or '..' in relative.parts or not relative.name:
            raise ValueError('Path must remain inside the workspace')
        directory = self._path(root, str(relative.parent), directory=True)
        file = directory / relative.name
        if file.suffix.lower() == '.py':
            try:
                compile(content, str(file), 'exec')
            except SyntaxError as error:
                raise ValueError(f'Python syntax error at line {error.lineno}, column {error.offset}: {error.msg}') from error
        temporary = None
        with _WRITE_LOCK:
            try:
                with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
                    temporary = stream.name
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                # link is exclusive even if another process creates the destination meanwhile.
                os.link(temporary, file)
            except FileExistsError as error:
                raise ValueError('File already exists. Choose another name; your draft was retained.') from error
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        return dict(root=str(self._root(root)), path=relative.as_posix(),
                    revision=hashlib.sha256(raw).hexdigest())

    @endpoint
    def document_save(self, root, path, content, revision):
        if not self.remote_edit:
            raise PermissionError('Remote editing is disabled by the host')
        if isinstance(path, str) and path.endswith('.ant.tytx') and isinstance(content, Bag):
            content = to_tytx(content)
        if not isinstance(content, str) or '\0' in content:
            raise ValueError('Expected UTF-8 text')
        raw = content.encode('utf-8')
        if len(raw) > self.filesystem_max_bytes:
            raise ValueError('Document is too large')
        with _WRITE_LOCK:
            file = self._path(root, path)
            current, _ = self._read(file)
            if hashlib.sha256(current).hexdigest() != revision:
                raise ValueError('File changed on disk. Your draft was retained; reopen the file before saving.')
            if file.suffix.lower() == '.py':
                try:
                    compile(content, str(file), 'exec')
                except SyntaxError as error:
                    raise ValueError(f'Python syntax error at line {error.lineno}, column {error.offset}: {error.msg}') from error
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=file.parent, delete=False) as stream:
                    temporary = stream.name
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, stat.S_IMODE(file.stat().st_mode))
                os.replace(temporary, file)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        return dict(revision=hashlib.sha256(raw).hexdigest())
