#!/usr/share/ucs-test/runner python3
## desc: Test if GPOs created on a native Windows Server work with S4
## exposure: dangerous
## packages: [univention-samba4, ucs-windows-tools]
## tags: [basic, windows_gpo_test, native_win_client, SKIP]
## bugs: [37568]
## roles:
## - domaincontroller_master
## - domaincontroller_slave

import xml.etree.ElementTree as ET
from os import path
from re import search
from subprocess import PIPE, Popen
from sys import exit

import univention.winexe
from univention.config_registry import ConfigRegistry
from univention.testing import utils
from univention.testing.codes import TestCodes
from univention.testing.strings import random_username
from univention.testing.ucs_samba import force_drs_replication
from univention.testing.udm import UCSTestUDM


def run_cmd(cmd, stdout=PIPE, stdin=None, std_in=None, encoding='UTF-8'):
    """
    Creates a process as a Popen instance with a given 'cmd'
    and 'communicates' with it.
    """
    proc = Popen(cmd, stdout=stdout, stderr=PIPE, stdin=stdin)
    stdout, stderr = proc.communicate(std_in)
    return stdout.decode(encoding), stderr.decode(encoding)


def remove_samba_warnings(input_str):
    """Removes the Samba Warning/Note from the given input_str."""
    # ignoring following messages (Bug #37362):
    input_str = input_str.replace('WARNING: No path in service IPC$ - making it unavailable!', '')
    return input_str.replace('NOTE: Service IPC$ is flagged unavailable.', '').strip()


def run_samba_tool(cmd, stdout=PIPE):
    """
    Creates a process as a Popen instance with a given 'cmd'
    and 'communicates' with it. Adds samba credintials to cmd.
    Returns (stdout, stderr).
    """
    cmd += samba_credentials
    stdout, stderr = run_cmd(cmd)

    if stderr:
        stderr = remove_samba_warnings(stderr)
    if stdout:
        stdout = remove_samba_warnings(stdout)
    return stdout, stderr


def samba_create_test_user():
    """Creates a 'test_username' via samba-tool."""
    print(f"\nCreating a '{test_username}' user for the test.")
    cmd = ("samba-tool", "user", "create", test_username, "Univention@99", "--given-name=" + test_username)

    stdout, stderr = run_samba_tool(cmd)
    if stderr:
        print(f"An error/warning occurred while trying to create a user with a username '{test_username}' via command: '{' '.join(cmd)}' \nSTDERR: {stderr}")
    if stdout:
        print(stdout)


def windows_create_gpo(gpo_name, gpo_comment, server=""):
    """
    Creates a GPO with a given 'gpo_name' and 'gpo_comment' via
    winexe running the powershell script on the Windows host.
    """
    print("\nCreating GPO for the test with a name:", gpo_name)
    try:
        ret_code, stdout, stderr = Win.create_gpo(gpo_name, gpo_comment, server)
        if ret_code != 0:
            utils.fail(f"The creation of the GPO on the Windows host returned code '{ret_code}' when 0 is expected. STDOUT: {stdout} STDERR: {stderr}")
    except univention.winexe.WinExeFailed as exc:
        utils.fail("An Error occurred while creating GPO remotely: %r" % exc)


def windows_link_gpo(gpo_name, container, server=""):
    """
    Links a given 'gpo_name' to a container using powershell script
    on Windows Host via winexe.
    """
    print(f"\nLinking GPO '{gpo_name}' to a '{container}'")
    try:
        ret_code, stdout, stderr = Win.link_gpo(
            gpo_name, 1, container, server)
        if ret_code != 0:
            utils.fail(f"The linking of the GPO on the Windows host returned code '{ret_code}' when 0 is expected. STDOUT: {stdout} STDERR: {stderr}")
    except univention.winexe.WinExeFailed as exc:
        utils.fail("An Error occurred while linking a GPO remotely: %r" % exc)


def windows_force_gpo_update():
    print("Forcing GPO update on Windows:")
    try:
        ret_code, stdout, stderr = Win.force_gpo_update()
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
    except univention.winexe.WinExeFailed as exc:
        utils.fail("An Error occurred while linking a GPO remotely: %r" % exc)


