#!/usr/share/ucs-test/runner /usr/bin/py.test
## desc: Test the management/univention-ldap/scripts/univention_lastbind.py script
## roles: [domaincontroller_master, domaincontroller_backup, domaincontroller_slave]
## exposure: dangerous
## tags:
##  - SKIP


import pytest

import subprocess
import time
import imp

from univention.udm import UDM
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM
from univention.config_registry import handler_set
import univention.testing.strings as uts

try:
	import univention_lastbind
except ImportError:
	univention_lastbind = imp.load_source('univention_lastbind', '/usr/share/univention-ldap/univention_lastbind.py')


def is_role(role):
	with UCSTestConfigRegistry() as ucr:
		return ucr.get('server/role') == role


def get_other_servers():
	with UCSTestConfigRegistry() as ucr:
		role = ucr.get('server/role')
		udm = UDM.machine().version(2)
		others = []
		for mod in ['computers/domaincontroller_master', 'computers/domaincontroller_backup', 'computers/domaincontroller_slave']:
			if role not in mod:
				others.extend(list(udm.get(mod).search()))
		return others


def is_multi_domain():
	return len(get_other_servers())


#  @pytest.fixture(scope="module")
#  def univention_lastbind():
	#  return imp.load_source('univention_lastbind', '/usr/share/univention-ldap/univention_lastbind.py')


@pytest.fixture(scope="module")
def other_server():
	return get_other_servers()[0]


@pytest.fixture
def preserve_other_server_ucr(bindpwdfile, other_server):
	lastbind = subprocess.check_output(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'get', 'ldap/overlay/lastbind']).strip()
	precision = subprocess.check_output(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'get', 'ldap/overlay/lastbind/precision']).strip()
	yield
	if lastbind:
		subprocess.call(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'get', 'ldap/overlay/lastbind=%s' % (lastbind,)])
	else:
		subprocess.call(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'unset', 'ldap/overlay/lastbind'])
	if precision:
		subprocess.call(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'get', 'ldap/overlay/lastbind/precision=%s' % (precision,)])
	else:
		subprocess.call(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'unset', 'ldap/overlay/lastbind/precision'])


@pytest.fixture
def bindpwdfile(tmpdir):
	path = tmpdir.join('bindpwdfile')
	path.write('univention')
	return str(path)


@pytest.fixture
def failbindpwdfile():
	return "/qwertzui"


@pytest.fixture
def binddn(ucr):
	return "uid=Administrator,cn=users,%s" % (ucr.get('ldap/base'),)


@pytest.fixture
def failbinddn():
	return "uid=Administrator,cn=users"


@pytest.fixture
def ucr():
	with UCSTestConfigRegistry() as ucr:
		yield ucr


@pytest.fixture(scope="module")
def testudm():
	with UCSTestUDM() as udm:
		yield udm


@pytest.fixture(scope="module")
def readudm():
	return UDM.machine().version(2)


def bind_for_timestamp(dn, host=None):
	args = ['univention-ldapsearch', '-LLL', '-D', dn, '-w', 'univention', '-b', dn, 'authTimestamp']
	if host:
		args.insert(1, host)
		args.insert(1, '-h')
	out = subprocess.check_output(args)
	timestamp = [line.split()[1] for line in out.splitlines() if 'authTimestamp' in line]
	timestamp = timestamp[0] if len(timestamp) else None
	return timestamp


#  @pytest.mark.skipif(is_role('domaincontroller_slave'), reason="domaincontroller_slave can't open admin connection to UDM")
#  def test_setup_admin(univention_lastbind, capsys):
	#  args = univention_lastbind.parse_args(['--setup'])
	#  univention_lastbind.main(args)
	#  assert univention_lastbind.is_setup_done()
	#  univention_lastbind.main(args)
	#  captured = capsys.readouterr()
	#  assert 'already exists. Doing nothing.' in captured.out
	#  univention_lastbind.undo_setup()
	#  assert not univention_lastbind.is_setup_done()
	#  univention_lastbind.undo_setup()
	#  captured = capsys.readouterr()
	#  assert 'does not exist. Doing nothing.' in captured.out


#  def test_setup_credentials(univention_lastbind, binddn, bindpwdfile, capsys):
	#  args = univention_lastbind.parse_args(['--setup', '--binddn', binddn, '--bindpwdfile', bindpwdfile])
	#  univention_lastbind.main(args)
	#  assert univention_lastbind.is_setup_done()
	#  univention_lastbind.undo_setup(binddn, bindpwdfile)
	#  assert not univention_lastbind.is_setup_done()


#  def test_setup_with_wrong_bind(univention_lastbind, binddn, failbinddn, bindpwdfile, failbindpwdfile, ucr):
	#  args = univention_lastbind.parse_args(['--setup', '--binddn', binddn])
	#  with pytest.raises(univention_lastbind.ScriptError) as excinfo:
		#  univention_lastbind.main(args)
	#  assert '"binddn" provided but not "bindpwdfile".' in str(excinfo.value)

	#  args = univention_lastbind.parse_args(['--setup', '--binddn', binddn, '--bindpwdfile', failbindpwdfile])
	#  with pytest.raises(univention_lastbind.ScriptError) as excinfo:
		#  univention_lastbind.main(args)
	#  assert 'Could not open "bindpwdfile" "%s"' % (failbindpwdfile) in str(excinfo.value)

	#  args = univention_lastbind.parse_args(['--setup', '--binddn', failbinddn, '--bindpwdfile', bindpwdfile])
	#  with pytest.raises(univention_lastbind.ScriptError) as excinfo:
		#  univention_lastbind.main(args)
	#  assert 'Could not connect to server "%s" with provided "binddn" "%s" and "bindpwdfile" "%s"' % (ucr.get('ldap/server/name'), failbinddn, bindpwdfile)


