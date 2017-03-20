Param(
[string]$domain,
[string]$domainMode,
[string]$forestMode,
[string]$password = "Univention.99"
)

##################
# error handling #
##################

$ErrorActionPreference = "Stop"

# for external commands
trap {
	Write-Error $_
	exit 1
}

#############
# functions #
#############

function error ($msg) {
	Write-Host "[$Now] $msg" -ForegroundColor Red
	Exit(1)
}

function mapMode ($mode) {
	# forest/domain level
	# 0 -> 2000
	# 2 -> 2003
	# 3 -> 2008
	# 4 -> 2008R2
	if ($mode.ToUpper() -eq "WIN2000") {
		return 0
	}
	elseif ($mode.ToUpper() -eq "WIN2003") {
		return 2
	}
	elseif ($mode.ToUpper() -eq "WIN2008") {
		return 3
	}
	elseif ($mode.ToUpper() -eq "WIN2008R2") {
		return 4
	}
	error("unknown forest/domain mode $mode")
}

function promoWithDCpromo ($domain, $domainMode, $forestMode, $password, $domainNetBios) {
	Write-Host "dcpromo.exe"

	# forest/domain level
	# 0 -> 2000
	# 2 -> 2003
	# 3 -> 2008
	# 4 -> 2008R2

	$forestMode = mapMode($forestMode)
	$domainMode = mapMode($domainMode)

	"[DCINSTALL]" > c:\dcpr.txt
	"InstallDNS=yes" >> c:\dcpr.txt
	"NewDomain=forest" >> c:\dcpr.txt
	"NewDomainDNSName=$domain" >> c:\dcpr.txt
	"DomainNetBiosName=$domainNetBios" >> c:\dcpr.txt
	"ReplicaOrNewDomain=domain" >> c:\dcpr.txt
	"ForestLevel=$forestMode" >> c:\dcpr.txt
	"DomainLevel=$domainMode" >> c:\dcpr.txt
	"RebootOnCompletion=yes" >> c:\dcpr.txt
	"SafeModeAdminPassword=$password" >> c:\dcpr.txt

	dcpromo /unattend:c:\dcpr.txt
}

function promoWithADDSDeployment ($domain, $domainMode, $forestMode, $password, $domainNetBios) {
	try {
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
	Catch {
		error("Exception occurred while promoting ad: $_")
	}
}

########
# MAIN #
########

$domainNetBios = $domain.Split(".")[0].ToUpper()
$base = "DC=" + $($domain.split(".") -join ",DC=")
$global:Now = Set-PSBreakpoint -Variable Now -Mode Read -Action { $global:Now = Get-Date }

try {
	Import-Module Servermanager
}
Catch {
	# error("$_")
	promoWithDCpromo `
		-domain "$domain" `
		-domainMode "$domainMode" `
		-forestMode "$forestMode" `
		-password "$password" `
		-domainNetBios "$domainNetBios"
}

if ((gwmi win32_computersystem).partofdomain -eq $true) {
	error("i am already joined")
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

exit(0)
