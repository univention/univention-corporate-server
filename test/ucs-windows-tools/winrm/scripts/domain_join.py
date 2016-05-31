ps = '''
$ErrorActionPreference = "Stop"

$password =  "%(domainpassword)s"| ConvertTo-SecureString -asPlainText -Force
$domain = "%(domain)s"
$username = "%(domain)s\%(domainuser)s" 
$credential = New-Object System.Management.Automation.PSCredential($username,$password)
Add-Computer -DomainName $domain -Credential $credential
'''
name = 'domain_join'
description = 'Join windows client into domain'
args = dict(
	dnsserver = dict(help='DNS Server to use for join'),
	domain = dict(help='the windows domain name'),
	domainuser = dict(help='username to use for the join'),
	domainpassword = dict(help='username to use for the join'),
)

def pre(winrm):
	winrm.set_dns_server(**vars(winrm.args))
	winrm.disable_firewall(state='off')

def post(winrm):
	winrm.reboot()
	#winrm.wait_until_client_is_gone()
	#winrm.wait_for_client()
	winrm.domain_user_validate_password(**vars(winrm.args))
