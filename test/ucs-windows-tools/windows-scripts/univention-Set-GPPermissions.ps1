Param(
# arguments:
        [string]$domain,
        [string]$gpo_name,  # GpoName (aka DisplayName)
        [string]$permission_level,  # GpoRead|GpoApply|GpoEdit|GpoEditDeleteModifySecurity|None
        [string]$target_name,  # Object in LDAP
        [string]$target_type,  # Computer|User|Group
        [string]$replace, # force GpoPermissions overwrite True|False
	[string]$server   # Domain controller
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
		Set-GPPermissions `
			-Name "$gpo_name" `
			-PermissionLevel "$permission_level" `
			-TargetName "$target_name" `
			-TargetType "$target_type" `
			-Domain "$domain" `
			-Replace:([System.Convert]::ToBoolean($replace)) `
			-Server "$server" `
	} else {
		Set-GPPermissions `
			-Name "$gpo_name" `
			-PermissionLevel "$permission_level" `
			-TargetName "$target_name" `
			-TargetType "$target_type" `
			-Domain "$domain" `
			-Replace:([System.Convert]::ToBoolean($replace)) `
	}
}
Catch {
	error("$_")
}

exit(0)
