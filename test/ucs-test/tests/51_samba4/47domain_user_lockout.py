#!/usr/share/ucs-test/runner python3
## desc: Test if a domain user account is locked out and freed.
## exposure: dangerous
## packages: [univention-samba4, univention-s4-connector]
## bugs: [35898]
## roles:
## - domaincontroller_master
## - domaincontroller_backup
## - domaincontroller_slave

import subprocess
import sys
from datetime import datetime, timedelta
from time import sleep
from typing import Iterator, List, Sequence, Tuple, Union  # noqa: F401

from univention.config_registry import ucr
from univention.testing import utils
from univention.testing.codes import TestCodes
from univention.testing.strings import random_username


LOCKOUT_DURATION = 1  # duration of lockout in minutes
LOCKOUT_THRESHOLD = 3  # amount of auth. attempts allowed before the lock out
TEST_USER_PASS = 'Univention1'

admin_username = ucr['tests/domainadmin/account'].split(",")[0][len("uid="):]
admin_password = ucr['tests/domainadmin/pwd']
hostname = ucr['ldap/server/name']
test_username = 'ucs_test_samba4_user_' + random_username(4)


def remove_samba_warnings(input_str: str) -> str:
    """Remove the Samba Warning/Note from the given input_str."""
    # ignoring following messages (Bug #37362):
    input_str = input_str.replace('WARNING: No path in service IPC$ - making it unavailable!', '')
    return input_str.replace('NOTE: Service IPC$ is flagged unavailable.', '').strip()


def create_and_run_process(cmd: Sequence[str]) -> Tuple[str, str]:
    """
    Create a process as a Popen instance with a given 'cmd'
    and 'communicates' with it. Returns (stdout, stderr).
    """
    proc = subprocess.run(cmd, capture_output=True, check=False, encoding="UTF-8")
    return remove_samba_warnings(proc.stdout), remove_samba_warnings(proc.stderr)


def try_to_authenticate(password: str) -> Tuple[str, str]:
    """
    Authenticate 'test_username' user with given 'password'
    using smbclient and execute an 'ls'. Returns (stdout, stderr).
    """
    print(f"## Authenticating user '{test_username}' with password '{password}'")

    cmd = (
        "smbclient", f"//{hostname}/{test_username}",
        "-U", f"{test_username}%{password}",
        "--use-kerberos=required",
        "-t", "20",  # 20 seconds timeout per operation.
        "-c", "ls",
        "--debuglevel=1",
    )
    try:
        return create_and_run_process(cmd)
    finally:
        dump_account()


def set_lockout_settings(lock_duration: Union[int, str], lock_threshold: Union[int, str]) -> None:
    """Set the lockout settings to given values."""
    print(f"# Setting account lockout settings: duration={lock_duration}m; threshold={lock_threshold}")

    cmd = (
        "samba-tool", "domain", "passwordsettings", "set",
        "--account-lockout-duration", str(lock_duration),
        "--account-lockout-threshold", str(lock_threshold),
        "-U", f"{admin_username}%{admin_password}",
        "--debuglevel=1",
    )

    out, err = create_and_run_process(cmd)
    if err:
        utils.fail(f"An error/warning occurred while (re)setting account lockout settings via '{' '.join(cmd)}':\n{err!r}")
    if out:
        print(out)


def create_delete_test_user(should_exist: bool) -> None:
    """
    Create or delete the 'test_username' depending on the given argument
    via 'samba-tool'. User password is TEST_USER_PASS.
    """
    if should_exist:
        print(f"# Creating test user '{test_username}'")
        cmd = ["samba-tool", "user", 'create', test_username, TEST_USER_PASS]
    else:
        print(f"# Deleting test user '{test_username}'")
        cmd = ["samba-tool", "user", 'delete', test_username]

    cmd += ["-U", f"{admin_username}%{admin_password}", "--debuglevel=1"]

    out, err = create_and_run_process(cmd)
    if err:
        utils.fail(f"An error/warning occurred while creating or removing user '{test_username}' via command {' '.join(cmd)}'.\nSTDERR: '{err}'")
    if out:
        print(out)


def check_no_errors_present_in_output(stdout: str, stderr: str) -> None:
    """
    Fail the test if there are signs of errors found in the given
    'stdout' or 'stderr'.
    """
    complete_output = stdout + stderr

    if 'NT_STATUS_ACCOUNT_LOCKED_OUT' in complete_output:
        utils.fail(f"The 'NT_STATUS_ACCOUNT_LOCKED_OUT' error was found in the output.\nSTDOUT: '{stdout}'. STDERR: '{stderr}'.")

    elif 'NT_STATUS_LOGON_FAILURE' in complete_output:
        utils.fail(f"The 'NT_STATUS_LOGON_FAILURE' error was found in the output.\nSTDOUT: '{stdout}'. STDERR: '{stderr}'.")

    elif 'NT_STATUS_OK' in complete_output:
        # the (only one possible) success status was found
        # (http://msdn.microsoft.com/en-us/library/ee441884.aspx)
        return

    elif 'NT_STATUS_' in complete_output:
        # all the rest status options are signs of errors
        utils.fail(f"An error occurred. \nSTDOUT: '{stdout}'. STDERR: '{stderr}'")


