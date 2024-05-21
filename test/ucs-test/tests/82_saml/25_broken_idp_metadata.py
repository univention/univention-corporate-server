#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check that the umc server does not stop if the idp metadata is not available.
## tags: [saml]
## bugs: [39355]
## join: true
## exposure: dangerous

from __future__ import annotations

import os
import subprocess
import time
from types import TracebackType

import pytest

import samltest


def restart_umc() -> None:
    subprocess.check_call(["systemctl", "restart", "univention-management-console-server"])
    time.sleep(3)  # Wait for the umc to be ready to answer requests.


class move_idp_metadata:

    metadata_dir = "/usr/share/univention-management-console/saml/idp/"

    def __enter__(self) -> None:
        for metadata_file in os.listdir(self.metadata_dir):
            metadata_file_fullpath = self.metadata_dir + metadata_file
            os.rename(metadata_file_fullpath, metadata_file_fullpath + '.backup')
        restart_umc()

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        for metadata_file in os.listdir(self.metadata_dir):
            metadata_file_fullpath = self.metadata_dir + metadata_file
            os.rename(metadata_file_fullpath, metadata_file_fullpath.replace('.backup', ''))
        restart_umc()


@pytest.fixture(autouse=True)
def cleanup():
    yield
    restart_umc()


def test_broken_idp_metadata(saml_session) -> None:
    with move_idp_metadata():
        with pytest.raises(samltest.SamlError) as exc:
            saml_session.login_with_new_session_at_IdP()
        expected_error = "There is a configuration error in the service provider: No identity provider are set up for use."
        assert expected_error in str(exc.value)

    saml_session.login_with_new_session_at_IdP()
    saml_session.test_logged_in_status()
    saml_session.logout_at_IdP()
    saml_session.test_logout_at_IdP()
    saml_session.test_logout()
