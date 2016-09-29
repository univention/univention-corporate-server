Param(
# arguments:
# domainname, gpo name, server name
        [string]$domain,
	[string]$gpo_name,
	[string]$server
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
	exit(1)
}

########
# MAIN #
########

## Work around annoying automatic line wrap:
$host.UI.RawUI.BufferSize = new-object System.Management.Automation.Host.Size(4096,50)

$global:Now = Set-PSBreakpoint -Variable Now -Mode Read -Action { $global:Now = Get-Date }

if (!(gwmi win32_computersystem).partofdomain -eq $true) {
	error("I am not joined")
}

Import-Module grouppolicy
try {
	if ($server -ne "") {
		Get-GPOReport `
			-Name "$gpo_name" `
			-ReportType "Xml" `
			-Domain "$domain" `
			-Server "$server" `
	} else {
		Get-GPOReport `
			-Name "$gpo_name" `
			-ReportType "Xml" `
			-Domain "$domain" `
	}
}
Catch {
	error("$_")
}

exit(0)
