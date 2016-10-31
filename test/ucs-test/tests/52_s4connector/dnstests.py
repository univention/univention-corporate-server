import os
import sys
import time
import ldap
import univention.testing.strings as uts
import univention.testing.utils as utils
import subprocess
import re
import random
import univention.config_registry
ucr = univention.config_registry.ConfigRegistry()
ucr.load()


## Adding a DNS zone causes bind restart in postrun, so we may have to
## retry a couple of times:
MATCH_ATTEMPTS = 17  # number of 'dig' attempts to be done, see Bug #38288


def check_ldap_object(item, item_name, item_attribute=None, expected_values=None, should_exist=True):
	print (" Testing Ldap object : {0}			".format(item_name)),
	if not isinstance(expected_values, list):
		expected_values = [expected_values]
	try:
		if item_attribute:
			utils.verify_ldap_object(item, {item_attribute: expected_values}, should_exist=should_exist)
		else:
			utils.verify_ldap_object(item, should_exist=should_exist)
	except utils.LDAPError as exc:
		print (' Failed')
		print ('Verification of Ldap object failed: %s' % exc)
		sys.exit(1)
	else:
		print(' Success ')


def test_dns_ns(zone_name, test_object, should_exist=True):
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+NS\s+\"*{1}\"*'.format(*map(re.escape, (zone_name, test_object))))
	match(re_test_object, zone_name, 'NS', should_exist=should_exist)


def test_dns_txt(dns_name, test_object, should_exist=True):
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+TXT\s+\"*{1}\"*'.format(*map(re.escape, (dns_name, test_object))))
	match(re_test_object, dns_name, 'TXT', should_exist=should_exist)


def test_dns_soa_ttl(dns_name, test_object, should_exist=True):
	re_test_object = re.compile(r"{0}\.*\s+{1}\s+IN\s+SOA".format(*map(re.escape, (dns_name, test_object))))
	match(re_test_object, dns_name, 'SOA', should_exist=should_exist)


def test_dns_reverse_zone(zone_name, test_object, should_exist=True):
	temp = zone_name.split('.')
	zone_namereverse = temp[2] + '.' + temp[1] + '.' + temp[0]
	re_test_object = re.compile(r"{0}.in-addr.arpa.\s+\d+\s+IN\s+NS\s+{1}".format(*map(re.escape, (zone_namereverse, test_object))))
	match(re_test_object, zone_name, 'NS', '-x', should_exist=should_exist)


def test_dns_serial(zone_name, test_object, should_exist=True):
	re_test_object = re.compile(r"{0}\.*\s+\d+\s+IN\s+SOA\s+.+\s+.+\s+{1}\s+".format(*map(re.escape, (zone_name, test_object))))
	match(re_test_object, zone_name, 'SOA', should_exist=should_exist)


def test_dns_a_record(dns_name, test_object, should_exist=True):
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+A\s+\"*{1}\"*'.format(*map(re.escape, (dns_name, test_object))))
	match(re_test_object, dns_name, 'A', should_exist=should_exist)


def test_dns_aaaa_record(dns_name, test_object, should_exist=True):
	# leading zeros will not be displayed in dig output so test_object has to be
	# manipulated accordingly or test will fail even with correct sync
	test_object_parts = test_object.split(':')
	new_test_object_parts = []
	for part in test_object_parts:
		while part[0] == '0':
			part = part[1:]
		new_test_object_parts.append(part)
	test_object = (':').join(new_test_object_parts)
	print test_object
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+AAAA\s+\"*{1}\"*'.format(*map(re.escape, (dns_name, test_object))))
	match(re_test_object, dns_name, 'AAAA', should_exist=should_exist)


def test_dns_alias(dns_name, test_object, should_exist=True):
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+CNAME\s+\"*{1}\"*'.format(*map(re.escape, (dns_name, test_object))))
	match(re_test_object, dns_name, 'CNAME', should_exist=should_exist)


