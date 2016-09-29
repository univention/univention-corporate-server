Param(
# arguments:
# domainname, gpo name, order, target, server name
        [string]$domain,
	[string]$gpo_name,
	[int]$order,
	[string]$target,
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
		New-GPLink `
			-Name "$gpo_name" `
			-Order "$order" `
			-Target "$target" `
			-Domain "$domain" `
			-Server "$server" `
	} else {
		New-GPLink `
			-Name "$gpo_name" `
			-Order "$order" `
			-Target "$target" `
			-Domain "$domain" `
	}
}
Catch {
	error("$_")
}

exit(0)
