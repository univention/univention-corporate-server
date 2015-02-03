Param(
# arguments:
        [string]$domain,
        [string]$gpo_name,  # GpoName (aka DisplayName)
        [string]$permission_level,  # GpoRead|GpoApply|GpoEdit|GpoEditDeleteModifySecurity|None
        [string]$target_name,  # Object in LDAP
        [string]$target_type,  # Computer|User|Group
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

    try {
            Set-GPPermissions `
                -Name "$gpo_name" `
                -PermissionLevel "$permission_level" `
                -TargetName "$target_name" `
                -TargetType "$target_type" `
                -Domain "$domain" `
                -Server "$server" `
}
    Catch {
            error("$_")
    }

exit(0)
