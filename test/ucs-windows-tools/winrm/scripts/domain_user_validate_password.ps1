$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.DirectoryServices.AccountManagement
 
$UserName = "%(domain_user)s"
$Password = "%(domain_password)s"
$Domain = "%(domain)s"
 
$ct = [System.DirectoryServices.AccountManagement.ContextType]::Domain
$pc = New-Object System.DirectoryServices.AccountManagement.PrincipalContext $ct,$Domain
if (! $pc.ValidateCredentials($UserName,$Password)) {
    Throw "user not valid"
}
