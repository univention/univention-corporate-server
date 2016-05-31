ps = '''
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.DirectoryServices.AccountManagement
 
$UserName = "%(domainuser)s"
$Password = "%(domainpassword)s"
$Domain = "%(domain)s"
 
$ct = [System.DirectoryServices.AccountManagement.ContextType]::Domain
$pc = New-Object System.DirectoryServices.AccountManagement.PrincipalContext $ct,$Domain
if (! $pc.ValidateCredentials($UserName,$Password)) {
    Throw "user not valid"
}
'''

name = 'domain_user_validate_password'
description = 'validate domain users password'
args = dict(
	domain = dict(help='the windows domain name'),
	domainuser = dict(help='the username'),
	domainpassword = dict(help='the users expected password'),
)
