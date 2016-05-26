[CmdletBinding()]
param(
$Path = (Get-Location),
[switch]$Reboot, 
[switch]$ScanOnly = $true, 
[string]$ProxyAddress,
[String[]][ValidateSet("Critical","Definition", "Drivers", "FeaturePacks", "Security", "ServicePacks", "Tools", "UpdateRollups", "Updates", "Microsoft", "ALL")]$UpdateTypes

)
    $AvailableUpdates = @()
    $UpdateIds = @()
    $UpdateTypes

    Write-Host "Checking for elevation... " -NoNewline
    $CurrentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    if (($CurrentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) -eq $false){
        $ArgumentList = "-noprofile -noexit -file `"{0}`" -Path `"$Path`""
        If ($ScanOnly) {$ArgumentList = $ArgumentList + " -ScanOnly"}
        If ($reboot) {$ArgumentList = $ArgumentList + " -Reboot"}
        If ($ProxyAddress){$ArgumentList = $ArgumentList + " -ProxyAddress $ProxyAddress"}
        If ($UpdateTypes) {$ArgumentList = $ArgumentList + " -UpdateTypes $UpdateTypes"}

    Write-Host "elevating"
    Start-Process powershell.exe -Verb RunAs -ArgumentList ($ArgumentList -f ($myinvocation.MyCommand.Definition))

    Write-Host "Exiting, please refer to console window" -ForegroundColor DarkRed
        break
        }

    if ($Reboot) {
        Write-Host "The computer will reboot if needed after installation is complete."
        Write-Host
    }
    if ($ScanOnly) {
        Write-Host "Running in scan only mode."
        Write-Host
    }

    Write-Verbose "Creating Update Session"
    $Session = New-Object -com "Microsoft.Update.Session"


    if ($ProxyAddress -ne $null) {
    Write-Verbose "Setting Proxy"
        $Proxy = New-Object -com "Microsoft.Update.WebProxy"
        $Session.WebProxy.Address = $Proxyaddress
        $Session.WebProxy.AutoDetect = $FALSE
        $Session.WebProxy.BypassProxyOnLocal = $TRUE
    }

    Write-Verbose "Creating Update Type Array"
    foreach($UpdateType in $UpdateTypes)
    {
        $UpdateID
        switch ($UpdateType)
        {
        "Critical" {$UpdateID = 0}
        "Definition"{$UpdateID = 1}
        "Drivers"{$UpdateID = 2}
        "FeaturePacks"{$UpdateID = 3}
        "Security"{$UpdateID = 4}
        "ServicePacks"{$UpdateID = 5}
        "Tools"{$UpdateID = 6}
        "UpdateRollups"{$UpdateID = 7}
        "Updates"{$UpdateID = 8}
        "Microsoft"{$UpdateID = 9}
        default {$UpdateID=99}
        }
        $UpdateIds += $UpdateID
    }

    Write-Host "Searching for updates..."
    $Search = $Session.CreateUpdateSearcher()
    $SearchResults = $Search.Search("IsInstalled=0 and IsHidden=0")
    Write-Host "There are " $SearchResults.Updates.Count "TOTAL updates available."

    if($UpdateIds -eq 99)
    {
        $AvailableUpdates = $SearchResults.Updates
    }
    else{
        
        foreach($UpdateID in $UpdateIds)
        {
            $AvailableUpdates += $SearchResults.RootCategories.Item($UpdateID).Updates
        }
    }

    Write-Host "Updates selected for installation"
    $AvailableUpdates | ForEach-Object {
    
        if (($_.InstallationBehavior.CanRequestUserInput) -or ($_.EulaAccepted -eq $FALSE)) {
            Write-Host $_.Title " *** Requires user input and will not be installed." -ForegroundColor Yellow
        }
        else {
            Write-Host $_.Title -ForegroundColor Green
        }
    }

    # Exit script if no updates are available
    if ($ScanOnly) {
        Write-Host "Exiting...";
        break
    }
    if($AvailableUpdates.count -lt 1){
        Write-Host "No results meet your criteria. Exiting";
        break
    }
    
    Write-Verbose "Creating Download Selection"
    $DownloadCollection = New-Object -com "Microsoft.Update.UpdateColl"

    $AvailableUpdates | ForEach-Object {
        if ($_.InstallationBehavior.CanRequestUserInput -ne $TRUE) {
            $DownloadCollection.Add($_) | Out-Null
            }
        }

    Write-Verbose "Downloading Updates"
    Write-Host "Downloading updates..."
    $Downloader = $Session.CreateUpdateDownloader()
    $Downloader.Updates = $DownloadCollection
    $Downloader.Download()

    Write-Host "Download complete."

    Write-Verbose "Creating Installation Object"
    $InstallCollection = New-Object -com "Microsoft.Update.UpdateColl"
    $AvailableUpdates | ForEach-Object {
	    if ($_.IsDownloaded) {
		    $InstallCollection.Add($_) | Out-Null
        }
    }

    Write-Verbose "Installing Updates"
    Write-Host "Installing updates..."
    $Installer = $Session.CreateUpdateInstaller()
    $Installer.Updates = $InstallCollection
    $Results = $Installer.Install()
    Write-Host "Installation complete."
    Write-Host


    # Reboot if needed
    if ($Results.RebootRequired) {
        if ($Reboot) {
            Write-Host "Rebooting..."
            Restart-Computer ## add computername here
        }
        else {
	        Write-Host "Please reboot."
        }
    }
    else {
	    Write-Host "No reboot required."
    }
