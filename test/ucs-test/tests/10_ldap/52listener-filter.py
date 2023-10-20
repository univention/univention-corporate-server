#!/usr/share/ucs-test/runner python3
## desc: |
##  Test filter mechanism for Listener cache
## bugs: [38823]
## packages:
##  - univention-directory-listener (>= 9.0.2-6)
## exposure: dangerous

from __future__ import absolute_import, annotations

from os import chown, mkdir
from os.path import join
from pwd import getpwnam
from shutil import rmtree
from socket import create_connection, error as socket_error
from subprocess import Popen
from sys import exit
from tempfile import mkdtemp
from time import sleep
from types import TracebackType
from typing import Dict, List, Type

from univention.config_registry.frontend import handler_set
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.testing.utils import verify_ldap_object


MODULE = 'container/ou'
UNIQUE = 'ucs-test38823'
TMPDIR = '/tmp'
USERID = 'listener'


class Environment:

    def __init__(self) -> None:
        self.tmpdir = None
        self.mdir = None
        self.cdir = None

        ent = getpwnam(USERID)
        self.uid = ent.pw_uid

    def __enter__(self) -> Environment:
        self.tmpdir = mkdtemp(prefix='ucs-test', dir=TMPDIR)
        print('I: tmpdir=%r' % (self.tmpdir,))
        chown(self.tmpdir, self.uid, -1)

        self.mdir = self.mkdir('module')
        self.cdir = self.mkdir('cache')

        self.copy_handler()
        return self

    def mkdir(self, name: str) -> str:
        path = join(self.tmpdir, name)
        mkdir(path)
        chown(path, self.uid, -1)
        return path

    def copy_handler(self) -> None:
        with open(argv[0]) as source, open(join(self.mdir, 'filter.py'), 'w') as target:
            for line in source:
                if line.startswith('TMPDIR = '):
                    line = 'TMPDIR = %r\n' % (self.tmpdir,)
                target.write(line)

    def __exit__(self, exc_type: Type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        rmtree(self.tmpdir, ignore_errors=True)
        self.tmpdir = None


class Listener:

    def __init__(self, ucr: Dict[str, str], env: Environment) -> None:
        self.ucr = ucr
        self.env = env
        self.proc = None
        self.cmd = [
            '/usr/sbin/univention-directory-listener',
            '-b', self.ucr['ldap/base'],
            '-m', self.env.mdir,
            '-c', self.env.cdir,
            '-x',
            '-ZZ',
            '-D', self.ucr['ldap/hostdn'],
            '-y', '/etc/machine.secret',
        ]

    def __enter__(self) -> Listener:
        self.init_listener()
        self.run_listener()
        return self

    def init_listener(self) -> None:
        cmd = self.cmd + [
            '-d', '2',
            '-i',
        ]
        proc = Popen(cmd, close_fds=True)
        print('I: %d = %r' % (proc.pid, cmd))
        ret = proc.wait()
        print('I: ret=%r' % (ret,))
        if ret:
            exit(ret)

    def run_listener(self) -> Listener:
        cmd = self.cmd + [
            '-d', '4',
            '-F',
        ]
        self.proc = Popen(cmd, close_fds=True)
        print('I: %d = %r' % (self.proc.pid, cmd))
        return self

    def __exit__(self, exc_type: Type[Exception] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        if not exc_type:
            self.wait_transactions()
        self.kill_listener()

        ret = self.proc.wait()
        print('I: ret=%d' % (ret,))
        self.proc = None

    def wait_transactions(self) -> None:
        prev_master = 0
        i = 0
        while i < 10:
            master = self.get_master_transaction()
            local = self.get_local_transaction()
            print("I: %d <= %d >= %d %d..." % (local, master, prev_master, i))
            if local == master:
                return
            i = i + 1 if master == prev_master else 0
            prev_master = master
            sleep(1)

    def get_master_transaction(self) -> int | None:
        hostname = self.ucr['ldap/master']
        try:
            sock = create_connection((hostname, 6669), 60.0)

            sock.send(b'Version: 3\nCapabilities: \n\n')
            sock.recv(100)

            sock.send(b'MSGID: 1\nGET_ID\n\n')
            result = sock.recv(100).decode('ASCII')

            sock.close()
        except socket_error as ex:
            print(f'E: error talking to UDN on {hostname}: {ex}')
            return

        lines = result.splitlines()
        return int(lines[1])

    def get_local_transaction(self) -> int:
        filename = join(self.env.cdir, 'notifier_id')
        with open(filename) as nid_file:
            nid = nid_file.read()
        return int(nid)

    def kill_listener(self) -> None:
        if not self.proc:
            return

        self.proc.terminate()
        for i in range(6):
            ret = self.proc.poll()
            print('I: ret=%s %d...' % (ret, i))
            if ret is not None:
                break
            sleep((1 << i) / 10.0)
        else:
            self.proc.kill()


def main() -> None:
    error = False
    with Environment() as env, UCSTestConfigRegistry() as ucr:
        handler_set(
            [f'listener/cache/filter=(ou={UNIQUE})'],
            opts={'schedule': True},
            quiet=False)

        with Listener(ucr, env) as listener, UCSTestUDM() as udm:
            ou = udm.create_object(MODULE, name=UNIQUE)
            udm.modify_object(MODULE, dn=ou, description=UNIQUE)
            listener.wait_transactions()
            verify_ldap_object(ou)

        error |= unexpected_transactions(env, ucr)
        error |= is_not_in_cache(env, ucr)

    exit(1 if error else 0)


def unexpected_transactions(env: Environment, ucr: Dict[str, str]) -> bool:
    found_add = False
    found_modify = False
    found_other = False

    dn = f'ou={UNIQUE},{ucr["ldap/base"]}'

    with open(join(env.tmpdir, UNIQUE)) as log:
        for line in log:
            line = line.strip()
            if line == repr((dn, True, False, 'a')):
                print(f'I: Found add: {line}')
                found_add = True
            elif line == repr((dn, True, False, 'm')):
                print(f'I: Found modify: {line}')
                found_modify = True
            elif eval(line)[0].endswith(dn):  # noqa: PGH001
                found_other = True
                print(f'E: Found other: {line}')

    return found_other or not found_add or not found_modify


def is_not_in_cache(env: Environment, ucr: Dict[str, str]) -> bool:
    error = False

    dn = f'dn: ou={UNIQUE},{ucr["ldap/base"]}'

    dump = join(env.tmpdir, 'dump')
    cmd = [
        '/usr/sbin/univention-directory-listener-dump',
        '-c', env.cdir,
        '-O', dump,
    ]
    proc = Popen(cmd, close_fds=True)
    print('I: %d = %r' % (proc.pid, cmd))
    proc.wait()

    with open(dump) as cache:
        for line in cache:
            line = line.strip()
            if line == dn:
                error = True
                print(f'E: Found DN: {line}')
            elif UNIQUE in line:
                print(f'W: Found line: {line}')

    return error


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]], cmd: str = '') -> None:
    with open(join(TMPDIR, UNIQUE), 'a') as log:
        print(repr((dn, bool(new), bool(old), cmd)), file=log)


if __name__ == '__main__':
    from sys import argv
    main()
else:
    name = "filter"
    description = "Test filter mechanism for Listener cache"
    filter = "(objectClass=organizationalUnit)"
    modrdn = "1"

# vim:set ft=python:
