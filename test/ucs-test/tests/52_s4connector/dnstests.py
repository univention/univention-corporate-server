import univention.testing.strings as uts
import univention.testing.utils as utils
import subprocess
import re
import random
import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()
ucr.load()
import os
import sys
from time import sleep


MATCH_ATTEMPTS = 10  # number of 'dig' attempts to be done, see Bug #38288


def check_ldap_object(item, item_name, item_attribute = None, name_string = None):
	print (" Testing Ldap object : {0}			".format(item_name)),
	try:
		if item_attribute:
			utils.verify_ldap_object(item, {item_attribute:[name_string]})
		else:
			utils.verify_ldap_object(item)
	except:
		print (' Failed')
		print ('Verification of Ldap object failed ')
		sys.exit(1)
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
	#leading zeros will not be displayed in dig output so test_object has to be
	#manipulated accordingly or test will fail even with correct sync
	test_object_parts=test_object.split(':')
	new_test_object_parts=[]
	for part in test_object_parts:
		while part[0] == '0':
			part = part[1:]
		new_test_object_parts.append(part)
	test_object=(':').join(new_test_object_parts)
	print test_object
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
		dig_cmd = ("dig", zone_name, typ, '+noall', '+answer')
	else:
		dig_cmd = ("dig", param, zone_name, typ, '+noall', '+answer')

	for attempt in range(MATCH_ATTEMPTS):
		dig_subprocess = subprocess.Popen(dig_cmd, shell = False, stdout = subprocess.PIPE).communicate()
		dig_answer = dig_subprocess[0].splitlines()

		print ("\nDig Output :")
		for line in dig_answer:
			print line
			if re.match(re_test_object, line):
				print("\nOK: DNS synced\n")
				return

		print("\n  DNS not synced yet, making another dig attempt in 1 sec.")
		sleep(1)

	print("\nFAIL: DNS still not synced, made %s dig attempts " % MATCH_ATTEMPTS)
	sys.exit(1)


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
