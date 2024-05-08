#!/usr/share/ucs-test/runner pytest-3 -s --tb=native
## desc: "Find traceback in /var/log/univention/ logfiles"
## exposure: safe
## tags: [apptest]

import argparse
import glob
import os
import shlex
import subprocess
import tempfile

import psutil
import pytest

import univention.testing.utils

import grep_traceback


@pytest.mark.exposure('safe')
def test_ucs_test_logfile():
    """Find traceback in ucs-test logfile"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--logfile')

    ucs_test = psutil.Process(os.getppid())
    args = parser.parse_known_args(ucs_test.cmdline())[0]

    if not args.logfile:
        for pfile in ucs_test.open_files():
            if pfile.path.startswith('/var/log/univention/test') and pfile.path.endswith('.log'):
                args.logfile = pfile.path
                break
    else:
        args.logfile = os.path.join(ucs_test.cwd(), args.logfile)

    if args.logfile and os.path.isfile(args.logfile):
        grep_traceback.main([args.logfile], ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)


@pytest.mark.exposure('safe')
def test_var_log_tracebacks():
    grep_traceback.main(glob.glob('/var/log/univention/*.log'), ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)


@pytest.mark.exposure('safe')
def test_var_log_subdirectory_tracebacks():
    grep_traceback.main(glob.glob('/var/log/univention/*/*.log'), ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)


@pytest.mark.exposure('safe')
def test_var_log_tracebacks_gz():
    grep_traceback.main(glob.glob('/var/log/univention/*.log.*.gz'), ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)


@pytest.mark.exposure('safe')
def test_journallog_tracebacks():
    proc = subprocess.Popen(['journalctl', '-o', 'cat'], stdout=subprocess.PIPE)
    grep_traceback.main([proc.stdout], ignore_exceptions=grep_traceback.COMMON_EXCEPTIONS)
    proc.wait()


@pytest.mark.roles_not('domaincontroller_master')
@pytest.mark.exposure('dangerous')
# @pytest.mark.parametrize('testcase', [
#     'test_var_log_tracebacks',
#     'test_var_log_tracebacks_gz',
# ])  # FIXME: skip test_ucs_test_logfile
def test_fetch_logfiles_on_dc_master(ucr, testcase=None):
    """Find traceback on the DC Master"""
    password = univention.testing.utils.UCSTestDomainAdminCredentials().bindpw
    TESTPATH = '/usr/share/ucs-test/99_end/01_var_log_tracebacks.py'
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(password.encode('UTF-8'))
        fd.flush()

        def ssh(cmd: str) -> None:
            subprocess.run(
                ['univention-ssh', '--no-split', fd.name, f"root@{ucr['ldap/master']}", cmd],
                capture_output=True,
                check=True,
            )

        ssh(f'[ -e {shlex.quote(TESTPATH)} ] || exec univention-install -q -y ucs-test-end')
        ssh(f'exec {TESTPATH} -i -f')
        # TODO: detect skipped exit code
