# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""Common functions used by tests."""

from __future__ import annotations

import functools
import logging
import os
import socket
import subprocess
import sys
import time
import traceback
from enum import IntEnum
from itertools import chain
from types import TracebackType
from typing import IO, Any, Callable, Dict, Iterable, List, Mapping, NoReturn, Sequence, Text, Tuple, Type, TypeVar

import ldap

from univention import uldap
from univention.config_registry import ConfigRegistry


logger = logging.getLogger('test')

try:
    from univention.admin.uldap import access
except ImportError:
    access = None

S4CONNECTOR_INIT_SCRIPT = '/etc/init.d/univention-s4-connector'
FIREWALL_INIT_SCRIPT = '/etc/init.d/univention-firewall'
SLAPD_INIT_SCRIPT = '/etc/init.d/slapd'

UCR = ConfigRegistry()


_T = TypeVar("_T")  # noqa: PYI018


class LDAPError(Exception):
    pass


class LDAPReplicationFailed(LDAPError):
    pass


class LDAPObjectNotFound(LDAPError):
    pass


class LDAPUnexpectedObjectFound(LDAPError):
    pass


class LDAPObjectValueMissing(LDAPError):
    pass


class LDAPObjectUnexpectedValue(LDAPError):
    pass


class UCSTestDomainAdminCredentials:
    """
    This class fetches the username, the LDAP bind DN and the password
    for a domain admin user account from UCR. The account may be used for testing.

    >>> dummy_ucr = {'ldap/base': 'dc=example,dc=com', 'tests/domainadmin/pwdfile': '/dev/null'}
    >>> account = UCSTestDomainAdminCredentials(ucr=dummy_ucr)
    >>> account.username
    'Administrator'
    >>> account.binddn
    'uid=Administrator,cn=users,dc=example,dc=com'
    >>> account.bindpw
    ''
    """

    def __init__(self, ucr: ConfigRegistry | None = None) -> None:
        if ucr is None:
            ucr = UCR
            ucr.load()
        self.binddn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%(ldap/base)s' % ucr)
        self.pwdfile = ucr.get('tests/domainadmin/pwdfile')
        if self.pwdfile:
            with open(self.pwdfile) as f:
                self.bindpw = f.read().strip('\n\r')
        else:
            self.bindpw = ucr.get('tests/domainadmin/pwd', 'univention')
        if self.binddn:
            self.username: Text | None = uldap.explodeDn(self.binddn, 1)[0]
        else:
            self.username = None


def get_ldap_connection(admin_uldap: bool = False, primary: bool = False) -> access:
    ucr = UCR
    ucr.load()

    if primary:
        port = int(ucr.get('ldap/master/port', 7389))
        ldap_servers = [ucr['ldap/master']]
    else:
        port = int(ucr.get('ldap/server/port', 7389))
        ldap_servers = []
        if ucr['ldap/server/name']:
            ldap_servers.append(ucr['ldap/server/name'])
        if ucr['ldap/servers/addition']:
            ldap_servers.extend(ucr['ldap/server/addition'].split())

    creds = UCSTestDomainAdminCredentials()

    for ldap_server in ldap_servers:
        try:
            lo = uldap.access(host=ldap_server, port=port, base=ucr['ldap/base'], binddn=creds.binddn, bindpw=creds.bindpw, start_tls=2, decode_ignorelist=[], follow_referral=True)
            if admin_uldap:
                lo = access(lo=lo)
            return lo
        except ldap.SERVER_DOWN:
            pass
    raise ldap.SERVER_DOWN()


