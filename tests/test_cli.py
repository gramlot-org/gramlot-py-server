"""The ``gramlot`` command: environments, ``new`` and the error of a missing extra."""
from importlib.metadata import EntryPoint

import pytest

from gramlot_py_server import cli
from gramlot_py_server.scaffold import TEMPLATES, project_files

ENVIRONMENTS = ["django", "fastapi", "flask", "kajenn", "uvicorn"]


def test_help_lists_the_five_environments(capsys):
    assert sorted(cli.environments()) == ENVIRONMENTS
    with pytest.raises(SystemExit) as raised:
        cli.main(["--help"])
    assert raised.value.code == 0
    assert "{django,fastapi,flask,kajenn,uvicorn}" in capsys.readouterr().out


def test_unknown_environment_and_missing_verb_are_usage_errors():
    for argv in (["rails", "new", "x"], [], ["uvicorn"]):
        with pytest.raises(SystemExit) as raised:
            cli.main(argv)
        assert raised.value.code == 2


def test_new_writes_the_templates(tmp_path):
    folder = tmp_path / "hello"
    assert cli.main(["uvicorn", "new", str(folder)]) == 0
    written = sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file())
    assert written == ["app.py", "pages/index.js", "pages/index.py", "requirements.txt"]
    for relative, template in project_files("uvicorn").items():
        assert (folder / relative).read_bytes() == template.read_bytes()


def test_every_environment_has_its_templates():
    for environment in ENVIRONMENTS:
        names = set(project_files(environment))
        assert {"requirements.txt", "pages/index.py", "pages/index.js"} <= names
        assert (TEMPLATES / environment / "requirements.txt").read_text().startswith(
            "gramlot-py-server[" + environment)


def test_new_refuses_a_folder_that_is_not_empty_or_a_file(tmp_path):
    (tmp_path / "used").mkdir()
    (tmp_path / "used" / "keep.txt").write_text("keep")
    (tmp_path / "file").write_text("file")
    for target in ("used", "file"):
        with pytest.raises(SystemExit) as raised:
            cli.main(["uvicorn", "new", str(tmp_path / target)])
        assert "exists and is not an empty folder" in str(raised.value)
    assert (tmp_path / "used" / "keep.txt").read_text() == "keep"
    empty = tmp_path / "empty"
    empty.mkdir()
    assert cli.main(["uvicorn", "new", str(empty)]) == 0


def test_an_environment_without_its_framework_names_the_extra():
    entry = EntryPoint(name="nothing", value="gramlot_py_server_absent:commands", group=cli.GROUP)
    with pytest.raises(SystemExit) as raised:
        cli.load_commands(entry)
    assert str(raised.value) == (
        "gramlot nothing: gramlot_py_server_absent is not installed. "
        'Install the extra: python -m pip install "gramlot-py-server[nothing]"'
    )