def windows_set_gpo_security_filter(gpo_name, permission_level, target_name, target_type, replace="False", server=""):
    """
    Applies the 'gpo_name' GPO to the 'target_name' of the 'target_type'
    by executing a powershell script on Windows host via winexe.
    By default (server="") the powershell code will select
    the Master (fsmo: PDC emulator) to run against.
    """
    if permission_level not in ("GpoRead", "GpoApply", "GpoEdit", "GpoEditDeleteModifySecurity", "None"):
        utils.fail(f"Set-GPPermissions: unsupported permission_level: {permission_level}")

    if target_type not in ("Computer", "User", "Group"):
        utils.fail(f"Set-GPPermissions: unsupported target_type: {target_type}")

    print(f"\nSet-GPPermissions on '{gpo_name}' for '{target_name}' '{target_type}' to '{permission_level}'")
    try:
        ret_code, stdout, stderr = Win.Set_GPPermissions(
            gpo_name,
            permission_level,
            target_name,
            target_type,
            replace,
            server)
        if ret_code != 0:
            utils.fail(f"Set-GPPermissions on the Windows host returned status '{ret_code}' when 0 is expected. STDOUT: {stdout} STDERR: {stderr}")
    except univention.winexe.WinExeFailed as exc:
        utils.fail("Exception during Set-GPPermissions: %r" % exc)


def samba_check_gpo_exists(gpo_name):
    """Checks that GPO with 'gpo_name' exists via samba-tool."""
    print(f"\nChecking that GPO '{gpo_name}' exists.")
    cmd = ("samba-tool", "gpo", "listall")

    stdout, stderr = run_samba_tool(cmd)
    if not stdout:
        utils.fail("The samba-tool did not produce any output when list of all GPOs is expected.")
    if gpo_name not in stdout:
        utils.fail(f"The GPO '{gpo_name}' was not found in the list of all GPOs.")


def windows_set_gpo_registry_value(gpo_name, reg_key, value_name, value, value_type, server=""):
    """
    Sets the 'value_name', 'value' and 'value_type' for 'gpo_name' Registry Key
    By default (server="") the powershell code will select
    the Master (fsmo: PDC emulator) to run against.
    """
    print(f"\nModifying the '{gpo_name}' GPO '{reg_key}' registry key ")
    try:
        ret_code, stdout, stderr = Win.Set_GPRegistryValue(
            gpo_name,
            reg_key,
            value_name,
            value,
            value_type,
            server)
        if ret_code != 0:
            utils.fail(f"The modification of the GPO on the Windows host returned code '{ret_code}' when 0 is expected. STDOUT: {stdout} STDERR: {stderr}")
    except univention.winexe.WinExeFailed as exc:
        utils.fail("An Error occurred while modifying GPO remotely: %r" % exc)


def samba_get_gpo_uid_by_name(gpo_name):
    """Returns the {GPO UID} for the given gpo_name using samba-tool."""
    stdout, stderr = run_samba_tool(("samba-tool", "gpo", "listall"))
    if not stdout:
        utils.fail("The samba-tool did not produce any output when list of all GPOs is expected.")
    if stderr:
        print("Samba-tool STDERR:", stderr)

    stdout = stdout.split('\n\n')  # separate GPOs
    for gpo in stdout:
        if gpo_name in gpo:
            return '{' + search('{(.+?)}', gpo).group(1) + '}'


def windows_check_gpo_report(gpo_name, identity_name, server=""):
    """
    Gets the XML GPOreport for the 'gpo_name' from the remote Windows Host
    via winexe. Checks that 'identity_name' has 'gpo_name' applied.
    """
    print(f"\nCollecting and checking the GPOreport for {gpo_name}:")
    try:
        ret_code, stdout, stderr = Win.get_gpo_report(gpo_name, server)
        if ret_code != 0:
            utils.fail(f"The collection of the GPO report on the Windows host returned code '{ret_code}' when 0 is expected. STDOUT: {stdout} STDERR: {stderr}")
        if not stdout:
            utils.fail("The GPOreport STDOUT from the remote Windows Host is empty.")
        if stderr:
            print("\nGET-GPOreport STDERR:", stderr)
    except univention.winexe.WinExeFailed as exc:
        utils.fail("An Error occurred while collecting GPO report remotely: %r" % exc)

    # Recode to match encoding specified in XML header
    gporeport_unicode = stdout.decode('cp850')
    gporeport_utf16 = gporeport_unicode.encode('utf-16')

    gpo_root = ET.fromstring(gporeport_utf16)  # noqa: S314
    gpo_types = "http://www.microsoft.com/GroupPolicy/Types"

    # find the 'TrusteePermissions' tags in xml:
    for trust_perm in gpo_root.iter(f"{{{gpo_types}/Security}}TrusteePermissions"):

        # check name tag of the 'Trustee':
        for name in trust_perm.iter(f"{{{gpo_types}}}Name"):
            trustee = name.text.split('\\', 1)[-1]  # cut off netbios domain prefix
            if identity_name == trustee:
                print(f"Found GPO test identity '{identity_name}'.")

                # check GPO is applied to user/computer:
                for access in trust_perm.iter(f"{{{gpo_types}/Security}}GPOGroupedAccessEnum"):
                    if "Apply Group Policy" in access.text:
                        print(f"Confirmed '{gpo_name}' GPO application to '{identity_name}'.")
                        return True

    print("\nUnexpected GPOreport:\n")
    print(gporeport_unicode)
    utils.fail(f"\nCould not confirm that GPO '{gpo_name}' is applied to '{identity_name}'")


