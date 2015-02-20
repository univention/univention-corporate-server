$status = (Get-WindowsFeature -Name gpmc).Installed

# if gpmc not installed, install binaries, otherwise do nothing
if (!$status) {$retn = Add-WindowsFeature -Name gpmc -ErrorAction Stop
        if (!$retn.Success) {
                Write-Error -Category NotInstalled -ErrorId "NotInstalledException" `
                -Message "Unable to install GPMC installation packages due of the following error: $($retn.breakCode)"
                exit(1)
        }
}
exit(0)
