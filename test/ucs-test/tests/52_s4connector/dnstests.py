import univention.testing.strings as uts
import univention.testing.utils as utils
import subprocess
import re
from time import sleep
import random
import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()
ucr.load()
import os
import sys
import s4connector

def wait_for_sync(multiplier = 1):
	synctime = int(ucr.get("connector/s4/poll/sleep",7))
	synctime = (synctime + 3) * multiplier
	print ("Waiting {0} seconds for sync...".format(synctime))
	sleep (synctime)

def check_ldap_object(item, item_name, item_attribute = None, name_string = None):
	print (" Testing Ldap object : {0}			".format(item_name)),
	try:
		if item_attribute:
			utils.verify_ldap_object(item, {item_attribute:[name_string]})
		else:
			utils.verify_ldap_object(item)
	except:
		print (' Failed')
		sys.exit('Verification of Ldap object failed ')
	else:
		
		print(' Success ')


def test_dns_forward_zone(zone_name, test_object):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+NS\s+\"*{1}\"*'.format(zone_name, test_object))
	match(re_test_object, zone_name, 'NS')

def test_dns_txt(zone_name, test_object):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+TXT\s+\"*{1}\"*'.format(zone_name, test_object))
	match(re_test_object, zone_name, 'TXT')


def test_dns_ttl(zone_name, test_object):
	re_test_object=re.compile(r"{0}\.*\s+{1}\s+IN\s+SOA".format(zone_name, test_object))
	match(re_test_object, zone_name, 'SOA')

def test_dns_reverse_zone(zone_name, test_object):
	temp = zone_name.split('.')
	zone_namereverse = temp[2] + '.' + temp[1] + '.' + temp[0]
	re_test_object=re.compile(r"{0}.in-addr.arpa.\s+\d+\s+IN\s+NS\s+{1}".format(zone_namereverse, test_object))
	match(re_test_object, zone_name, 'NS', '-x')

def test_dns_serial(zone_name, test_object):
	re_test_object=re.compile(r"{0}\.*\s+\d+\s+IN\s+SOA\s+.+\s+.+\s+{1}\s+".format(zone_name, test_object))
	match(re_test_object, zone_name, 'SOA')

def test_dns_a_record(zone_name, test_object):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+A\s+\"*{1}\"*'.format(zone_name, test_object))
	match(re_test_object, zone_name, 'A')

def test_dns_aaaa_record(zone_name, test_object):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+AAAA\s+\"*{1}\"*'.format(zone_name, test_object))
	match(re_test_object, zone_name ,'AAAA')

def test_dns_alias(zone_name, test_object):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+CNAME\s+\"*{1}\"*'.format(zone_name, test_object))
	match(re_test_object, zone_name, 'CNAME')

def test_dns_service_record(zone_name, test_object):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+SRV\s+\"*{1}\"*'.format(zone_name, test_object))
	match(re_test_object, zone_name, 'SRV')

def test_dns_pointer_record(reverse_zone, ip, test_object):
	reverse_address = str(ip) + '.' + reverse_zone
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+PTR\s+\"*{1}\"*'.format(reverse_address, test_object))
	match(re_test_object, reverse_address, 'PTR')

def match(re_test_object, zone_name, typ, param=None):

	if not param:
		dig_subprocess = subprocess.Popen(["dig", zone_name, typ, '+noall', '+answer'], shell = False, stdout = subprocess.PIPE).communicate()
	else:
		dig_subprocess = subprocess.Popen(["dig", param, zone_name, typ, '+noall', '+answer'], shell = False, stdout = subprocess.PIPE).communicate()
	dig_answer = dig_subprocess[0].splitlines()

	found_test_object_match = False
	print ("Dig Output :")
	for line in dig_answer:
		print line
		if re.match(re_test_object, line):
			found_test_object_match = True
	if found_test_object_match:
		print
		print("  DNS synced ")
	else:
		sys.exit(" DNS not synced ")


def get_hostname():
	host = ucr.get("ldap/master")
	return host

def random_name():
	random_name = '{0} tcp {1}'.format(uts.random_name(), uts.random_name())
	return random_name

def random_zone():
	random_zone = '{0}.{1}'.format(uts.random_string(), uts.random_string())
	return random_zone

def location():
	location = '0 1 2 {0}.{1}'.format(uts.random_name(), uts.random_name())
	return location

def random_reverse_zone():
	while True:
		ip_parts = [str(random.randrange(1, 254)) for i in range(3)]
		random_reverse_zone = '.'.join(ip_parts)
		try:
			utils.verify_ldap_object(random_reverse_zone)
		except:
			break
		else:
			pass
	return random_reverse_zone

def make_random_ip():
	while True:
		ip_parts = [str(random.randrange(1, 254)) for i in range(4)]
		randomIP = '.'.join(ip_parts)
		command = os.system('ping -c 1 {0} >/dev/null'.format(randomIP))
		if command == 0:
			pass
		else: 
			break
	return randomIP

def make_random_ipv6():
	ipv6 = random_hex()
	for i in range(7):
		ipv6 +=':'+(random_hex())
	return ipv6

def random_hex():
	result = []
	result = ''.join([random.choice('0123456789abcdef') for i in range(4)])
	return result

def check_group(group_dn, old_group_dn = None):
	s4 = s4connector.S4Connection()
	group_found = s4.exists(group_dn)
	if not old_group_dn:
		if group_found:
			print ("Group synced to Samba")
		else:
			sys.exit("Groupname not synced")
	else:
		old_group_gone = not s4.exists(old_group_dn)
		if group_found and old_group_gone:
			print ("Group synced to Samba")
		else:
			sys.exit("Groupname not synced")


def check_user(user_dn, surname = None, old_user_dn = None):
	s4 = s4connector.S4Connection()
	user_dn_modified = modify_user_dn(user_dn)
	user_found = s4.exists(user_dn_modified)
	if not surname:
		if user_found:
			print ("User synced to Samba")
		else:
			sys.exit("Username not synced")
	elif surname:
		user_dn_modified_surname = get_user_surname(user_dn)
		old_user_dn_modified = modify_user_dn(old_user_dn)
		old_user_gone = not s4.exists(old_user_dn_modified)
		if old_user_gone and user_found and user_dn_modified_surname == surname:
			print ("User synced to Samba")
		else:
			sys.exit("Username not synced")

def get_user_surname(user_dn):
	s4 = s4connector.S4Connection()
	user_dn_modified = modify_user_dn(user_dn)
	surname = s4.get_attribute(user_dn_modified,'sn')
	return surname

def modify_user_dn(user_dn):
	user_dn_modified = 'cn' + user_dn[3:]
	return user_dn_modified


def correct_cleanup(group_dn, groupname2, udm_test_instance, return_new_dn = False):
	tmp = group_dn.split(',')
	modified_group_dn = 'cn={0},{1},{2},{3}'.format(groupname2, tmp[1], tmp[2], tmp[3])
	udm_test_instance._cleanup['groups/group'].append(modified_group_dn)
	if return_new_dn:
		return modified_group_dn

def verify_users(group_dn,users):
	print (" Checking Ldap Objects")
	utils.verify_ldap_object(group_dn, {
	'uniqueMember': [user for user in users],
	'memberUid': [(user.split('=')[1]).split(',')[0] for user in users]
	})

def modify_username(user_dn, new_user_name, udm_instance):
	newdn = 'uid=%s,%s' % (new_user_name, user_dn.split(",", 1)[1])
	udm_instance._cleanup['users/user'].append(newdn)
	udm_instance.modify_object('users/user', dn = user_dn, username = new_user_name)
	return newdn