def sysvol_sync():
    """
    We need to sync the sysvol from the master (fsmo: PDC emulator)
    because the special Domain DFS module dfs_server/dfs_server_ad.c
    randomizes the DFS referral for the Windows client
    """
    stdout, stderr = run_cmd("/usr/share/univention-samba4/scripts/sysvol-sync.sh")
    print(stdout)
    if stderr:
        print("\nAn Error occurred during sysvol sync:", stderr)


def sysvol_check_gpo_registry_value(gpo_name, reg_key, value_name, value):
    """
    Checks that GPO exists on the filesystem level in sysvol;
    Checks the Registry.pol contents has test values.
    """
    print(f"\nChecking '{gpo_name}' GPO registry key value in Samba")
    gpo_uid = samba_get_gpo_uid_by_name(gpo_name)  # get GPO UID to determine path

    gpo_path = f'/var/lib/samba/sysvol/{domainname}/Policies/{gpo_uid}'
    if not path.exists(gpo_path):
        utils.fail(f"The location of '{gpo_name}' GPO cannot be found at '{gpo_path}'")

    if (not path.exists(gpo_path + '/Machine') or not path.exists(gpo_path + '/User')):
        # both folders should exist
        utils.fail(f"The '{gpo_name}' GPO has no Machine or User folder at '{gpo_path}'")

    if reg_key.startswith('HKCU'):
        reg_pol_file = gpo_path + '/User/Registry.pol'
    elif reg_key.startswith('HKLM'):
        reg_pol_file = gpo_path + '/Machine/Registry.pol'
    else:
        utils.fail(f"The given registry key '{reg_key}' should be either HKCU or HKLM")

    if not path.exists(reg_pol_file):
        utils.fail(f"The Registry.pol file cannot be found at '{reg_pol_file}'")

    try:
        reg_policy = open(reg_pol_file)
        # skip first 8 bytes (signature and file version):
        # https://msdn.microsoft.com/en-us/library/aa374407%28v=vs.85%29.aspx
        reg_policy_text = reg_policy.read()[8:].decode(encoding='utf-16')
        reg_policy.close()
    except OSError as exc:
        utils.fail("An Error occurred while opening '%s' file: %r" % (reg_pol_file, exc))

    reg_key = reg_key[5:]  # the 'HKCU\' or 'HKLM\' are not included:
    if reg_key not in reg_policy_text:
        utils.fail(f"Could not find '{reg_key}' Registry key in '{gpo_name}' GPO Registry.pol")

    if value_name not in reg_policy_text:
        utils.fail(f"Could not find '{value_name}' ValueName in '{gpo_name}' GPO Registry.pol")

    if value not in reg_policy_text:
        utils.fail(f"Could not find '{value}' Value in '{gpo_name}' GPO Registry.pol")


def samba_check_gpo_application_listed(gpo_name, username):
    """
    Checks if the 'gpo_name' GPO is listen in GPOs for
    'username' via samba-tool.
    """
    print(f"\nChecking that GPO '{gpo_name}' is applied to {username}")
    stdout, stderr = run_samba_tool(("samba-tool", "gpo", "list", username))
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    if not stdout:
        utils.fail("The samba-tool did not produce any output when list of all user/computer GPOs is expected.")
    if gpo_name not in stdout:
        utils.fail(f"The GPO '{gpo_name}' was not found in the list of all user/computer GPOs.")