def retry_on_error(func: Callable[..., _T], exceptions: Tuple[Type[Exception], ...] = (Exception,), retry_count: int = 20, delay: float = 10) -> _T:
    """
    This function calls the given function `func`.
    If one of the specified `exceptions` is caught, `func` is called again until
    the retry count is reached or any unspecified exception is caught. Between
    two calls of `func` retry_on_error waits for `delay` seconds.

    :param func: function to be called
    :param exceptions: tuple of exception classes, that cause a rerun of `func`
    :param retry_count: retry the execution of `func` max `retry_count` times
    :param delay: waiting time in seconds between two calls of `func`
    :returns: return value of `func`
    """
    for i in range(retry_count + 1):
        try:
            return func()
        except exceptions:
            exc_info = sys.exc_info()
            if i != retry_count:
                print('Exception occurred: %s (%s). Retrying in %.2f seconds (retry %d/%d).\n' % (exc_info[0], exc_info[1], delay, i, retry_count))
                time.sleep(delay)
            else:
                print('Exception occurred: %s (%s). This was the last retry (retry %d/%d).\n' % (exc_info[0], exc_info[1], i, retry_count))
    else:  # noqa: PLW0120
        assert exc_info[1] is not None
        raise exc_info[1].with_traceback(exc_info[2])


def verify_ldap_object(
        baseDn: str,
        expected_attr: Mapping[str, Sequence[bytes | str]] | None = None,
        strict: bool = True,
        should_exist: bool = True,
        retry_count: int = 20,
        delay: float = 10,
        primary: bool = False,
        pre_check: Callable[..., None] | None = None,
        pre_check_kwargs: Dict[str, Any] | None = None,
        not_expected_attr: Dict[str, str] | None = None,
) -> None:
    """
    Verify [non]existence and attributes of LDAP object.

    :param str baseDn: DN of object to check
    :param dict expected_attr: attributes and their values that the LDAP object is expected to have
    :param bool strict: value lists of multi-value attributes must be complete
    :param bool should_exist: whether the object is expected to exist
    :param int retry_count: how often to retry the verification if it fails before raising an exception
    :param float delay: waiting time in seconds between retries on verification failures
    :param bool primary: whether to connect to the primary (DC master) instead of local LDAP (to be
            exact: ucr[ldap/server/name], ucr['ldap/server/addition'])
    :param pre_check: function to execute before starting verification. Value should be a function object
            like `utils.wait_for_replication`.
    :param dict pre_check_kwargs: dict with kwargs to pass to `pre_check()` call
    :param dict not_expected_attr: attributes and their values that the LDAP object is NOT expected to have
    :return: None
    :raises LDAPObjectNotFound: when no object was found at `baseDn`
    :raises LDAPUnexpectedObjectFound: when an object was found at `baseDn`, but `should_exist=False`
    :raises LDAPObjectValueMissing: when a value listed in `expected_attr` is missing in the LDAP object
    :raises LDAPObjectUnexpectedValue: if `strict=True` and a multi-value attribute of the LDAP object
            has more values than were listed in `expected_attr` or an `not_expected_attr` was found
    """
    ucr = UCR
    ucr.load()
    retry_count = int(ucr.get("tests/verify_ldap_object/retry_count", retry_count))
    delay = int(ucr.get("tests/verify_ldap_object/delay", delay))

    if pre_check:
        pre_check(**(pre_check_kwargs or {}))

    return retry_on_error(
        functools.partial(__verify_ldap_object, baseDn, expected_attr, strict, should_exist, primary, not_expected_attr),
        (LDAPUnexpectedObjectFound, LDAPObjectNotFound, LDAPObjectValueMissing, LDAPObjectUnexpectedValue),
        retry_count,
        delay)


