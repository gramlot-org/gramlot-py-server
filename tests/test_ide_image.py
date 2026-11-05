import base64
import pytest
from genro_bag import Bag
from genro_tytx import from_tytx, to_tytx
from gramlot_py_server.filesystem import FileSystemPageMixin


def test_image_companion_create_update_and_conflict(tmp_path):
    page=FileSystemPageMixin();page.filesystem_roots=(str(tmp_path),);page.remote_edit=True
    image=tmp_path/'radiografia.png';image.write_bytes(b'\x89PNG\r\n\x1a\nimage bytes')
    original=image.read_bytes();root=str(tmp_path)
    opened=page.document_read(root,'radiografia.png')
    assert opened['language']=='image' and opened['annotationPath']=='radiografia_png.ant.tytx'
    assert base64.b64decode(opened['image'].split(',',1)[1])==original
    assert isinstance(opened['content'],Bag) and opened['revision'] is None
    bag=Bag();bag.set_item('a',Bag({'type':'text','text':'Test'}));content=to_tytx(bag)
    created=page.document_create(root,opened['annotationPath'],bag)
    restored=page.document_read(root,'radiografia.png')
    assert restored['content'].get_item('a.text')=='Test'
    assert restored['revision']==created['revision']
    bag.set_item('a.text','Changed');page.document_save(root,opened['annotationPath'],bag,created['revision'])
    with pytest.raises(ValueError,match='changed on disk'):
        page.document_save(root,opened['annotationPath'],content,created['revision'])
    assert image.read_bytes()==original
    (tmp_path/'radiografia.jpg').write_bytes(b'jpeg')
    assert page.document_read(root,'radiografia.jpg')['annotationPath']=='radiografia_jpg.ant.tytx'
    page.remote_edit=False
    with pytest.raises(PermissionError):page.document_save(root,opened['annotationPath'],content,created['revision'])


def test_companion_symlink_is_rejected(tmp_path):
    page=FileSystemPageMixin();page.filesystem_roots=(str(tmp_path),)
    (tmp_path/'a.png').write_bytes(b'png')
    (tmp_path/'a_png.ant.tytx').symlink_to(tmp_path/'missing')
    with pytest.raises(PermissionError):page.document_read(str(tmp_path),'a.png')


def test_upload_original_image_to_open_workspace_without_overwrite(tmp_path):
    page=FileSystemPageMixin();page.filesystem_roots=(str(tmp_path),)
    metadata={'name':'photo.png','mediaType':'image/png','context':{'root':str(tmp_path)},'fields':{}}
    with pytest.raises(PermissionError):page.workspace_upload(metadata)
    page.remote_edit=True
    target=page.workspace_upload(metadata);target.write(b'original bytes')
    result=target.finish();assert result=={'state':'completed','result':{'root':str(tmp_path),'path':'photo.png'}}
    assert (tmp_path/'photo.png').read_bytes()==b'original bytes'
    with pytest.raises(ValueError,match='already exists'):page.workspace_upload(metadata)
    assert target.abort()==result and (tmp_path/'photo.png').read_bytes()==b'original bytes'
    metadata['name']='../outside.png'
    with pytest.raises(ValueError):page.workspace_upload(metadata)
    metadata['name']='other.png';metadata['mediaType']='text/plain'
    with pytest.raises(ValueError):page.workspace_upload(metadata)
    metadata['mediaType']='image/png';target=page.workspace_upload(metadata);target.write(b'temp')
    assert target.abort()=={'state':'unsaved'} and not (tmp_path/'other.png').exists()
    assert not list(tmp_path.glob('.gramlot-upload-*'))