def dns_get_host_ip(host_name, all=False):
    """Lookup host_name;"""
    print(f"\nLooking for '{host_name}' host ip address:")

    ips = []
    dig_sources = []
    for source in ['nameserver1', 'nameserver2', 'nameserver3']:
        if source in ucr:
            dig_sources.append(f"@{ucr[source]}")

    for dig_source in dig_sources:
        try:
            cmd = ['dig', dig_source, host_name, '+search', '+short']
            p1 = Popen(cmd, close_fds=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p1.communicate()
            if p1.returncode == 0:
                for i in stdout.split('\n'):
                    if i:
                        ips.append(i)
            if ips:
                break
        except OSError as ex:
            print(f"\n{cmd} failed: {ex.args[1]}")

    if not ips:
        utils.fail(f"Could not resolve '{host_name}' via DNS.")
    else:
        if all:
            print(f"Host IPs are: {ips}")
            return ips
        else:
            print(f"Host IP is: {ips[0]}")
            return ips[0]


def udm_get_windows_computer():
    """
    Using UDM looks for 'computers/windows' hostname of the joined
    Windows Host (Assuming there is only one).
    """
    stdout, stderr = run_cmd(("udm", "computers/windows", "list"))
    if stderr:
        print("\nAn Error occurred while looking for Windows Server hostname:", stderr)

    sed_stdout, stderr = run_cmd(("sed", "-n", "s/^DN: //p"), stdin=PIPE, std_in=stdout)
    if not sed_stdout:
        print("SKIP: failed to find any Windows Host DN via UDM. Perhaps host not joined as a memberserver or does not exist in this setup.")
        exit(TestCodes.REASON_INSTALL)

    return {'hostdn': sed_stdout, 'hostname': sed_stdout.split(',')[0][3:]}


def windows_check_domain():
    """Runs powershell script via Winexe to check Windows Host domain is correct."""
    print(f"Trying to check Windows host '{Win.client}' domain")
    try:
        Win.winexec("check-domain", domainname)
    except univention.winexe.WinExeFailed as exc:
        utils.fail("Failed to check that Windows host domain is correct: %r" % exc)


def samba_remove_test_user():
    """Removes 'the test_username' via samba-tool."""
    print(f"\nRemoving '{test_username}' user:")
    stdout, stderr = run_samba_tool(("samba-tool", "user", "delete", test_username))
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)


def windows_remove_test_gpo(gpo_name, server=""):
    """
    Removes the GPO with a given 'gpo_name' via
    winexe running the powershell script on the Windows host.
    """
    print("\nRemoving GPOs created for the test:", gpo_name)
    try:
        ret_code, stdout, stderr = Win.remove_gpo(gpo_name, server)
        if ret_code != 0:
            print(f"The removal of the GPO on the Windows host returned code '{ret_code}' when 0 is expected. STDOUT: {stdout} STDERR: {stderr}")
    except (univention.winexe.WinExeFailed, NameError) as exc:
        print("An Error occurred while removing GPO remotely: %r" % exc)


