$ErrorActionPreference = "Stop"

$d = [adsi]"LDAP://%(domain)s"
$d.PSBase.UserName = "%(domain_user)s"
$d.PSBase.Password = "%(domain_password)s"

$searcher = New-Object System.DirectoryServices.DirectorySearcher($d)
$searcher.PageSize = 1000
$searcher.filter = "(sAMAccountName=%(user_name)s)"
$Result = $searcher.FindOne()
If ($Result -ne $Null) {
	$user = $Result.GetDirectoryEntry()
	$user.SetPassword("%(user_password)s")
	exit 0
}

exit 1
