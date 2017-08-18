ps = '''
$ErrorActionPreference = "Stop"

$d = [adsi]"LDAP://%(domain)s"

$searcher = New-Object System.DirectoryServices.DirectorySearcher($d)
$searcher.PageSize = 1000
$searcher.filter = "%(filter)s"
$Results = $searcher.FindAll()
foreach ($objResult in $Results) {
	$objItem = $objResult.Properties
	$objItem
}
'''
name = 'search-ad'
description = 'search ad'
args = dict(
	domain=dict(help='the windows domain name'),
	filter=dict(help='search filter'),
)