#  @pytest.mark.skipif(not is_role('domaincontroller_slave'), reason="Only domaincontroller_slave cannot create admin connection without binddn/bindpwdfile")
#  def test_setup_on_slave_without_bind(univention_lastbind):
	#  args = univention_lastbind.parse_args(['--setup'])
	#  with pytest.raises(univention_lastbind.ScriptError) as excinfo:
		#  univention_lastbind.main(args)
	#  assert 'Could not create a writable connection to UDM on this server. Try to provide "binddn" and "bindpwdfile"' in str(excinfo.value)


@pytest.mark.slow
def test_save_timestamp(testudm, readudm, binddn, bindpwdfile, capsys):
	dn, _ = testudm.create_user()
	o = readudm.obj_by_dn(dn)
	timestamp = 'foo'
	capsys.readouterr()  # flush
	univention_lastbind.save_timestamp(o, timestamp)
	assert 'Warning: Could not save new timestamp "%s" to "lastbind" extended attribute of user "%s". Continuing' % (timestamp, o.dn,) in capsys.readouterr()[1]
	writeudm = univention_lastbind.get_writable_udm(binddn, bindpwdfile)
	o = writeudm.obj_by_dn(dn)
	univention_lastbind.save_timestamp(o, timestamp)
	assert "INFO: Modified 'users/user' object"  # make sure that this string is still printed on save so that we can check later that it is missing
	o.reload()
	assert o.props.lastbind == timestamp
	capsys.readouterr()  # flush
	univention_lastbind.save_timestamp(o, None)
	assert "INFO: Modified 'users/user' object" not in capsys.readouterr()[0]
	assert o.props.lastbind == timestamp
	univention_lastbind.save_timestamp(o, timestamp)
	assert "INFO: Modified 'users/user' object" not in capsys.readouterr()[0]  # test no save happens when timestamp didn't change
	assert o.props.lastbind == timestamp


@pytest.mark.slow
def test_main_single_server(binddn, bindpwdfile, ucr, testudm, readudm):
	handler_set(['ldap/overlay/lastbind=true'])
	subprocess.call(['service', 'slapd', 'restart'])
	o = readudm.obj_by_dn(testudm.create_user()[0])
	assert o.props.lastbind is None
	timestamp = bind_for_timestamp(o.dn)
	assert timestamp is not None
	args = univention_lastbind.parse_args(['--binddn', binddn, '--bindpwdfile', bindpwdfile, '--user', o.dn])
	univention_lastbind.main(args)
	o.reload()
	assert o.props.lastbind == timestamp


@pytest.mark.skipif(not is_multi_domain(), reason="Test only in multi domain")
@pytest.mark.slow
def test_main_multi_server(binddn, bindpwdfile, testudm, readudm, other_server, preserve_other_server_ucr):
	handler_set(['ldap/overlay/lastbind=true'])
	subprocess.call(['service', 'slapd', 'restart'])
	subprocess.call(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'ucr', 'set', 'ldap/overlay/lastbind=true'])
	subprocess.call(['univention-ssh', bindpwdfile, other_server.props.fqdn, 'service', 'slapd', 'restart'])
	o = readudm.obj_by_dn(testudm.create_user()[0])
	assert o.props.lastbind is None
	local_timestamp = bind_for_timestamp(o.dn)
	assert local_timestamp is not None
	time.sleep(2)
	other_timestamp = bind_for_timestamp(o.dn, other_server.props.fqdn)
	assert other_timestamp is not None
	youngest_timestamp = max(local_timestamp, other_timestamp)
	assert youngest_timestamp is not None
	args = univention_lastbind.parse_args(['--binddn', binddn, '--bindpwdfile', bindpwdfile, '--user', o.dn])
	univention_lastbind.main(args)
	o.reload()
	assert o.props.lastbind == youngest_timestamp

# TODO test precision


def test_main_not_enough_arguments():
	args = univention_lastbind.parse_args([])
	with pytest.raises(univention_lastbind.ScriptError) as excinfo:
		univention_lastbind.main(args)
	assert 'Provide either --user USER or --allusers.' in str(excinfo.value)


@pytest.mark.slow
def test_server_down(ucr, testudm, readudm, capsys):
	mod = readudm.get('computers/%s' % (ucr.get('server/role'),))
	comp = mod.get_by_id(ucr.get('hostname'),)
	slave = testudm.create_object('computers/domaincontroller_slave', name=uts.random_name(), dnsEntryZoneForward=comp.props.dnsEntryZoneForward[0][0])
	slave = readudm.obj_by_dn(slave)
	capsys.readouterr()  # flush
	univention_lastbind.get_ldap_connections()
	assert 'Server "%s" is not reachable. The "authTimestamp" will not be read from it. Continuing.' % (slave.props.fqdn,) in capsys.readouterr()[1]


def test_invalid_user(binddn, bindpwdfile):
	user = 'qqqqqq'
	args = univention_lastbind.parse_args(['--user', user, '--binddn', binddn, '--bindpwdfile', bindpwdfile])
	with pytest.raises(univention_lastbind.ScriptError) as excinfo:
		univention_lastbind.main(args)
	assert 'The provided user "%s" could not be found' % (user,) in str(excinfo.value)