def __verify_ldap_object(
        baseDn: str,
        expected_attr: Mapping[str, Sequence[bytes | str]] | None = None,
        strict: bool = True,
        should_exist: bool = True,
        primary: bool = False,
        not_expected_attr: Dict[str, str] | None = None,
) -> None:
    if expected_attr is None:
        expected_attr = {}
    if not_expected_attr is None:
        not_expected_attr = {}
    try:
        _dn, attr = get_ldap_connection(primary=primary).search(
            filter='(objectClass=*)',
            base=baseDn,
            scope=ldap.SCOPE_BASE,
            attr=set(chain(expected_attr.keys(), not_expected_attr.keys())),
        )[0]
    except (ldap.NO_SUCH_OBJECT, IndexError):
        if should_exist:
            raise LDAPObjectNotFound('DN: %s' % baseDn)
        return

    if not should_exist:
        raise LDAPUnexpectedObjectFound('DN: %s' % baseDn)

    values_missing = {}
    unexpected_values = {}
    for attribute, expected_values_ in expected_attr.items():
        found_values = set(attr.get(attribute, []))
        expected_values = {x if isinstance(x, bytes) else x.encode('UTF-8') for x in expected_values_}

        difference = expected_values - found_values
        if difference:
            values_missing[attribute] = difference

        if strict:
            difference = found_values - expected_values
            if difference:
                unexpected_values[attribute] = difference

    for attribute, not_expected_values_ in not_expected_attr.items():
        if strict and attribute in expected_attr.keys():
            continue
        found_values = set(attr.get(attribute, []))
        not_expected_values = {x if isinstance(x, bytes) else x.encode('UTF-8') for x in not_expected_values_}
        intersection = found_values.intersection(not_expected_values)
        if intersection:
            unexpected_values[attribute] = intersection

    mixed = {key: (values_missing.get(key), unexpected_values.get(key)) for key in list(values_missing) + list(unexpected_values)}
    msg = 'DN: %s\n%s\n' % (
        baseDn,
        '\n'.join(
            "%s: %r, %s %s" % (
                attribute,
                attr.get(attribute),
                ('missing: %r;' % "', ".join(x.decode('UTF-8', 'replace') for x in difference_missing)) if difference_missing else '',
                ('unexpected: %r' % "', ".join(x.decode('UTF-8', 'replace') for x in difference_unexpected)) if difference_unexpected else '',
            ) for attribute, (difference_missing, difference_unexpected) in mixed.items()),
    )

    if values_missing:
        raise LDAPObjectValueMissing(msg)
    if unexpected_values:
        raise LDAPObjectUnexpectedValue(msg)


def s4connector_present() -> bool:
    ucr = ConfigRegistry()
    ucr.load()

    if ucr.is_true('directory/manager/samba3/legacy', False):
        return False
    if ucr.is_false('directory/manager/samba3/legacy', False):
        return True

    for _dn, attr in get_ldap_connection().search(
            filter='(&(|(objectClass=univentionDomainController)(objectClass=univentionMemberServer))(univentionService=S4 Connector))',
            attr=['aRecord'],
    ):
        if 'aRecord' in attr:
            return True
    return False


def stop_s4connector() -> None:
    if package_installed('univention-s4-connector'):
        subprocess.call((S4CONNECTOR_INIT_SCRIPT, 'stop'))


def start_s4connector() -> None:
    if package_installed('univention-s4-connector'):
        subprocess.call((S4CONNECTOR_INIT_SCRIPT, 'start'))


def restart_s4connector() -> None:
    stop_s4connector()
    start_s4connector()


def stop_slapd() -> None:
    subprocess.call((SLAPD_INIT_SCRIPT, 'stop'))


def start_slapd() -> None:
    subprocess.call((SLAPD_INIT_SCRIPT, 'start'))


def restart_slapd() -> None:
    subprocess.call((SLAPD_INIT_SCRIPT, 'restart'))


def stop_listener() -> None:
    subprocess.call(('systemctl', 'stop', 'univention-directory-listener'))


def start_listener() -> None:
    subprocess.call(('systemctl', 'start', 'univention-directory-listener'))


def restart_listener() -> None:
    subprocess.call(('systemctl', 'restart', 'univention-directory-listener'))


def restart_firewall() -> None:
    subprocess.call((FIREWALL_INIT_SCRIPT, 'restart'))


class AutomaticListenerRestart:
    """
    Automatically restart Univention Directory Listener when leaving the "with" block::

        with AutomaticListenerRestart() as alr:
            with ucr_test.UCSTestConfigRegistry() as ucr:
                # set some ucr variables, that influence the Univention Directory Listener
                univention.config_registry.handler_set(['foo/bar=ding/dong'])
    """

    def __enter__(self) -> AutomaticListenerRestart:  # FIXME Py3.9: Self
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        restart_listener()


