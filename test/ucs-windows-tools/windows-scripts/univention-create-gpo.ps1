Param(
# arguments:
# domainname, gpo name, server name, comment
        [string]$domain,
	[string]$gpo_name,
	[string]$comment,
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
		New-GPO `
			-Name "$gpo_name" `
			-Comment "$comment" `
			-Domain "$domain" `
			-Server "$server" `
	} else {
		New-GPO `
			-Name "$gpo_name" `
			-Comment "$comment" `
			-Domain "$domain" `
	}
}
Catch {
	error("$_")
}

exit(0)