if __name__ == '__main__':
    """
    IMPORTANT: Windows Host should be joined to the domain prior test run!

    Finds Windows hostname and ip;
    Configures Winexe and checks win domain;
    Creates a User via samba-tool;
    Creates a GPO on the remote Windows Host (joined into Domain);
    Checks created GPO exist via samba-tool;
    Applies the GPO to the User and modifies GPO registry values;
    Checks GPO is listed by samba-tool for the User;
    Checks GPO registry values in the samba sysvol;
    Gets GPO report from Windows Host and verifies GPO application.

    Performs similar checks for Machine GPO using Windows host account.

    GPOs are applied using 'Security Filtering',
    'Authenticated Users' are set to have only GpoRead permissions.
    """
    ucr = ConfigRegistry()
    ucr.load()

    domain_admin_dn = ucr.get('tests/domainadmin/account')
    domain_admin_password = ucr.get('tests/domainadmin/pwd')
    windows_admin = ucr.get('tests/windowsadmin/account', 'Administrator')
    windows_admin_password = ucr.get('tests/windowsadmin/pwd', 'univention')
    domainname = ucr.get('domainname')
    hostname = ucr.get('hostname')
    ldap_base = ucr.get('ldap/base')

    if not all((domain_admin_dn, domain_admin_password, domainname, hostname, ldap_base)):
        print("\nFailed to obtain settings for the test from UCR. Skipping the test.")
        exit(TestCodes.REASON_INSTALL)

    domain_admin = domain_admin_dn.split(',')[0][len('uid='):]
    samba_credentials = ("--username=" + domain_admin, "--password=" + domain_admin_password)

    windows_client = udm_get_windows_computer()

    # setup winexe:
    Win = univention.winexe.WinExe(
        domainname,
        domain_admin, domain_admin_password,
        windows_admin, windows_admin_password,
        445, dns_get_host_ip(windows_client['hostname']), loglevel=4)
    windows_check_domain()

    test_username = 'ucs_test_gpo_user_' + random_username(4)
    random_gpo_suffix = random_username(4)
    test_user_gpo = 'test_user_gpo_' + random_gpo_suffix
    test_machine_gpo = 'test_machine_gpo_' + random_gpo_suffix

    UDM = UCSTestUDM()
    test_user_dn = UDM.create_user(
        username=test_username,
        password='univention',
    )[0]

    try:
        # case 1: checks with user GPO
        gpo_name = test_user_gpo
        windows_create_gpo(gpo_name, f"GPO for {test_username}")
        force_drs_replication()
        force_drs_replication(direction="out")
        samba_check_gpo_exists(gpo_name)

        sysvol_sync()
        windows_set_gpo_registry_value(
            gpo_name,
            r"HKCU\Software\Policies\Microsoft\UCSTestKey",
            "TestUserValueOne",
            "Foo",
            "String")
        force_drs_replication()
        force_drs_replication(direction="out")
        sysvol_sync()
        sysvol_check_gpo_registry_value(
            gpo_name,
            r"HKCU\Software\Policies\Microsoft\UCSTestKey",
            "TestUserValueOne",
            "Foo")

        windows_link_gpo(gpo_name, ldap_base)
        force_drs_replication()
        force_drs_replication(direction="out")
        samba_check_gpo_application_listed(gpo_name, test_username)

        windows_set_gpo_security_filter(gpo_name, 'GpoRead', 'Authenticated Users', 'Group', 'True')
        if ucr.is_true("connector/s4/mapping/gpo/ntsd", False):
            # Workaround for Bug #35336
            utils.wait_for_connector_replication()
            utils.wait_for_replication()
            utils.wait_for_connector_replication()
        windows_set_gpo_security_filter(gpo_name, 'GpoApply', test_username, 'User')
        force_drs_replication()
        force_drs_replication(direction="out")
        windows_force_gpo_update()
        windows_check_gpo_report(gpo_name, test_username)

        # case 2: checks with computer GPO
        gpo_name = test_machine_gpo
        windows_create_gpo(gpo_name, f"GPO for {windows_client['hostname']} Windows host")
        force_drs_replication()
        force_drs_replication(direction="out")
        samba_check_gpo_exists(gpo_name)

        sysvol_sync()
        windows_set_gpo_registry_value(
            gpo_name,
            r"HKLM\Software\Policies\Microsoft\UCSTestKey",
            "TestComputerValueTwo",
            "Bar",
            "String")
        force_drs_replication()
        force_drs_replication(direction="out")
        sysvol_sync()
        sysvol_check_gpo_registry_value(
            gpo_name,
            r"HKLM\Software\Policies\Microsoft\UCSTestKey",
            "TestComputerValueTwo",
            "Bar")

        windows_link_gpo(gpo_name, ldap_base)
        force_drs_replication()
        force_drs_replication(direction="out")
        samba_check_gpo_application_listed(gpo_name, windows_client['hostname'])

        windows_set_gpo_security_filter(gpo_name, 'GpoRead', 'Authenticated Users', 'Group', 'True')
        if ucr.is_true("connector/s4/mapping/gpo/ntsd", False):
            # Workaround for Bug #35336
            utils.wait_for_connector_replication()
            utils.wait_for_replication()
            utils.wait_for_connector_replication()
        windows_set_gpo_security_filter(gpo_name, 'GpoApply', windows_client['hostname'], 'Computer')
        force_drs_replication()
        force_drs_replication(direction="out")
        windows_force_gpo_update()
        windows_check_gpo_report(gpo_name, f"{windows_client['hostname']}$")
    finally:
        windows_remove_test_gpo(test_user_gpo)
        windows_remove_test_gpo(test_machine_gpo)
        UDM.remove_object('users/user', dn=test_user_dn)
