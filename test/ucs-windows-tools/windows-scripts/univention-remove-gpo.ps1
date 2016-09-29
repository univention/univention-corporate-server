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

$global:Now = Set-PSBreakpoint -Variable Now -Mode Read -Action { $global:Now = Get-Date }

if (!(gwmi win32_computersystem).partofdomain -eq $true) {
	error("I am not joined")
}

Import-Module grouppolicy
try {
	if ($server -ne "") {
		Remove-GPO `
			-Name "$gpo_name" `
			-Domain "$domain" `
			-Server "$server" `
	} else {
		Remove-GPO `
			-Name "$gpo_name" `
			-Domain "$domain" `
	}
}
Catch {
	error("$_")
}

exit(0)
