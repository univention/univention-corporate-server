Param(
# arguments:
        [string]$domain,
        [string]$gpo_name,  # GpoName (aka DisplayName)
        [string]$reg_key,  # for ex: HKLM\Software\Policies\Microsoft\Windows NT\DNSClien
        [string]$value_name,  # a value name or array of value names
        [string]$value,  # a value(-s)
        [string]$type,  # Unknown|String|ExpandString|Binary|DWord|MultiString|QWord
        [string]$server  # Domain controller
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
		Set-GPRegistryValue `
			-Name "$gpo_name" `
			-Key "$reg_key" `
			-ValueName "$value_name" `
			-Value "$value" `
			-Type "$type" `
			-Domain "$domain" `
			-Server "$server" `
	} else {
		Set-GPRegistryValue `
			-Name "$gpo_name" `
			-Key "$reg_key" `
			-ValueName "$value_name" `
			-Value "$value" `
			-Type "$type" `
			-Domain "$domain" `
	}
}
Catch {
	error("$_")
}

exit(0)
