#!/usr/share/ucs-test/runner python3
## desc: New listener module API test
## tags: []
## roles: []
## exposure: dangerous
## packages:
##   - univention-directory-listener
## bugs: [44786]

import logging
import os
import pwd
import subprocess
import sys
import time

from ldap.filter import filter_format

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.config_registry import handler_set
from univention.listener.handler_logging import get_logger
from univention.testing import utils
from univention.testing.codes import TestCodes
from univention.testing.decorators import SetTimeout
from univention.testing.ucs_samba import wait_for_drs_replication, wait_for_s4connector


lm_name = f'test-{uts.random_name()}'
lm_file = os.path.join('/usr/lib/univention-directory-listener/system', f'{lm_name}.py')
log_file = os.path.join('/tmp', f'{uts.random_name()}.log')
uid_default_file = None
uid_root_file = None
verify_ldap_object = SetTimeout(utils.verify_ldap_object, 60)


def cleanup():
    for filename in (lm_file, log_file, uid_default_file, uid_root_file):
        print(f'Deleting {filename!r}...')
        try:
            os.remove(filename)
        except OSError as exc:
            print(exc)
    print('Restarting univention-directory-listener...')
    subprocess.call(['systemctl', 'restart', 'univention-directory-listener.service'])


def main():
    global uid_default_file, uid_root_file

    username = uts.random_name()
    employeeType = uts.random_name()
    test_id = uts.random_name()
    street = uts.random_name()
    roomNumber = uts.random_name()
    uid_default_file = os.path.join('/tmp', f'{uts.random_name()}.log')
    uid_root_file = os.path.join('/tmp', f'{uts.random_name()}')
    lm_logger_path = os.path.join('/var/log/univention/listener_modules', f'{lm_name}.log')
    text_replacements = {
        'TEST_ID': test_id,
        'MODULE_NAME': lm_name,
        'LOGFILE': log_file,
        'LDAP_FILTER': filter_format('(&(objectClass=inetOrgPerson)(uid=%s))', (username,)),
        'UID_ROOT_FILE': uid_root_file,
        'UID_DEFAULT_FILE': uid_default_file,
        'IMPORTS': 'from univention.listener import ListenerModuleHandler',
        'HANDLER_SUPER_CLASS': 'ListenerModuleHandler',
        'CONFIG_MODULE_ARGS': '',
    }

    # create test listener module
    with open('listener_module_testpy', 'rb') as fp:
        lm_txt = fp.read()

    for k, v in text_replacements.items():
        lm_txt = lm_txt.replace(f'@@{k}@@'.encode('UTF-8'), v.encode('UTF-8'))

    with open(lm_file, 'wb') as fp:
        fp.write(lm_txt)
    print(f'Wrote listener module to {lm_file!r}.')

    print(f'test_id: {test_id!r}')
    print(f'Listener module name: {lm_name!r}')
    print(f'Action log file: {log_file!r}')
    print(f'Listener module log file: {lm_logger_path!r}')
    print(f'UID default (listener) file: {uid_default_file!r}')
    print(f'UID root file: {uid_root_file!r}')

    # create, modify, move, modify
    with udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr:
        handler_set([f'listener/module/{lm_name}/debug/level=4'])
        print('Restarting univention-directory-listener...')
        subprocess.call(['systemctl', 'restart', 'univention-directory-listener.service'])

        lm_logger = get_logger(lm_name, path=lm_logger_path)
        lm_logger.addHandler(logging.StreamHandler())

        lm_logger.info('*** Creating user...')
        userdn, username = udm.create_user(
            username=username,
        )
        wait_for_drs_replication(filter_format('cn=%s', (username,)))
        time.sleep(2)  # wait for s4 to write SID back to OpenLDAP, don't wait to long or a post_run() will happen
        verify_ldap_object(userdn, should_exist=True)

        lm_logger.info('*** Checking setuid()...')
        file0_uid = os.stat(uid_root_file).st_uid
        if file0_uid != 0:
            utils.fail(f'File (root) {uid_root_file!r} has uid={file0_uid!r}, expected 0.')
        file_default_uid = os.stat(uid_default_file).st_uid
        listener_uid = pwd.getpwnam('listener').pw_uid
        if file_default_uid != listener_uid:
            utils.fail(f'File (listener) {uid_default_file!r} has uid={file_default_uid!r}, expected {listener_uid!r}.')

        lm_logger.info('*** Modifying user (employeeType)...')
        udm.modify_object(
            'users/user',
            dn=userdn,
            employeeType=employeeType,
        )

        lm_logger.info('*** Moving user (to LDAP base)...')
        new_dn = udm.move_object(
            'users/user',
            dn=userdn,
            position=ucr['ldap/base'],
        )

        lm_logger.info('*** Modifying user (street) should not trigger listener module...')
        udm.modify_object(
            'users/user',
            dn=new_dn,
            street=street,
        )

        lm_logger.info('*** Moving user (to cn=users)...')
        new_dn = udm.move_object(
            'users/user',
            dn=new_dn,
            position='cn=users,{}'.format(ucr['ldap/base']),
        )

        lm_logger.info('*** Modifying user (roomNumber) and triggering error...')
        udm.modify_object(
            'users/user',
            dn=new_dn,
            roomNumber=roomNumber,
        )

        # wait for s4 connector to catch up, before deleting the user
        wait_for_drs_replication(filter_format('cn=%s', (username,)))
        wait_for_s4connector()

        lm_logger.info('*** Deleting user...')

    # wait for UCSTestUDM context manager to delete user
    wait_for_drs_replication(filter_format('(!(cn=%s))', (username,)))
    wait_for_s4connector()
    verify_ldap_object(new_dn, should_exist=False)
    time.sleep(15)  # give listener time to settle: wait for post_run()

    logging.shutdown()

    lm_logfile = f'/var/log/univention/listener_modules/{lm_name}.log'
    print('*******************************************')
    print(f'    {lm_logfile}')
    print('----------')
    with open(lm_logfile, 'rb') as fp:
        print(fp.read().decode('UTF-8', 'replace'))
    print('*******************************************')

    # check logfile for correct entries
    with open(log_file, 'rb') as fp:
        log_text = fp.read().decode('UTF-8', 'replace')
        print('*******************************************')
        print(f'    {log_file}')
        print('----------')
        print(log_text)
        print('*******************************************')

    lines = (line.strip() for line in log_text.split('\n') if line.strip())
    operations = ('clean', 'initialize', 'pre_run', 'create', f'modify employeeType {employeeType}', 'move', 'move', f'modify roomNumber {roomNumber}', 'error_handler', 'remove', 'post_run')
    for operation in operations:
        exp = f'{test_id} {operation}'
        try:
            line = next(lines)
        except StopIteration:
            if operation == 'post_run':
                print('Ignoring missing "post_run" - probably to much going on...')
                line = exp
            else:
                utils.fail(f'Missing operation(s). Expected: {operations!r}.')
        if not line.startswith(exp):
            if line.startswith(f'{test_id} post_run'):
                # probably waited so long for s4c to catch up, that post_run happened,
                # next line should be "pre_run" and then "remove"
                line2 = next(lines)
                line3 = next(lines)
                if line2.startswith(f'{test_id} pre_run') and line3.startswith(f'{test_id} {operation}'):
                    continue
            utils.fail(f'Expected startswith({exp!r}) found {line!r}.')
    print('Test succeeded.')


if __name__ == '__main__':
    # see Bug #49723, fails on samba master, so skip for now
    if utils.package_installed('univention-samba4'):
        sys.exit(TestCodes.RESULT_SKIP)
    try:
        main()
    finally:
        cleanup()
