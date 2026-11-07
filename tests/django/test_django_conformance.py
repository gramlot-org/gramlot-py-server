"""The server protocol GC-230 over HTTP, checked by the core on the running adapter."""
import pytest

from conformance_checks import CASE_IDS, CASES, check_adapter, check_revalidation


@pytest.mark.parametrize(("mount_path", "policy", "page_ttl"), CASES, ids=CASE_IDS)
def test_django_conforms_to_the_server_protocol(tmp_path, mount_path, policy, page_ttl):
    check_adapter("django", tmp_path, mount_path, policy, page_ttl)


@pytest.mark.parametrize("mount_path", ["", "/py"])
def test_django_revalidates_the_runtime_and_the_themes(tmp_path, mount_path):
    check_revalidation("django", tmp_path, mount_path)
