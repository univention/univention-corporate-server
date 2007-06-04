#!/usr/bin/python

import univention_baseconfig, time, os

baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()

if baseConfig['security/firewall/enable'] != "yes":
	print "Firewall is not enabled. Exiting."
	exit

def main():

	initscript = '/etc/univention-firewall/init.sh'
	
	# Important initialize
	# This is the data one firewall-service record consists of
	# After all data has been collected out of the baseconfig the
	# entry is written as iptables script
	oldservice = ''
	udp = {}
	tcp = {}
	allowip = []
	denyip = []
	log = ''
	policy = ''
	enable = ''

	# Open the main file
	fh = open_iptables_script(initscript)
	fh.write('$iptables -F\n\n')

	# Global TCP/UDP blocking also needs to be done in the loop
	# Now traverse the security/firewall/services/
	base = baseConfig.keys()
	base.sort()

	for key in base:
		value = baseConfig[key]
		#print "[%s]\t\t%s" % (key, value)

		# Seek for the ports
		if key.startswith('security/firewall/tcp/') or key.startswith('security/firewall/udp/'):
			tmp = key.split('/', 3)
			proto = tmp[2]
			port = tmp[3]
		
			# Only block as value is accepted!
			# As default policy is accept and this is about general
			# tcp/udp port blocking
			if value == "block":
				fh.write(add_iptables_entry(proto , port))
		
		# Welcome to the complex part, filtering out
		if key.startswith('security/firewall/services/'):
			key = key.replace('security/firewall/services/', '')
			(service, data) = key.split('/', 1)
			
			enable = baseConfig['security/firewall/services/'+service+'/enable']
			if baseConfig['security/firewall/services/'+service+'/enable'] != "yes":
				print "Firewall service disabled: " + service + '. Going on.'
				continue

			# We got a new service. Means, we can write the old, as we got all data
			# You can be sure about this, because sort() was called on baseConfig
			if oldservice and oldservice != service:
				
				write_service(oldservice, fh, enable, policy, log, tcp, udp, allowip, denyip)
				
				# Reset our values
				udp = {}
				tcp = {}
				allowip = []
				denyip = []
				log = ''
				policy = ''
				enable = ''
			
			# Else we need to collect more data
			else:
				# Logging rule
				if (data == 'logging' and value == 'yes'):
					log = 1
				
				if data == 'policy' and (value == 'accept' or value == 'deny'):
					policy = value

				if data.startswith('tcp/'):
					(tmp, port) = data.split('/', 1)
					tcp[port] = value

				if data.startswith('udp/'):
					(tmp, port) = data.split('/', 1)
					udp[port] = value
				
				if data.startswith('allowed/'):
					allowip.append(value)
				
				if data.startswith('denied/'):
					denyip.append(value)
			
			#print "Service: %s " % service
			#print "data: %s => %s " % (data, value)

			oldservice = service
		
		
	write_service(oldservice, fh, enable, policy, log, tcp, udp, allowip, denyip)

	# Close the main script
	fh.write('\n')
	fh.close()
	os.chmod(initscript, 0755);

### functions^Wmethods
def open_iptables_script (file):
	fh = open(file, 'w')
	fh.write('#!/bin/sh\n\n')
	fh.write('#\n# Written by univention-baseconfig at '+time.strftime('%H:%M   %d %b %Y')+' \n#\n\n')
	fh.write('iptables=$(which iptables)\n\n')
	return fh

# Add a IPTables entry to the INPUT chain
# iptables -A INPUT  -p tcp --dport 111 -j univention-thinclient
# call: add_iptables_entry('tcp', '111', 'thinclient')
# jump='' option whether we want to jump into a certain chain or block in INPUT
# disable='' if a ruleset is disabled, write it commented out anyway
def add_iptables_entry(proto, port, jump='', disable=''):
	if jump:
		jump = 'univention-%s' % jump
	else:
		if proto == 'tcp':
			jump = 'REJECT --reject-with tcp-reset'
		if proto == 'udp':
			jump = 'DROP'

	port = port.replace('-', ':', 1)

	return ('$iptables -A INPUT -p %s --dport %s -j %s\n' % (proto, port, jump))


# Add a new iptables chain
# iptables -N univention-thinclient
# call: add_iptables_chain('thinclient')
def add_iptables_chain(name):
	return ('$iptables -N univention-%s\n' % name)

# Adds a allow/reject rule to a service
# iptables -A univention-thinclient -s 10.200.32.128/25 -j ACCEPT
# call: add_iptables_service_entry('thinclient', '10.200.32.128/25', 'accept')
def add_iptables_service_entry(name, source, policy):
	return ('$iptables -A univention-%s -s %s -j %s\n' % (name, source, policy))

# Sets a default policy for a service (should be called last)
# iptables -A univention-thinclient -j REJECT --reject-with tcp-reset [-p tcp]
# call: set_iptables_default_policy('univention', 'reject')
def set_iptables_service_defaultpolicy(name, policy, tcp, udp):
	str = ''
	
	if policy == "deny":
		policy = "drop"
	
	if policy == "drop" and len(tcp) > 0:
		str += ('$iptables -A univention-%s -p tcp -j REJECT --reject-with tcp-reset\n' % name)
	
	return (str+'$iptables -A univention-%s -j %s\n' % (name, policy.upper()))

# This enables logging of packets which end ip in the default policy after
# traversing the chain
# iptables -A univention-thinclient -j LOG
# call: set_iptables_service_logging('thinclient')
def set_iptables_service_logging(name):
	return ('$iptables -A univention-%s -j LOG\n' % name)

# Write our service entry...
# Arguments are:
# 1. service       The name of the service, i.e. 'thinclient'
# 2. filehandle    The filehandle of the main init script
# 3. enable        The enable/disable status of the rule - won't be activated until explicitely set to 'yes'
# 4. policy        The default policy, should be 'deny' or 'accept'
# 5. log           Should this service be logged?
# 6. tcp [dict]    TCP ports this service affects (may be integer or common port name)
# 7. udp [dict]    UDP ports this service affects (may be integer or common port name)
# 8. allowip [arr] List of IPs (including netmask) which are allowed for this service
# 9. denyip [arr]  List of IPs (including netmask) which are denied for this service
def write_service(service, fh, enable, policy, log, tcp, udp, allowip, denyip):
	#print "write_service(%s, %s, %s, %s, %s, %s, %s, %s, %s)" % (service, fh, enable, policy, log, tcp, udp, allowip, denyip)
	script = '/etc/univention-firewall/'+service+'.sh'
	servicefh = open_iptables_script(script);
	
	# If enable is not set to yes, we only write the init scripts, but commented out
	if enable != "yes":
		cchar = '# '
	else:
		cchar = ''
	
	fh.write(cchar+add_iptables_chain(service));
	
	for elem in tcp:
		fh.write(cchar+add_iptables_entry('tcp', elem, service))
	
	for elem in udp:
		fh.write(cchar+add_iptables_entry('udp', elem, service))
	
	for elem in allowip:
		servicefh.write(cchar+add_iptables_service_entry(service, elem, 'ACCEPT'))

	for elem in denyip:
		servicefh.write(cchar+add_iptables_service_entry(service, elem, 'REJECT'))
	
	if log == 1:
		servicefh.write(cchar+set_iptables_service_logging(service))
	
	servicefh.write(cchar+set_iptables_service_defaultpolicy(service, policy, tcp, udp)+'\n')
	os.chmod(script, 0755);

	servicefh.close()

	# Schedule start of the service in the init.sh Script
	fh.write(cchar+'/etc/univention-firewall/'+service+'.sh\n');

# Set it off
main()