def test_dns_service_record(dns_name, test_object, should_exist=True):
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+SRV\s+\"*{1}\"*'.format(*map(re.escape, (dns_name, test_object))))
	match(re_test_object, dns_name, 'SRV', should_exist=should_exist)


def test_dns_pointer_record(reverse_zone, ip, test_object, should_exist=True):
	reverse_address = str(ip) + '.' + reverse_zone
	re_test_object = re.compile(r'{0}\.*\s+\d+\s+IN\s+PTR\s+\"*{1}\"*'.format(*map(re.escape, (reverse_address, test_object))))
	match(re_test_object, reverse_address, 'PTR', should_exist=should_exist)


def match(re_test_object, dns_name, typ, param=None, should_exist=True):

	if not param:
		dig_cmd = ("dig", dns_name, typ, '+noall', '+answer')
	else:
		dig_cmd = ("dig", param, dns_name, typ, '+noall', '+answer')

	## Adding a DNS zone causes bind restart in postrun, so we may have to
	## retry a couple of times
	for attempt in range(MATCH_ATTEMPTS):
		dig_subprocess = subprocess.Popen(dig_cmd, shell=False, stdout=subprocess.PIPE).communicate()
		dig_answer = dig_subprocess[0].splitlines()

		if not re_test_object and dig_answer:
			print("\nFAIL: Received DNS answer, expected none:\n%s", dig_answer)

		print ("\nDig Output :")
		for line in dig_answer:
			print line
			if should_exist and re.match(re_test_object, line):
				print("\nOK: DNS synced after %s seconds\n" % attempt)
				return
			elif not should_exist and not re.match(re_test_object, line):
				print("\nOK: DNS record removed after after %s seconds\n" % attempt)
				return

		print("\n  DNS not synced yet, making another dig attempt in 1 sec.")
		time.sleep(1)

	utils.fail("FAIL: DNS still not synced, made %s dig attempts " % MATCH_ATTEMPTS)


def get_hostname_of_ldap_master():
	host = ucr.get("ldap/master")
	return host


def random_srv_fields():
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
		ipv6 += ':' + (random_hex())
	return ipv6


def random_hex():
	result = []
	result = ''.join([random.choice('0123456789abcdef') for i in range(4)])
	return result


def fail_if_cant_resolve_own_hostname(max_attempts=17, delta_t_seconds=1):
		p = subprocess.Popen(["host", "%(hostname)s.%(domainname)s" % ucr])
		rc = p.wait()
		attempt = 1
		while rc != 0:
			if attempt > max_attempts:
				utils.fail("Cannot resolve own hostname after %s seconds" % max_attempts)
			sys.stdout.flush()
			time.sleep(delta_t_seconds)
			p = subprocess.Popen(["host", "%(hostname)s.%(domainname)s" % ucr])
			rc = p.wait()
			attempt += 1
		print "Resolved own hostname after %s seconds" % attempt


def udm_remove_dns_record_object(module, object_dn):
	superordinate = ",".join(ldap.explode_dn(object_dn)[1:])
	cmd = ['/usr/sbin/udm-test', module, 'remove', '--dn', object_dn, '--superordinate', superordinate]
	p = subprocess.Popen(cmd)
	rc = p.wait()

	return rc


def get_kerberos_ticket_for_machine():
	sys.stdout.flush()
	p = subprocess.Popen(["kdestroy"])
	rc = p.wait()

	principal_for_nsupdate = "%s$" % ucr["hostname"].upper()
	p = subprocess.Popen(["kinit", "-t", "/etc/krb5.keytab", principal_for_nsupdate])
	rc = p.wait()
	if rc != 0:
		utils.fail("kinit for %s failed" % principal_for_nsupdate)


def nsupdate(nsupdate_request):
	p = subprocess.Popen(["nsupdate", "-v", "-g"], stdin=subprocess.PIPE)
	(stdout, stderr) = p.communicate(input=nsupdate_request)
	if p.returncode != 0:
		utils.fail("nsupdate failed")
