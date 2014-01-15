
import univention.config_registry
import subprocess

def createMachinePassword():
	"""
	Returns a $(pwgen) generated password according to the 
	requirements in
		machine/password/length
		machine/password/complexity
	"""
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	length = ucr.get('machine/password/length', '20')
	compl = ucr.get('machine/password/complexity', 'scn')
	p = subprocess.Popen(["pwgen", "-1", "-" + compl, length], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate()
	return stdout.strip()

def getLDAPURIs(configRegistryInstance = None):
	"""
	Returns a string with all configured LDAP servers,
	ldap/server/name and ldap/server/addition.
	Optional a UCR instance ca be given as parameter, for example
	if the function is used in a UCR template
	"""
	if configRegistryInstance:
		ucr = configRegistryInstance
	else:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	uri_string = ''
	ldaphosts=[]
	port = ucr.get('ldap/server/port', '7389')
	ldap_server_name = ucr.get('ldap/server/name')
	ldap_server_addition = ucr.get('ldap/server/addition')

	if ldap_server_name:
		ldaphosts.append(ldap_server_name)
	if ldap_server_addition:
		ldaphosts.extend(ldap_server_addition.split())
	if ldaphosts:
		urilist=[ "ldap://%s:%s" % (host, port) for host in ldaphosts ]
		uri_string = ' '.join(urilist)

	return uri_string

def getLDAPServersCommaList(configRegistryInstance = None):
	"""
	Returns a comma-separated string with all configured LDAP servers,
	ldap/server/name and ldap/server/addition.
	Optional a UCR instance ca be given as parameter, for example
	if the function is used in a UCR template
	"""
	if configRegistryInstance:
		ucr = configRegistryInstance
	else:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ldap_servers = ''
	ldaphosts=[]
	ldap_server_name = ucr.get('ldap/server/name')
	ldap_server_addition = ucr.get('ldap/server/addition')

	if ldap_server_name:
		ldaphosts.append(ldap_server_name)
	if ldap_server_addition:
		ldaphosts.extend(ldap_server_addition.split())
	if ldaphosts:
		ldap_servers = ','.join(ldaphosts)

	return ldap_servers

def custom_username(name, configRegistryInstance = None):
	"""
	Returns the customized username configured via UCR
	"""

	if not name:
		raise ValueError

	if configRegistryInstance:
		ucr = configRegistryInstance
	else:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	return ucr.get("users/default/" + name.lower().replace(" ", ""), name)

def custom_groupname(name, configRegistryInstance = None):
	"""
	Returns the customized groupname configured via UCR
	"""

	if not name:
		raise ValueError

	if configRegistryInstance:
		ucr = configRegistryInstance
	else:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	return ucr.get("groups/default/" + name.lower().replace(" ", ""), name)
