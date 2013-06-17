import ldap
import time
import univention.uldap as uldap
import univention.config_registry

def getLdapConnection(pwdfile = False, start_tls = 2, decode_ignorelist = []):
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()

	port = int(ucr.get('ldap/server/port', 7389))
	binddn = ucr.get('tests/domainadmin/account', 'uid=Administrator,cn=users,%s' % ucr['ldap/base'])
	bindpw = None
	ldapServers = []
	if ucr['ldap/server/name']:
		ldapServers.append(ucr['ldap/server/name'])
	if ucr['ldap/servers/addition']:
		ldapServers.extend(ucr['ldap/server/addition'].split())

	if pwdfile:
		with open(ucr['tests/domainadmin/pwdfile']) as f:
			bindpw = f.read().strip('\n')
	else:
		bindpw = ucr['tests/domainadmin/pwd']

	
	for ldapServer in ldapServers:
		try:
			lo = uldap.access(host=ldapServer, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=start_tls, decode_ignorelist=decode_ignorelist)
			return lo
		except ldap.SERVER_DOWN:
			pass
	raise ldap.SERVER_DOWN

def wait_for_replication():
	print 'Waiting for replication:'
	for i in range(0,300):
		rc = subprocess.call('/usr/lib/nagios/plugins/check_univention_replication')
		if rc == 0:
			break
		time.sleep(1)
	if i >= 300:
		print 'Error: replication incomplete.'
		return 1
	print 'Done: replication complete.'
	return 0

def wait_for_replication_and_postrun ():
	rc = wait_for_replication ()
	print "Waiting for postrun"
	time.sleep(17)
	return rc
