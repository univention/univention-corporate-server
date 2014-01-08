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

def wait_for_sync(multiplier=1):
	synctime = int(ucr.get("connector/s4/poll/sleep",7))
	synctime = (synctime +3)*multiplier
	print ("Waiting {0} seconds for sync...".format(synctime))
	sleep (synctime)

def check_ldap_object(item,item_name,item_attribute=None,name_string=None):
	print (" Testing Ldap object : {0}			".format(item_name)),
	if os.isatty:
		(col,nocol) = ("\033[31m","\033[0m")
	else:
		(col,nocol) = ("","")
	try:
		if item_attribute:
			utils.verify_ldap_object(item, {item_attribute:[name_string]})
		else:
			utils.verify_ldap_object(item)
	except:
		print ('{0} Failed {1}'.format(col,nocol))
		raise Exception('{0} Verification of Ldap object failed {1}'.format(col,nocol))
	else:
		if os.isatty:
			col = ("\033[32m")
		print('{0} Success {1}'.format(col,nocol))


def test_dns_forward_zone(zone_name,test_object,debug=False):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+NS\s+\"*{1}\"*'.format(zone_name,test_object))
	match(re_test_object,zone_name,'NS',debug)

def test_dns_txt(zone_name,test_object,debug=False):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+TXT\s+\"*{1}\"*'.format(zone_name,test_object))
	match(re_test_object,zone_name,'TXT',debug)


def test_dns_ttl(zone_name,test_object,debug=False):
	re_test_object=re.compile(r"{0}\.*\s+{1}\s+IN\s+SOA".format(zone_name,test_object))
	match(re_test_object,zone_name,'SOA',debug)

def test_dns_reverse_zone(zone_name,test_object,debug=False):
	temp = zone_name.split('.')
	zone_namereverse = temp[2]+'.'+temp[1]+'.'+temp[0]
	re_test_object=re.compile(r"{0}.in-addr.arpa.\s+\d+\s+IN\s+NS\s+{1}".format(zone_namereverse,test_object))
	match(re_test_object,zone_name,'NS',debug,'-x')

def test_dns_serial(zone_name,test_object,debug=False):
	if debug:
		print ("Ldap serial : %s"%test_object)
	re_test_object=re.compile(r"{0}\.*\s+\d+\s+IN\s+SOA\s+.+\s+.+\s+{1}\s+".format(zone_name, test_object))
	match(re_test_object,zone_name,'SOA',debug)

def test_dns_a_record(zone_name,test_object,debug=False):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+A\s+\"*{1}\"*'.format(zone_name,test_object))
	match(re_test_object,zone_name,'A',debug)

def test_dns_aaaa_record(zone_name,test_object,debug=False):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+AAAA\s+\"*{1}\"*'.format(zone_name,test_object))
	match(re_test_object,zone_name,'AAAA',debug)

def test_dns_alias(zone_name,test_object,debug=False):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+CNAME\s+\"*{1}\"*'.format(zone_name,test_object))
	match(re_test_object,zone_name,'CNAME',debug)

def test_dns_service_record(zone_name,test_object,debug=False):
	re_test_object=re.compile(r'{0}\.*\s+\d+\s+IN\s+SRV\s+\"*{1}\"*'.format(zone_name,test_object))
	match(re_test_object,zone_name,'SRV',debug)




def match(re_test_object,zone_name,typ,debug,param=None):

	if not param:
		dig_subprocess = subprocess.Popen(["dig", zone_name, typ,'+noall','+answer'],shell=False, stdout=subprocess.PIPE).communicate()
	else:
		dig_subprocess = subprocess.Popen(["dig", param, zone_name, typ,'+noall','+answer'],shell=False, stdout=subprocess.PIPE).communicate()
	dig_answer = dig_subprocess[0].splitlines()

	found_test_object_match = False
	for line in dig_answer:
		if debug:
			print line
		if re.match(re_test_object,line):
			found_test_object_match = True
	if os.isatty:
		(col,nocol) = ("\033[32m","\033[0m")
	if found_test_object_match:
		print("{0}  DNS synced {1}".format(col,nocol))
	else:
		if os.isatty:
			col = col = ("\033[31m")
		raise Exception ("{0}  DNS not synced {1}".format(col,nocol))


def get_hostname():
	host = ucr.get("ldap/master")
	return host

def random_name():
	random_name = '{0} tcp {1}'.format(uts.random_name(),uts.random_name())
	return random_name

def random_zone():
	random_zone = '{0}.{1}'.format(uts.random_string(), uts.random_string())
	return random_zone

def location():
	location = '0 1 2 {0}.{1}'.format(uts.random_name(), uts.random_name())
	return location

def random_reverse_zone():
	while True:
		random_reverse_zone = '{0}.{1}.{2}'.format(random.randrange(1,254), random.randrange(1,254) ,random.randrange(1,254))
		try:
			utils.verify_ldap_object(random_reverse_zone)
		except:
			break
		else:
			pass
	return random_reverse_zone

def make_random_ip():
	while True:
		part1 = random.randrange(1,254)
		part2 = random.randrange(1,254)
		part3 = random.randrange(1,254)
		part4 = random.randrange(1,254)
		randomIP = '{0}.{1}.{2}.{3}'.format(part1,part2,part3,part4)
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

