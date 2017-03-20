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
installFeature("AD-Domain-Services")
installFeature("RSAT-DNS-Server")
installFeature("RSAT-ADDS")

exit(0)
