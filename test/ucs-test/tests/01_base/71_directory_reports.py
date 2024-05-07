#!/usr/share/ucs-test/runner pytest-3 -vv
## exposure: careful
## desc: check if directory reports can be generated
## packages: [univention-directory-reports, univention-management-console-module-udm]

from __future__ import annotations

from pathlib import Path
from subprocess import check_call
from urllib.parse import parse_qs, urlparse

import pytest

from univention.config_registry import ucr
from univention.testing.umc import Client


CASES = (
    ('users/user', '%(tests/domainadmin/account)s'),
    ('computers/computer', '%(ldap/hostdn)s'),
    ('groups/group', 'cn=Backup Join,cn=groups,%(ldap/base)s'),
)
TYPES = (
    "PDF Document",
    "CSV Report",
)

PATH = Path("/usr/share/univention-management-console-module-udm")


@pytest.fixture(scope="module")
def client():
    return Client.get_test_connection()


def test_users_user(client):
    r = client.umc_command('udm/reports/query', {}, 'users/user')
    assert r.status == 200


@pytest.mark.parametrize("report_type", TYPES)
@pytest.mark.parametrize("module,obj", CASES)
def test_umc(report_type: str, module: str, obj: str, client) -> None:
    r = client.umc_command('udm/reports/create', {"report": report_type, "objects": [obj % ucr]}, module)
    assert r.status == 200

    url = r.result.get('URL')
    u = urlparse(url)
    query = parse_qs(u.query)
    report, = query["report"]
    fname = PATH / report
    assert fname.is_file()

    try:
        r = client.umc_command('udm/reports/get', {"report": report}, print_response=False)
        assert r.status == 200
        assert r.data
        if report_type == 'PDF Document':
            assert b'ReportLab Generated PDF document' in r.data
            assert report.endswith('.pdf')
        elif report_type == 'CSV Report':
            assert report.endswith('.csv')
    finally:
        fname.unlink()


@pytest.mark.parametrize("report_type", TYPES)
@pytest.mark.parametrize("module,obj", CASES)
def test_cmdline(report_type: str, module: str, obj: str, tmp_path) -> None:
    report = tmp_path / "report"
    check_call(['univention-directory-reports', '-m', module, '-r', report_type, '--output-dir', report.parent.as_posix(), '--output-name', report.name, obj % ucr])
    assert report.is_file()


def test_cmd_list() -> None:
    check_call(['univention-directory-reports', '-l'])


def test_cleanup() -> None:
    check_call(['univention-directory-reports-cleanup'])