class AutoCallCommand:
    """
    Automatically call the given commands when entering/leaving the "with" block.
    The keyword arguments enter_cmd and exit_cmd are optional::

        with AutoCallCommand(
                enter_cmd=['/etc/init.d/dovecot', 'reload'],
                exit_cmd=['/etc/init.d/dovecot', 'restart']) as acc:
            with ucr_test.UCSTestConfigRegistry() as ucr:
                # set some ucr variables, that influence the Univention Directory Listener
                univention.config_registry.handler_set(['foo/bar=ding/dong'])

    In case some filedescriptors for stdout/stderr have to be passed to the executed
    command, they may be passed as kwarg::

        with AutoCallCommand(
                enter_cmd=['/etc/init.d/dovecot', 'reload'],
                exit_cmd=['/etc/init.d/dovecot', 'restart'],
                stderr=open('/dev/zero', 'w')) as acc:
            pass
    """

    def __init__(self, enter_cmd: Sequence[str] | None = None, exit_cmd: Sequence[str] | None = None, stdout: IO[str] | None = None, stderr: IO[str] | None = None) -> None:
        self.enter_cmd = None
        if type(enter_cmd) in (list, tuple):
            self.enter_cmd = enter_cmd
        self.exit_cmd = None
        if type(exit_cmd) in (list, tuple):
            self.exit_cmd = exit_cmd
        self.pipe_stdout = stdout
        self.pipe_stderr = stderr

    def __enter__(self) -> AutoCallCommand:  # FIXME Py3.9: Self
        if self.enter_cmd:
            subprocess.call(self.enter_cmd, stdout=self.pipe_stdout, stderr=self.pipe_stderr)
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        if self.exit_cmd:
            subprocess.call(self.exit_cmd, stdout=self.pipe_stdout, stderr=self.pipe_stderr)


class FollowLogfile:
    """
    Prints the contents of the listed files on exit of the with block if
    an exception occurred.
    Set always=True to also print them without exception.
    You may wish to make the server flush its logs before existing the
    with block. Use AutoCallCommand inside the block for that::

        cmd = ('doveadm', 'log', 'reopen')
        with FollowLogfile(logfiles=['/var/log/syslog', '/var/log/mail.log']):
            with utils.AutoCallCommand(enter_cmd=cmd, exit_cmd=cmd):
                pass

        with FollowLogfile(logfiles=['/var/log/syslog'], always=True):
            with utils.AutoCallCommand(enter_cmd=cmd, exit_cmd=cmd):
                pass
    """

    def __init__(self, logfiles: Iterable[str], always: bool = False) -> None:
        """
        :param logfiles: list of absolute filenames to read from
        :param always: bool, if True: print logfile change also if no error occurred (default=False)
        """
        assert isinstance(always, bool)
        self.always = always
        self.logfile_pos: Dict[str, int] = dict.fromkeys(logfiles, 0)

    def __enter__(self) -> FollowLogfile:  # FIXME Py3.9: Self
        self.logfile_pos.update((logfile, os.path.getsize(logfile)) for logfile in self.logfile_pos)
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        if self.always or exc_type:
            for logfile, pos in self.logfile_pos.items():
                with open(logfile) as log:
                    log.seek(pos, 0)
                    print(logfile.center(79, "="))
                    sys.stdout.writelines(log)
                    print("=" * 79)


class ReplicationType(IntEnum):
    LISTENER = 1
    POSTRUN = 2
    S4C_FROM_UCS = 3
    S4C_TO_UCS = 4
    DRS = 5