def check_error_present_in_output(stdout: str, stderr: str) -> None:
    """
    Fail the test if there is no 'NT_STATUS_ACCOUNT_LOCKED_OUT' error in
    the given stdout or stderr.
    """
    if 'NT_STATUS_ACCOUNT_LOCKED_OUT' not in (stdout + stderr):
        utils.fail(f"The 'NT_STATUS_ACCOUNT_LOCKED_OUT' error could not be found in the STDOUT: '{stdout}' or STDERR: '{stderr}'. The account lockout may not work.")


def dump_account() -> None:
    """
    Dump current account seettings.

    lastLogonTimestamp: This is the time that the user last logged into the domain (global).
    lastLogon: This is the time that the user last logged into the domain (local).
    badPasswordTime: The last time and date that an attempt to log on to this account was made with a password that is not valid.
    lockoutTime: Das Datum und die Uhrzeit (UTC), zu dem dieses Konto gesperrt wurde.
    logonCount: Gibt an, wie oft sich das Konto erfolgreich angemeldet hat.
    badPwdCount: The number of times the user tried to log on to the account using an incorrect password.
    """
    out, _err = create_and_run_process(["samba-tool", "user", "show", test_username])
    vals = dict(
        line.split(": ")
        for line in out.splitlines()
        if line
    )
    print(f"  {'now':20}\t{datetime.utcnow()}Z")
    for key in ("badPasswordTime", "lockoutTime"):  # "lastLogonTimestamp", "lastLogon"
        try:
            val = vals[key]  # 100ns since ANSI/MS Epoch
            dt = datetime(1601, 1, 1) + timedelta(microseconds=int(val) / 10)
            print(f"  {key:20}\t{dt}Z")
        except (LookupError, ValueError):
            continue
    for key in ("logonCount", "badPwdCount"):
        try:
            val = vals[key]
            print(f"  {key:20}\t{val}")
        except LookupError:
            continue


def dump_pwpolicy() -> Iterator[str]:
    """Dump the current password policy settings."""
    out, _err = create_and_run_process(["samba-tool", "domain", "passwordsettings", "show"])
    for line in out.splitlines():
        if " lockout " in line:
            yield line


def main() -> None:
    if not all((admin_username, admin_password, hostname)):
        print("SKIP: Missing Administrator credentials or a hostname from UCR.")
        sys.exit(TestCodes.REASON_INSTALL)

    try:
        create_delete_test_user(True)

        set_lockout_settings(LOCKOUT_DURATION, LOCKOUT_THRESHOLD)
        hist = []  # type: List[str]
        hist += dump_pwpolicy()

        print("# Twiddling thumbs for 30s")  # Why?
        sleep(30)

        print(f"# Authenticating user '{test_username}' with correct password '{TEST_USER_PASS}'")
        hist += dump_pwpolicy()
        stdout, stderr = try_to_authenticate(TEST_USER_PASS)
        check_no_errors_present_in_output(stdout, stderr)
        print("# OKAY: login worked")

        print(f"# Locking out user '{test_username}' by authenticating with wrong password {LOCKOUT_THRESHOLD + 1} times:")
        for attempt in range(LOCKOUT_THRESHOLD + 1):
            hist += dump_pwpolicy()
            stdout, stderr = try_to_authenticate(f"{attempt}{TEST_USER_PASS}")
        check_error_present_in_output(stdout, stderr)
        print("# OKAY: account should be locked now")

        print(f"# Authenticating user '{test_username}' with correct password '{TEST_USER_PASS}' on locked out account:")
        hist += dump_pwpolicy()
        stdout, stderr = try_to_authenticate(TEST_USER_PASS)
        check_error_present_in_output(stdout, stderr)
        print("# OKAY: login failed for locked account")

        for delay in (LOCKOUT_DURATION * 60, 10, 20, 30):
            print(f"# Waiting for user account '{test_username}' to be unlocked after the lock out timeout ({delay}s) expires:")
            sleep(delay)

            print(f"# Authenticating user '{test_username}' with correct password '{TEST_USER_PASS}' after the lock time has expired")
            hist += dump_pwpolicy()
            stdout, stderr = try_to_authenticate(TEST_USER_PASS)
            if "NT_STATUS_ACCOUNT_LOCKED_OUT" not in stdout:
                break
        else:
            print("\n".join(hist))
            # breakpoint()

        check_no_errors_present_in_output(stdout, stderr)
        print("# OKAY: login succeeded for unlocked account")
    finally:
        set_lockout_settings('default', 'default')

        create_delete_test_user(False)


if __name__ == '__main__':
    with utils.FollowLogfile(["/var/log/samba/log.samba"]):
        main()
