Param(
[string]$domain,
[string]$domainMode,
[string]$forestMode,
[string]$password = "Univention.99"
)

$domainNetBios = $domain.Split(".")[0].ToUpper()
$base = "DC=" + $($domain.split(".") -join ",DC=")

Import-Module Servermanager
Add-WindowsFeature AD-Domain-Services
Add-WindowsFeature DNS
Add-WindowsFeature RSAT-ADDS
Add-WindowsFeature RSAT-DNS-Server

function promoWithDCpromo () {
	"dcpromo.exe"
	# TODO
}

function promoWithADDSDeployment ($domain, $domainMode, $forestMode, $password, $domainNetBios) {
	"ADDSDeployment"
	Import-Module ADDSDeployment
	Install-ADDSForest `
		-CreateDnsDelegation:$false `
		-DatabasePath 'C:\Windows\NTDS' `
		-DomainMode "$domainMode" `
		-DomainName "$domain" `
		-DomainNetbiosName "$domainNetBios" `
		-ForestMode "$forestMode" `
		-InstallDns:$true `
		-LogPath 'C:\Windows\NTDS' `
		-NoRebootOnCompletion:$false `
		-SysvolPath 'C:\Windows\SYSVOL' `
		-Force:$true `
		-SafeModeAdministratorPassword (ConvertTo-SecureString -String "$password" -AsPlainText -Force)
}

if (Get-Module -ListAvailable | Where-Object { $_.name -eq "ADDSDeployment" }) {
	promoWithADDSDeployment `
		-domain "$domain" `
		-domainMode "$domainMode" `
		-forestMode "$forestMode" `
		-password "$password" `
		-domainNetBios "$domainNetBios" 
}
else {
	promoWithDCpromo `
		-domain "$domain" `
		-domainMode "$domainMode" `
		-forestMode "$forestMode" `
		-password "$password" `
		-domainNetBios "$domainNetBios"
}
