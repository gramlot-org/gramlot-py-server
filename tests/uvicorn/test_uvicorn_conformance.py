"""The server protocol GC-230 over HTTP, checked by the core on the running adapter."""
import pytest

from conformance_checks import CASE_IDS, CASES, check_adapter


@pytest.mark.parametrize(("mount_path", "policy"), CASES, ids=CASE_IDS)
def test_uvicorn_conforms_to_the_server_protocol(tmp_path, mount_path, policy):
    check_adapter("uvicorn", tmp_path, mount_path, policy)
