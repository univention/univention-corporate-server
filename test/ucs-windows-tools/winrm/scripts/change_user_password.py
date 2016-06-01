ps = '''
$ErrorActionPreference = "Stop"

$d = [adsi]"LDAP://%(domain)s"
$d.PSBase.UserName = "%(domainuser)s"
$d.PSBase.Password = "%(domainpassword)s"

$searcher = New-Object System.DirectoryServices.DirectorySearcher($d)
$searcher.PageSize = 1000
$searcher.filter = "(sAMAccountName=%(username)s)"
$Result = $searcher.FindOne()
If ($Result -ne $Null) {
	$user = $Result.GetDirectoryEntry()
	$user.SetPassword("%(userpassword)s")
	exit 0
}

exit 1
'''
name = 'change_user_password'
description = 'change user password'
args = dict(
	username = dict(help='change password for this user'),
	userpassword = dict(help='the password string'),
	domain = dict(help='the windows domain name'),
	domainuser = dict(help='username to use for the join'),
	domainpassword = dict(help='username to use for the join'),
)