def wait_for_replication_from_master_openldap_to_local_samba(replication_postrun: bool = False, ldap_filter: str | None = None, verbose: bool = True) -> None:
    """Wait for all kind of replications"""
    # the order matters!
    conditions: List[Tuple[ReplicationType, Any]] = [(ReplicationType.LISTENER, 'postrun' if replication_postrun else True)]
    ucr = UCR
    ucr.load()
    if ucr.get('samba4/ldap/base'):
        conditions.append((ReplicationType.S4C_FROM_UCS, ldap_filter))
    if ucr.get('server/role') in ('domaincontroller_backup', 'domaincontroller_slave'):
        conditions.append((ReplicationType.DRS, ldap_filter))
    wait_for(conditions, verbose=True)


def wait_for_replication_from_local_samba_to_local_openldap(replication_postrun: bool = False, ldap_filter: str | None = None, verbose: bool = True) -> None:
    """Wait for all kind of replications"""
    conditions = []
    # the order matters!
    ucr = UCR
    ucr.load()
    if ucr.get('server/role') in {'domaincontroller_backup', 'domaincontroller_slave'}:
        conditions.append((ReplicationType.DRS, ldap_filter))
    if ucr.get('samba4/ldap/base'):
        conditions.append((ReplicationType.S4C_FROM_UCS, ldap_filter))
    if replication_postrun:
        conditions.append((ReplicationType.LISTENER, 'postrun'))
    else:
        conditions.append((ReplicationType.LISTENER, None))
    wait_for(conditions, verbose=True)


def wait_for(conditions: List[Tuple[ReplicationType, Any]] | None = None, verbose: bool = True) -> None:
    """Wait for all kind of replications"""
    for replicationtype, detail in conditions or []:
        if replicationtype == ReplicationType.LISTENER:
            if detail == 'postrun':
                wait_for_listener_replication_and_postrun(verbose)
            else:
                wait_for_listener_replication(verbose)
        elif replicationtype == ReplicationType.S4C_FROM_UCS:
            wait_for_s4connector_replication(verbose)
            if detail:
                # TODO: search in Samba/AD with filter=detail
                pass
        elif replicationtype == ReplicationType.S4C_TO_UCS:
            wait_for_s4connector_replication(verbose)
            if detail:
                # TODO: search in OpenLDAP with filter=detail
                pass
        elif replicationtype == ReplicationType.DRS:
            if not isinstance(detail, dict):
                detail = {'ldap_filter': detail}
            wait_for_drs_replication(verbose=verbose, **detail)


def wait_for_drs_replication(*args: Any, **kwargs: Any) -> None:
    from univention.testing.ucs_samba import wait_for_drs_replication
    return wait_for_drs_replication(*args, **kwargs)


def wait_for_listener_replication(verbose: bool = True) -> None:
    sys.stdout.flush()
    time.sleep(1)  # Give the notifier some time to increase its transaction id
    if verbose:
        print('Waiting for replication...')
    for _ in range(300):
        # The "-c 1" option ensures listener and notifier id are equal.
        # Otherwise the check is successful as long as the listener id changed since the last check.
        cmd = ('/usr/lib/nagios/plugins/check_univention_replication', '-c', '1')
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        _stdout, _stderr = proc.communicate()
        if proc.returncode == 0:
            if verbose:
                print('Done: replication complete.')
            return
        print('.', end=' ')
        time.sleep(1)

    print('Error: replication incomplete.')
    raise LDAPReplicationFailed()


def get_lid() -> int:
    """get_lid() returns the last processed notifier ID of univention-directory-listener."""
    with open("/var/lib/univention-directory-listener/notifier_id") as notifier_id:
        return int(notifier_id.readline())


def wait_for_listener_replication_and_postrun(verbose: bool = True) -> None:
    # Postrun function in listener modules are called after 15 seconds without any events
    wait_for_listener_replication(verbose=verbose)
    if verbose:
        print("Waiting for postrun...")
    lid = get_lid()
    seconds_since_last_change = 0
    for _ in range(300):
        time.sleep(1)
        print('.', end=' ')
        if lid == get_lid():
            seconds_since_last_change += 1
        else:
            seconds_since_last_change = 0

        # Less than 15 sec because a postrun function can potentially make ldap changes,
        # which would result in a loop here.
        if seconds_since_last_change > 12:
            time.sleep(20)  # Give the postrun function some time
            if verbose:
                print("Postrun should have run")
            return
        lid = get_lid()
    print("Postrun was probably never called in the last 300 seconds")
    raise LDAPReplicationFailed


