Param(
	[string]$domain
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

function installFeature ($feature) {
	Try {
		$result = Add-WindowsFeature "$feature"
		If (! $Result.Success) {
			error("$feature could not be installed!")
		}
	}
	Catch {
		error("Exception occurred while installing ${feature}: $_")
	}
}

########
# MAIN #
########

$global:Now = Set-PSBreakpoint -Variable Now -Mode Read -Action { $global:Now = Get-Date }
$domainNetBios = $domain.Split(".")[0].ToUpper()
$base = "DC=" + $($domain.split(".") -join ",DC=")
$caname = $domainNetBios + "-" + $(hostname) + "-CA"

try {
	Import-Module Servermanager
}
Catch {
	error("$_")
}

if (!(gwmi win32_computersystem).partofdomain -eq $true) {
	error("i am not joined")
}

installFeature("AD-Certificate")
installFeature("RSAT-ADCS-Mgmt")

if (Get-Command -Module ADCSDeployment | Where-Object { $_.name -eq "Install-AdcsCertificationAuthority" }) {
	try {
		Install-AdcsCertificationAuthority `
			-OverwriteExistingKey `
			-CAType EnterpriseRootCA `
			-ValidityPeriod Years `
			-ValidityPeriodUnits 5 `
			-CACommonName "$caname" `
			-CADistinguishedNameSuffix "$base" `
			-DatabaseDirectory c:\CertDB `
			-OverwriteExistingDatabase `
			-LogDirectory c:\CertLog `
			-Force
	}
	Catch {
		error("$_")
	}
}
else {
	try {
		. c:\univention-install-certification-authority.ps1
		Install-CertificationAuthority `
			-CAType "Enterprise Root" `
			-OverwriteExisting `
			-ValidForYears 5 `
			-CADNSuffix "$base" `
			-CAName "$caname" `
			-Force
	}
	Catch {
		error("$_")
	}
}

exit(0)