def wait_for_s4connector_replication(verbose: bool = True) -> None:
    if verbose:
        print('Waiting for connector replication')
    import univention.testing.ucs_samba
    try:
        univention.testing.ucs_samba.wait_for_s4connector(17)
    except OSError as exc:  # nagios not installed
        if verbose:
            print(f'Nagios not installed: {exc}', file=sys.stderr)
        time.sleep(16)
    except univention.testing.ucs_samba.WaitForS4ConnectorTimeout:
        if verbose:
            print('Warning: S4 Connector replication was not finished after 17 seconds', file=sys.stderr)


# backwards compatibility
wait_for_replication = wait_for_listener_replication
wait_for_replication_and_postrun = wait_for_listener_replication_and_postrun
wait_for_connector_replication = wait_for_s4connector_replication


def package_installed(package: str) -> bool:
    sys.stdout.flush()
    with open('/dev/null', 'w') as null:
        return (subprocess.call("dpkg-query -W -f '${Status}' %s | grep -q ^install" % package, stderr=null, shell=True) == 0)


def fail(log_message: str | None = None, returncode: int = 1) -> NoReturn:
    print('### FAIL ###')
    if log_message:
        print('%s\n###      ###' % log_message)
        if sys.exc_info()[-1]:
            print(traceback.format_exc(), file=sys.stderr)
    sys.exit(returncode)


def uppercase_in_ldap_base() -> bool:
    ucr = ConfigRegistry()
    ucr.load()
    return not ucr.get('ldap/base').islower()


def is_udp_port_open(port: int, ip: str | None = None) -> bool:
    if ip is None:
        ip = '127.0.0.1'
    try:
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.connect((ip, int(port)))
        os.write(udp_sock.fileno(), b'X')
        os.write(udp_sock.fileno(), b'X')
        os.write(udp_sock.fileno(), b'X')
        return True
    except OSError as ex:
        print(f'is_udp_port_open({port}) failed: {ex}')
    return False


def is_port_open(port: int, hosts: Iterable[str] | None = None, timeout: float = 60) -> bool:
    """
    check if port is open, if host == None check
    hostname and 127.0.0.1

    :param int port: TCP port number
    :param hosts: list of hostnames or localhost if hosts is None.
    :type hosts: list[str] or None
    :return: True if at least on host is reachable, False otherwise.
    :rtype: boolean
    """
    if hosts is None:
        hosts = (socket.gethostname(), '127.0.0.1', '::1')
    for host in hosts:
        address = (host, int(port))
        try:
            connection = socket.create_connection(address, timeout)
            connection.close()
            return True
        except OSError as ex:
            print(f'is_port_open({port}) failed: {ex}')
    return False


def no_change_in_file(no_change_for: int, log_file: str) -> bool:
    modify_time = os.path.getmtime(log_file)
    current_time = time.time()
    if (current_time - modify_time) >= no_change_for:
        return True
    return False


def wait_for_s4_connector_to_be_inactive(no_change_for: int = 15) -> None:
    log_file = '/var/log/univention/connector-s4.log'
    if not os.path.isfile(log_file):
        return
    for i in range(30):
        if no_change_in_file(no_change_for, log_file):
            logger.debug(f'no change in {log_file} for {no_change_for}s')
            print(f'no change in {log_file} for {no_change_for}s')
            break
        logger.info('connector is active, waiting')
        print('connector is active, waiting')
        time.sleep(no_change_for + 3)
    else:
        print('wait_for_s4_connector_to_be_inactive timed out, contiuing anyway')
        logger.error('wait_for_s4_connector_to_be_inactive timed out, contiuing anyway')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
