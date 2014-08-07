function Install-CertificationAuthority {
<#
.Synopsis
    Installs Active Directory Certificate Services role on local computer.
.Description
    Installs Active Directory Certificate Services (AD CS) role on local computer. A user can choose different options, such
	Certification Authority (CA) type, key pair parameters, CA certificate validity and so on.
	
	The command supports Windows Server 2008 R2 Server Core installations.
.Parameter CAName
    Specifies a custom CA certificate name/subject (what you see in the certificate display UI). If not passed, a '<ComputerName>-CA'
	form is used for workgroup CAs and '<DomainName>-<ComputerName-CA>' form is used for domain CAs. The parameter supports Unicode names.
.Parameter CADNSuffix
	Specifies a DN suffix to specify some additional information. For example, company name, country, city, etc. DN suffix is empty for
	workgroup CAs and includes current domain distinguished name (for example, DC=domain,DC=com). The parameter accepts suffixes in a
	X500 form, for example: OU=Information Systems, O=Sysadmins LV, C=LV.
.Parameter CAType
	Specifies CA type:
	
	Standalone Root,
	Standalone Subordinate,
	Enterprise Root,
	Enterprise Subordinate.
	
	If not passed, for non-domain environments or if you don't have Enterprise Admins rights, Standalone Root is used. If you have
	Enterprise Admins rights and your forest already has installed CAs, Enterprise Subordinate is used. If no Enterprise CAs installed
	in the forest, Enterprise Root is used.
.Parameter ParentCA
	This parameter allows you to specify parent CA location only if you install Enterprise Subordinate CA. For other CA types, the
	parameter is ignored. Parent CA information must be passed in the following form: CAComputerName\CASanitizedName. Sanitized name
	is a sanitized form of CA name (subject). Mostly sanitized name is the same as CA name (unless you use Unicode and/or special
	characters, that are disallowed in X500). If the parameter is not specified, a certificate request will be generated on the root
	of system drive. I've decided to not implement this parameter for Standalone Subordinate CAs, because mostly they are installed
	in a workgroup environments and direct request submission to other CAs is likely unavailable (due of computer authentication
	complexity in the non-domain environments). However, if you need it — contact me.
.Parameter CSP
	Specifies custom cryptographic service provider. By default 'RSA#Microsoft Software Key Storage Provider' is used (in most cases
	you will use default CSP). You need to explicitly specify custom CSP only when you setup completely CNG authority (CSPs with ECDSA
	prefix) or you use HSM. Each HSM uses it's own custom CSP. You must install HSM middleware before CA installation.

	The full list of supportable and available "by default" CSPs for Windows Server 2008+ is:

	Microsoft Base Cryptographic Provider v1.0
	Microsoft Base DSS Cryptographic Provider
	Microsoft Base Smart Card Crypto Provider
	Microsoft Enhanced Cryptographic Provider v1.0
	Microsoft Strong Cryptographic Provider
	RSA#Microsoft Software Key Storage Provider
	DSA#Microsoft Software Key Storage Provider
	ECDSA_P256#Microsoft Software Key Storage Provider
	ECDSA_P384#Microsoft Software Key Storage Provider
	ECDSA_P521#Microsoft Software Key Storage Provider
	RSA#Microsoft Smart Card Key Storage Provider
	ECDSA_P256#Microsoft Smart Card Key Storage Provider
	ECDSA_P384#Microsoft Smart Card Key Storage Provider
	ECDSA_P521#Microsoft Smart Card Key Storage Provider
.Parameter KeyLength
	This parameter specifies the key length. If not specified, a 2048-bit key will be generated. There is a little trick: if you look to
	a CSP list (above), you will see that key length is specified for each ECDSA* provider. I've developed a script logic in that way,
	so the script ignores this parameter if one of ECDSA* CSP is explicitly chosen and uses key length that is supported by the CSP.
	Therefore you will not receive an error if you select 'ECDSA_P256#Microsoft Smart Card Key Storage Provider' CSP with 2048 key length.
	256-bit key will be selected automatically
.Parameter HashAlgorithm
	This parameter specifies hash algorithm that will be used for CA certificate/request hashing. Note that this is important for root
	CA installations. Subordinate CA certificates are hashed and signed by the parent CA with it's own settings. By default 'SHA1' is
	used (though this parameter is applicable for all CA installation types).
.Parameter ValidForYears
	Specifies the validity for root CA installations. By default root CA certificates are valid for 5 years. You can increase this value
	to 10, 20, 50, whatever you need. For any subordinate CA types this parameter is silently ignored. This is because subordinate CA
	validity is determined by the parent CA. This parameter accepts integer values, assuming that the value is specified in years.
.Parameter RequestFileName
	If you setup any sort of subordinate (not root) CAs you can specify custom path to a request file. By default request file is
	generated on the root of system drive.
.Parameter CACertFile
	Specifies the path to a PFX file with CA certificate. Relative paths are allowed. Setup API performs additional checks for the certificate.
	Therefore you must ensure if: this is CA certificate (but not EFS encryption ;)), CA certificate is trusted (for non-root certificates)
	and chains to trusted CA and CA certificate revocation checking can be performed. Otherwise you will unable to setup CA with that CA certificate.
.Parameter Password
	Specifies the password to open PFX file. The parameter supports only securestrings! You can't type a password as a simple text. This is made for
	security reasons. There are few ways to pass a password in a securestring form:

	$Password = Read-Host –a
	
	or

	ConvertTo-SecureString <plaintext> –a –f
	
	You can enclose last command in parentheses and pass directly as a parameter value.
.Parameter Thumbprint
	specifies a thumbprint of the certificate to use. The certificate must be installed in Local Machine\Personal store and must be trusted
	(for non-root certificates) and must not be revoked (the issuer revocation information must be available).
.Parameter DBDirectory
	Specifies the path to a folder to store CA database. If not specified, the default path: %windir%\System32\CertLog folder is used. If you
	need to specify custom path (for example, shared storage for CA clusters), you need to specify the next parameter too. The path must be valid.
.Parameter LogDirectory
	Specifies the path to a folderto store CA database log files. By default %windir%\System32\CertLog folder is used. If you use custom path for
	either database or log folders, you must explicitly specify both paths.
.Parameter OverwriteExisting
	Specifies, whether to overwrite any existing database files in the specified directories.
.Parameter AllowCSPInteraction
	Specifies, whether the cryptographic service provider (CSP) is allowed to interact with the desktop. This parameter should be used only if you
	use custom hardware-based CSP (HSM or smart card CSP). In other cases you don't need to allow CSP interactions.
.Parameter Force
	By default, the script explicitly prompts you whether you want to install Certification Authority with selected values. If you want to implement
	silent (quiet) installations — specify this parameter to suppress any prompts during role installation
.EXAMPLE
	PS > Install-CertificationAuthority -CAName "My Root CA" -CADNSuffix "OU=Information Systems, O=Sysadmins LV, C=LV" `
	-CAType "Standalone Root" -ValidForYears 10


	In this scenario you setup new Standalone Root CA with "CN=My Root CA, OU=Information Systems, O=Sysadmins LV, C=LV" subject, that will be valid
	for 10 years. The CA will use default paths to CA database and log files and certificate will use 'RSA#Microsoft Software Key Storage Provider'
	CSP with 2048-bit key and SHA1 hashing algorithm.
.EXAMPLE
	PS > Install-CertificationAuthority -CAName "My Root CA" -CADNSuffix "OU=Information Systems, O=Sysadmins LV, C=LV" `
	-CAType "Standalone Root" -ValidForYears 20 -CSP "ECDSA_P256#Microsoft Smart Card Key Storage Provider" `
	-HashAlgorithm SHA512

	This example is similar to previous, with the exception that this CA will be completely CNG/SHA2 root. CA certificate will use CNG (not RSA)
	keys and hashing algorithm will be SHA512.
.EXAMPLE
	PS > Install-CertificationAuthority -CAName "Clustered CA" -CADNSuffix "OU=Information Systems, O=Sysadmins LV, C=LV" `
	-CAType "Enterprise Subordinate" -KeyLength 4096 -DBDirectory "S:\CertDB" -LogDirectory "S:\CertLog" `
	-RequestFileName "S:\Clustered CA.req"

	This example assumes that you setup CA cluster first node (but not necessary). CA database will be stored on a shared storage (attached with S: drive letter).
	CA certificate will use default 'RSA#Microsoft Software Key Storage Provider' with 4096-bit key and default SHA1 hashing algorithm. CA certificate validity
	will be determined by the parent CA. In addition, CA certificate request will be stored on the shared storage.
.EXAMPLE
	PS > $Password = Read-Host -AsSecureString
	PS > Install-CertificationAuthority -CACertFile .\ClusteredCA.pfx -Password $Password `
	-DBDirectory "S:\CertDB" -LogDirectory "S:\CertLog" -OverwriteExisting

	This is two-line example. Say, you have successfully installed CA cluster first node and have exported CA certificate to a PFX, and moved it to the second
	node (to the current directory). At first you will be prompted for a password. Since you type password to a securestring prompt, no characters will be displayed.
	After that you will specify relative path to a PFX file and specify shared storage to store CA database and log files. You overwrite database files that was
	created during first node installation. Actually this command installs CA cluster second node.
.EXAMPLE
	PS > Install-CertificationAuthority -CAName "Company Enterprise CA-2" -CADNSuffix "O=Company, E=companypky@company.com" `
	-CAType "Enterprise Subordinate" -ParentCA "ca01.company.com\Company Enterprise CA-1"

	From best-practices perspective this is not a very good example, because it assumes at least 2 tiers of Enterprise CAs. However, it is still common. In a given
	example, Enterprise Subordinate CA will be installed and certificate request will be sent directly to existing Enterprise CA — 'Company Enterprise CA-1' that is
	hosted on 'ca01.company.com'. Note that existing CA must be online and must issue 'Subordinate Certification Authority' template.
.Inputs
	None.
.Outputs
	None.
.NOTES
	Author: Vadims Podans
	Blog  : http://en-us.sysadmins.lv
#>
[CmdletBinding(
	DefaultParameterSetName = 'NewKeySet',
	ConfirmImpact = 'High',
	SupportsShouldProcess = $true
)]
	param(
		[Parameter(ParameterSetName = 'NewKeySet')]
		[string]$CAName,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[string]$CADNSuffix,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[ValidateSet("Standalone Root","Standalone Subordinate","Enterprise Root","Enterprise Subordinate")]
		[string]$CAType,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[string]$ParentCA,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[string]$CSP,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[int]$KeyLength,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[string]$HashAlgorithm,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[int]$ValidForYears = 5,
		[Parameter(ParameterSetName = 'NewKeySet')]
		[string]$RequestFileName,
		[Parameter(Mandatory = $true, ParameterSetName = 'PFXKeySet')]
		[IO.FileInfo]$CACertFile,
		[Parameter(Mandatory = $true, ParameterSetName = 'PFXKeySet')]
		[Security.SecureString]$Password,
		[Parameter(Mandatory = $true, ParameterSetName = 'ExistingKeySet')]
		[string]$Thumbprint,
		[string]$DBDirectory,
		[string]$LogDirectory,
		[switch]$OverwriteExisting,
		[switch]$AllowCSPInteraction,
		[switch]$Force
	)

#region OS and existing CA checking
	# check if script running on Windows Server 2008 or Windows Server 2008 R2
	$OS = Get-WmiObject Win32_OperatingSystem -Property ProductType
	if ([Environment]::OSVersion.Version.Major -lt 6) {
		Write-Error -Category NotImplemented -ErrorId "NotSupportedException" `
		-Message "Windows XP, Windows Server 2003 and Windows Server 2003 R2 are not supported!"
		return
	}
	if ($OS.ProductType -eq 1) {
		Write-Error -Category NotImplemented -ErrorId "NotSupportedException" `
		-Message "Client operating systems are not supported!"
		return
	}
	$CertConfig = New-Object -ComObject CertificateAuthority.Config
	try {$ExistingDetected = $CertConfig.GetConfig(3)}
	catch {}
	if ($ExistingDetected) {
		Write-Error -Category ResourceExists -ErrorId "ResourceExistsException" `
		-Message "Certificate Services are already installed on this computer. Only one Certification Authority instance per computer is supported."
		return
	}
	
#endregion

#region Binaries checking and installation if necessary
	if ([Environment]::OSVersion.Version.Major -eq 6 -and [Environment]::OSVersion.Version.Minor -eq 0) {
		cmd /c "servermanagercmd -install AD-Certificate 2> null" | Out-Null
	} else {
		try {Import-Module ServerManager -ErrorAction Stop}
		catch {
			ocsetup 'ServerManager-PSH-Cmdlets' /quiet | Out-Null
			Start-Sleep 1
			Import-Module ServerManager -ErrorAction Stop
		}
		$status = (Get-WindowsFeature -Name AD-Certificate).Installed
		# if still no, install binaries, otherwise do nothing
		if (!$status) {$retn = Add-WindowsFeature -Name AD-Certificate -ErrorAction Stop
			if (!$retn.Success) {
				Write-Error -Category NotInstalled -ErrorId "NotInstalledException" `
				-Message "Unable to install ADCS installation packages due of the following error: $($retn.breakCode)"
				return
			}
		}
	}
	try {$CASetup = New-Object -ComObject CertOCM.CertSrvSetup.1}
	catch {
		Write-Error -Category NotImplemented -ErrorId "NotImplementedException" `
		-Message "Unable to load necessary interfaces. Your Windows Server operating system is not supported!"
		return
	}
	# initialize setup binaries
	try {$CASetup.InitializeDefaults($true, $false)}
	catch {
		Write-Error -Category InvalidArgument -ErrorId ParameterIncorrectException `
		-ErrorAction Stop -Message "Cannot initialize setup binaries!"
	}
#endregion

#region Property enums
	$CATypesByName = @{"Enterprise Root" = 0; "Enterprise Subordinate" = 1; "Standalone Root" = 3; "Standalone Subordinate" = 4}
	$CATypesByVal = @{}
	$CATypesByName.keys | ForEach-Object {$CATypesByVal.Add($CATypesByName[$_],$_)}
	$CAPRopertyByName = @{"CAType"=0;"CAKeyInfo"=1;"Interactive"=2;"ValidityPeriodUnits"=5;
		"ValidityPeriod"=6;"ExpirationDate"=7;"PreserveDataBase"=8;"DBDirectory"=9;"Logdirectory"=10;
		"ParentCAMachine"=12;"ParentCAName"=13;"RequestFile"=14;"WebCAMachine"=15;"WebCAName"=16
	}
	$CAPRopertyByVal = @{}
	$CAPRopertyByName.keys | ForEach-Object {$CAPRopertyByVal.Add($CAPRopertyByName[$_],$_)}
	$ValidityUnitsByName = @{"years" = 6}
	$ValidityUnitsByVal = @{6 = "years"}
#endregion
	$ofs = ", "
#region Key set processing functions

#region NewKeySet
function NewKeySet ($CAName, $CADNSuffix, $CAType, $ParentCA, $CSP, $KeyLength, $HashAlgorithm, $ValidForYears, $RequestFileName) {

#region CSP, key length and hashing algorithm verification
	$CAKey = $CASetup.GetCASetupProperty(1)
	if ($CSP -ne "") {
		if ($CASetup.GetProviderNameList() -notcontains $CSP) {
			# TODO add available CSP list
			Write-Error -Category InvalidArgument -ErrorId "InvalidCryptographicServiceProviderException" `
			-ErrorAction Stop -Message "Specified CSP '$CSP' is not valid!"
		} else {
			$CAKey.ProviderName = $CSP
		}
	} else {
		$CAKey.ProviderName = "RSA#Microsoft Software Key Storage Provider"
	}
	if ($KeyLength -ne 0) {
		if ($CASetup.GetKeyLengthList($CSP).Length -eq 1) {
			$CAKey.Length = $CASetup.GetKeyLengthList($CSP)[0]
		} else {
			if ($CASetup.GetKeyLengthList($CSP) -notcontains $KeyLength) {
				Write-Error -Category InvalidArgument -ErrorId "InvalidKeyLengthException" `
				-ErrorAction Stop -Message @"
The specified key length '$KeyLength' is not supported by the selected CSP '$CSP' The following
key lengths are supported by this CSP: $($CASetup.GetKeyLengthList($CSP))
"@
			}
			$CAKey.Length = $KeyLength
		}
	}
	if ($HashAlgorithm -ne "") {
		if ($CASetup.GetHashAlgorithmList($CSP) -notcontains $HashAlgorithm) {
				Write-Error -Category InvalidArgument -ErrorId "InvalidHashAlgorithmException" `
				-ErrorAction Stop -Message @"
The specified hash algorithm is not supported by the selected CSP '$CSP' The following
hash algorithms are supported by this CSP: $($CASetup.GetHashAlgorithmList($CSP))
"@
		}
		$CAKey.HashAlgorithm = $HashAlgorithm
	}
	$CASetup.SetCASetupProperty(1,$CAKey)
#endregion

#region Setting CA type
	if ($CAType) {
		$SupportedTypes = $CASetup.GetSupportedCATypes()
		$SelectedType = $CATypesByName[$CAType]
		if ($SupportedTypes -notcontains $CATypesByName[$CAType]) {
			Write-Error -Category InvalidArgument -ErrorId "InvalidCATypeException" `
			-ErrorAction Stop -Message @"
Selected CA type: '$CAType' is not supported by current Windows Server installation.
The following CA types are supported by this installation: $([int[]]$CASetup.GetSupportedCATypes() | %{$CATypesByVal[$_]})
"@
		} else {$CASetup.SetCASetupProperty($CAPRopertyByName.CAType,$SelectedType)}
	}
#endregion

#region setting CA certificate validity
	if ($SelectedType -eq 0 -or $SelectedType -eq 3 -and $ValidForYears -ne 0) {
		try{$CASetup.SetCASetupProperty(6,$ValidForYears)}
		catch {
			Write-Error -Category InvalidArgument -ErrorId "InvalidCAValidityException" `
			-ErrorAction Stop -Message "The specified CA certificate validity period '$ValidForYears' is invalid."
		}
	}
#endregion

#region setting CA name
	if ($CAName -ne "") {
		if ($CADNSuffix -ne "") {$Subject = "CN=$CAName" + ",$CADNSuffix"} else {$Subject = "CN=$CAName"}
		$DN = New-Object -ComObject X509Enrollment.CX500DistinguishedName
		# validate X500 name format
		try {$DN.Encode($Subject,0x0)}
		catch {
			Write-Error -Category InvalidArgument -ErrorId "InvalidX500NameException" `
			-ErrorAction Stop -Message "Specified CA name or CA name suffix is not correct X.500 Distinguished Name."
		}
		$CASetup.SetCADistinguishedName($Subject, $true, $true, $true)
	}
#endregion

#region set parent CA/request file properties
	if ($CASetup.GetCASetupProperty(0) -eq 1 -and $ParentCA) {
		[void]($ParentCA -match "^(.+)\\(.+)$")
		try {$CASetup.SetParentCAInformation($ParentCA)}
		catch {
			Write-Error -Category ObjectNotFound -ErrorId "ObjectNotFoundException" `
			-ErrorAction Stop -Message @"
The specified parent CA information '$ParentCA' is incorrect. Make sure if parent CA
information is correct (you must specify existing CA) and is supplied in a 'CAComputerName\CASanitizedName' form.
"@
		}
	} elseif ($CASetup.GetCASetupProperty(0) -eq 1 -or $CASetup.GetCASetupProperty(0) -eq 4 -and $RequestFileName -ne "") {
		$CASetup.SetCASetupProperty(14,$RequestFileName)
	}
#endregion
}

#endregion

#region PFXKeySet
function PFXKeySet ($CACertFile, $Password) {
	$FilePath = Resolve-Path $CACertFile -ErrorAction Stop
	try {[void]$CASetup.CAImportPFX(
		$FilePath.Path,
		[Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)),
		$true)
	} catch {Write-Error $_ -ErrorAction Stop}
}
#endregion

#region ExistingKeySet
function ExistingKeySet ($Thumbprint) {
	$ExKeys = $CASetup.GetExistingCACertificates() | ?{
		([Security.Cryptography.X509Certificates.X509Certificate2]$_.ExistingCACertificate).Thumbprint -eq $Thumbprint
	}
	if (!$ExKeys) {
		Write-Error -Category ObjectNotFound -ErrorId "ElementNotFoundException" `
		-ErrorAction Stop -Message "The system cannot find a valid CA certificate with thumbprint: $Thumbprint"
	} else {$CASetup.SetCASetupProperty(1,@($ExKeys)[0])}
}
#endregion

#endregion

#region set database settings
	if ($DBDirectory -ne "" -and $LogDirectory -ne "") {
		try {$CASetup.SetDatabaseInformation($DBDirectory,$LogDirectory,$null,$OverwriteExisting)}
		catch {
			Write-Error -Category InvalidArgument -ErrorId "InvalidPathException" `
			-ErrorAction Stop -Message "Specified path to either database directory or log directory is invalid."
		}
	} elseif ($DBDirectory -ne "" -and $LogDirectory -eq "") {
		Write-Error -Category InvalidArgument -ErrorId "InvalidPathException" `
		-ErrorAction Stop -Message "CA Log file directory cannot be empty."
	} elseif ($DBDirectory -eq "" -and $LogDirectory -ne "") {
		Write-Error -Category InvalidArgument -ErrorId "InvalidPathException" `
		-ErrorAction Stop -Message "CA database directory cannot be empty."
	}

#endregion
	# process parametersets.
	switch ($PSCmdlet.ParameterSetName) {
		"ExistingKeySet" {ExistingKeySet $Thumbprint}
		"PFXKeySet" {PFXKeySet $CACertFile $Password}
		"NewKeySet" {NewKeySet $CAName $CADNSuffix $CAType $ParentCA $CSP $KeyLength $HashAlgorithm $ValidForYears $RequestFileName}
	}
	try {
		Write-Host "Installing Certification Authority role on $env:computername ..." -ForegroundColor Cyan
		if ($Force -or $PSCmdlet.ShouldProcess($env:COMPUTERNAME, "Install Certification Authority")) {
			$CASetup.Install()
			$PostRequiredMsg = @"
Certification Authority role was successfully installed, but not completed. To complete installation submit
request file '$($CASetup.GetCASetupProperty(14))' to parent Certification Authority
and install issued certificate by running the following command: certutil -installcert 'PathToACertFile'
"@
			if ($CASetup.GetCASetupProperty(0) -eq 1 -and $ParentCA -eq "") {
				Write-Host $PostRequiredMsg -ForegroundColor Yellow -BackgroundColor Black
			} elseif ($CASetup.GetCASetupProperty(0) -eq 1 -and $PSCmdlet.ParameterSetName -eq "NewKeySet" -and $ParentCA -ne "") {
				$CASName = (Get-ItemProperty HKLM:\System\CurrentControlSet\Services\CertSvc\Configuration).Active
				$SetupStatus = (Get-ItemProperty HKLM:\System\CurrentControlSet\Services\CertSvc\Configuration\$CASName).SetupStatus
				$RequestID = (Get-ItemProperty HKLM:\System\CurrentControlSet\Services\CertSvc\Configuration\$CASName).RequestID
				if ($SetupStatus -ne 1) {
					Write-Host $PostRequiredMsg -ForegroundColor Yellow -BackgroundColor Black
				}
			} elseif ($CASetup.GetCASetupProperty(0) -eq 4) {
				Write-Host $PostRequiredMsg -ForegroundColor Yellow -BackgroundColor Black
			} else {Write-Host "Certification Authority role is successfully installed!" -ForegroundColor Green}
		}
	} catch {Write-Error $_ -ErrorAction Stop}
	Remove-Module ServerManager -ErrorAction SilentlyContinue
}

function Uninstall-CertificationAuthority {
<#
.Synopsis
    Uninstalls Active Directory Certificate Services role from the local computer.
.Description
    Uninstalls Active Directory Certificate Services role from the local computer.
	
	The command supports Windows Server 2008 R2 Server Core installations.
.Parameter AutoRestart
    Automatically restarts computer to complete CA role removal. Otherwise you will have to restart the server manually.
.Parameter Force
	By default, the commands prompts you whether you want to remove CA role. Use –Force switch to suppress all prompts.
.EXAMPLE
	PS > Uninstall-CertificationAuthority -AutoRestart -Force

	The command will uninstall CA role, suppresses all prompts and automatically restarts the server upon completion.
.Inputs
	None.
.Outputs
	None.
.NOTES
	Author: Vadims Podans
	Blog  : http://en-us.sysadmins.lv
#>
[CmdletBinding(
	ConfirmImpact = 'High',
	SupportsShouldProcess = $true
)]
	param(
		[switch]$AutoRestart,
		[switch]$Force
	)

#region OS and existing CA checking
	# check if script running on Windows Server 2008 or Windows Server 2008 R2
	$OS = Get-WmiObject Win32_OperatingSystem -Property ProductType
	if ([Environment]::OSVersion.Version.Major -lt 6) {
		Write-Error -Category NotImplemented -ErrorId "NotSupportedException" `
		-Message "Windows XP, Windows Server 2003 and Windows Server 2003 R2 are not supported!"
		return
	}
	if ($OS.ProductType -eq 1) {
		Write-Error -Category NotImplemented -ErrorId "NotSupportedException" `
		-Message "Client operating systems are not supported!"
		return
	}
	$CertConfig = New-Object -ComObject CertificateAuthority.Config
    try {$ExistingDetected = $CertConfig.GetConfig(3)}
    catch {
        Write-Error -Category ObjectNotFound -ErrorId "ElementNotFoundException" `
        -ErrorAction Stop -Message "Certificate Services are not installed on this computer."
    }

#endregion

#region Binaries checking and removal stuff
	try {$CASetup = New-Object -ComObject CertOCM.CertSrvSetup.1}
	catch {
		Write-Error -Category NotImplemented -ErrorId "NotImplementedException" `
		-Message "Unable to load necessary interfaces. Your Windows Server operating system is not supported!"
		return
	}
	if ([Environment]::OSVersion.Version.Major -eq 6 -and [Environment]::OSVersion.Version.Minor -eq 0) {
		cmd /c "servermanagercmd -remove ADCS-Cert-Authority 2> null" | Out-Null
	} else {
		try {Import-Module ServerManager -ErrorAction Stop}
		catch {
			ocsetup 'ServerManager-PSH-Cmdlets' /quiet | Out-Null
			Start-Sleep 2
			Import-Module ServerManager
		}
		$status = (Get-WindowsFeature -Name ADCS-Cert-Authority).Installed
		if ($status) {
			$WarningPreference = "SilentlyContinue"
			if ($Force -or $PSCmdlet.ShouldProcess($env:COMPUTERNAME, "Uninstall Certification Authority")) {
				$CASetup.PreUninstall($false)
				$retn = Remove-WindowsFeature -Name ADCS-Cert-Authority -ErrorAction Stop
			}
		}
	}
	if ($AutoRestart) {
		Restart-Computer -Force
	} else {
		Write-Host "Certification Authority role was removed successfully. You must restart this server to complete role removal." `
		-ForegroundColor Yellow -BackgroundColor Black
	}
#endregion
}
# SIG # Begin signature block
# MIIQWAYJKoZIhvcNAQcCoIIQSTCCEEUCAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQUKT+aLJUEuqomzabnAAN5hI+D
# V2SgggwdMIIDejCCAmKgAwIBAgIQOCXX+vhhr570kOcmtdZa1TANBgkqhkiG9w0B
# AQUFADBTMQswCQYDVQQGEwJVUzEXMBUGA1UEChMOVmVyaVNpZ24sIEluYy4xKzAp
# BgNVBAMTIlZlcmlTaWduIFRpbWUgU3RhbXBpbmcgU2VydmljZXMgQ0EwHhcNMDcw
# NjE1MDAwMDAwWhcNMTIwNjE0MjM1OTU5WjBcMQswCQYDVQQGEwJVUzEXMBUGA1UE
# ChMOVmVyaVNpZ24sIEluYy4xNDAyBgNVBAMTK1ZlcmlTaWduIFRpbWUgU3RhbXBp
# bmcgU2VydmljZXMgU2lnbmVyIC0gRzIwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJ
# AoGBAMS18lIVvIiGYCkWSlsvS5Frh5HzNVRYNerRNl5iTVJRNHHCe2YdicjdKsRq
# CvY32Zh0kfaSrrC1dpbxqUpjRUcuawuSTksrjO5YSovUB+QaLPiCqljZzULzLcB1
# 3o2rx44dmmxMCJUe3tvvZ+FywknCnmA84eK+FqNjeGkUe60tAgMBAAGjgcQwgcEw
# NAYIKwYBBQUHAQEEKDAmMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC52ZXJpc2ln
# bi5jb20wDAYDVR0TAQH/BAIwADAzBgNVHR8ELDAqMCigJqAkhiJodHRwOi8vY3Js
# LnZlcmlzaWduLmNvbS90c3MtY2EuY3JsMBYGA1UdJQEB/wQMMAoGCCsGAQUFBwMI
# MA4GA1UdDwEB/wQEAwIGwDAeBgNVHREEFzAVpBMwETEPMA0GA1UEAxMGVFNBMS0y
# MA0GCSqGSIb3DQEBBQUAA4IBAQBQxUvIJIDf5A0kwt4asaECoaaCLQyDFYE3CoIO
# LLBaF2G12AX+iNvxkZGzVhpApuuSvjg5sHU2dDqYT+Q3upmJypVCHbC5x6CNV+D6
# 1WQEQjVOAdEzohfITaonx/LhhkwCOE2DeMb8U+Dr4AaH3aSWnl4MmOKlvr+ChcNg
# 4d+tKNjHpUtk2scbW72sOQjVOCKhM4sviprrvAchP0RBCQe1ZRwkvEjTRIDroc/J
# ArQUz1THFqOAXPl5Pl1yfYgXnixDospTzn099io6uE+UAKVtCoNd+V5T9BizVw9w
# w/v1rZWgDhfexBaAYMkPK26GBPHr9Hgn0QXF7jRbXrlJMvIzMIIDxDCCAy2gAwIB
# AgIQR78Zld+NUkZD99ttSA0xpDANBgkqhkiG9w0BAQUFADCBizELMAkGA1UEBhMC
# WkExFTATBgNVBAgTDFdlc3Rlcm4gQ2FwZTEUMBIGA1UEBxMLRHVyYmFudmlsbGUx
# DzANBgNVBAoTBlRoYXd0ZTEdMBsGA1UECxMUVGhhd3RlIENlcnRpZmljYXRpb24x
# HzAdBgNVBAMTFlRoYXd0ZSBUaW1lc3RhbXBpbmcgQ0EwHhcNMDMxMjA0MDAwMDAw
# WhcNMTMxMjAzMjM1OTU5WjBTMQswCQYDVQQGEwJVUzEXMBUGA1UEChMOVmVyaVNp
# Z24sIEluYy4xKzApBgNVBAMTIlZlcmlTaWduIFRpbWUgU3RhbXBpbmcgU2Vydmlj
# ZXMgQ0EwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCpyrKkzM0grwp9
# iayHdfC0TvHfwQ+/Z2G9o2Qc2rv5yjOrhDCJWH6M22vdNp4Pv9HsePJ3pn5vPL+T
# rw26aPRslMq9Ui2rSD31ttVdXxsCn/ovax6k96OaphrIAuF/TFLjDmDsQBx+uQ3e
# P8e034e9X3pqMS4DmYETqEcgzjFzDVctzXg0M5USmRK53mgvqubjwoqMKsOLIYdm
# vYNYV291vzyqJoddyhAVPJ+E6lTBCm7E/sVK3bkHEZcifNs+J9EeeOyfMcnx5iIZ
# 28SzR0OaGl+gHpDkXvXufPF9q2IBj/VNC97QIlaolc2uiHau7roN8+RN2aD7aKCu
# FDuzh8G7AgMBAAGjgdswgdgwNAYIKwYBBQUHAQEEKDAmMCQGCCsGAQUFBzABhhho
# dHRwOi8vb2NzcC52ZXJpc2lnbi5jb20wEgYDVR0TAQH/BAgwBgEB/wIBADBBBgNV
# HR8EOjA4MDagNKAyhjBodHRwOi8vY3JsLnZlcmlzaWduLmNvbS9UaGF3dGVUaW1l
# c3RhbXBpbmdDQS5jcmwwEwYDVR0lBAwwCgYIKwYBBQUHAwgwDgYDVR0PAQH/BAQD
# AgEGMCQGA1UdEQQdMBukGTAXMRUwEwYDVQQDEwxUU0EyMDQ4LTEtNTMwDQYJKoZI
# hvcNAQEFBQADgYEASmv56ljCRBwxiXmZK5a/gqwB1hxMzbCKWG7fCCmjXsjKkxPn
# BFIN70cnLwA4sOTJk06a1CJiFfc/NyFPcDGA8Ys4h7Po6JcA/s9Vlk4k0qknTnqu
# t2FB8yrO58nZXt27K4U+tZ212eFX/760xX71zwye8Jf+K9M7UhsbOCf3P0owggTT
# MIIDu6ADAgECAgphPJ1VAAAAAAATMA0GCSqGSIb3DQEBBQUAMHIxCzAJBgNVBAYT
# AkxWMRUwEwYDVQQKEwxTeXNhZG1pbnMgTFYxHDAaBgNVBAsTE0luZm9ybWF0aW9u
# IFN5c3RlbXMxLjAsBgNVBAMTJVN5c2FkbWlucyBMViBJbnRlcm5hbCBDbGFzcyAx
# IFN1YkNBLTEwHhcNMTAwNDE1MTc0MDU2WhcNMTUwNDE0MTc0MDU2WjBaMQswCQYD
# VQQHEwJMVjEVMBMGA1UEChMMU3lzYWRtaW5zIExWMRwwGgYDVQQLExNJbmZvcm1h
# dGlvbiBTeXN0ZW1zMRYwFAYDVQQDEw1WYWRpbXMgUG9kYW5zMIIBIjANBgkqhkiG
# 9w0BAQEFAAOCAQ8AMIIBCgKCAQEAhzDxXkGOfXVksAb8aGJD7LsISli39npqUVB2
# QE09Ie5YwL55s9RCASTLnsk56j0N5dS/z6s7E63W2Gm0QMQhnm0lAeFLEsR+jEtI
# dAKSfg6ZBeTqr9RlZ++S2/veTZGr7F22+YwVMfjGq+F11WZrox4oQFY+7lRGFPvC
# +cj5waHlN4TySYSur8TaFUg55nWvzkgLWdoGJXhXEkwxCR4+zAFNgIByNgJPVRTw
# aKER2Crx0KU2awTZr91g2hOS3EgZSTbAWc/+m1IS2uXOFzMprlYOUZ64zHraV9G5
# N/Or6A7OTgkOV653o0+qoiKOH+JgFL6on7gZ7Fg8vTBkJ1M9VQIDAQABo4IBgTCC
# AX0wOwYJKwYBBAGCNxUHBC4wLAYkKwYBBAGCNxUIlp1NhZKyeL2fPIXo7HSCzthE
# eoKq90KH58Q2AgFkAgEDMB8GA1UdJQQYMBYGCisGAQQBgjcKAwwGCCsGAQUFBwMD
# MA4GA1UdDwEB/wQEAwIHgDApBgkrBgEEAYI3FQoEHDAaMAwGCisGAQQBgjcKAwww
# CgYIKwYBBQUHAwMwHQYDVR0OBBYEFCx12lrTtrk1gAKUsuYvMaIr11eZMB8GA1Ud
# IwQYMBaAFBv6XnMtZxNcztMO5uh6qWCMC2P8MDcGA1UdHwQwMC4wLKAqoCiGJmh0
# dHA6Ly93d3cuc3lzYWRtaW5zLmx2L3BraS9waWNhLTEuY3JsMGkGCCsGAQUFBwEB
# BF0wWzAyBggrBgEFBQcwAoYmaHR0cDovL3d3dy5zeXNhZG1pbnMubHYvcGtpL3Bp
# Y2EtMS5jcnQwJQYIKwYBBQUHMAGGGWh0dHA6Ly9vY3NwLnN5c2FkbWlucy5sdi8w
# DQYJKoZIhvcNAQEFBQADggEBAEnZsZtm77dP7Rklc5NKNB9d8BwHPOocz5HXpSnq
# peSNSdCCC4g1P/Uq2qvfLtJ08aTIdnK2rPQAHCv+GBnVt2XhZpX3GnLigmeLvBTg
# aroyHxDO+EbCtCZCJ9tHK6Yz8QozPJhlT4qQPtMAeg3UKIQaGITIr705VpA3EDHA
# 7eOZZY1yPZDzpitXuv5fOQBT83qBJ5VReKLl4YDfTBA2cJZB3ZxPMv20d00fy3io
# o30uGKO3QSjEYRlgYOeJE6YhiUjBlSPqdT9eyZ4fInm+ly8HG7XYBVAw0hRj4fMI
# tK0qcLJJ3WG2YkF6aVpqbQ495intBJQqDDObX6ArzXcZTMoxggOlMIIDoQIBATCB
# gDByMQswCQYDVQQGEwJMVjEVMBMGA1UEChMMU3lzYWRtaW5zIExWMRwwGgYDVQQL
# ExNJbmZvcm1hdGlvbiBTeXN0ZW1zMS4wLAYDVQQDEyVTeXNhZG1pbnMgTFYgSW50
# ZXJuYWwgQ2xhc3MgMSBTdWJDQS0xAgphPJ1VAAAAAAATMAkGBSsOAwIaBQCgeDAY
# BgorBgEEAYI3AgEMMQowCKACgAChAoAAMBkGCSqGSIb3DQEJAzEMBgorBgEEAYI3
# AgEEMBwGCisGAQQBgjcCAQsxDjAMBgorBgEEAYI3AgEVMCMGCSqGSIb3DQEJBDEW
# BBQzc2r7FJfEUO0yY09ICBx4w+NAQTANBgkqhkiG9w0BAQEFAASCAQBxu7zuXLuX
# EGfQFqrJbc+NzOyE6tjtOYPcjxnZQVl2C7lFaByl/rAL4DDVe3jgpf8dOEW1ol5z
# yS70NAwXtXauGiij1TorP2oMKpLZRZ9xpJAIfC68/cCt1d7sdy3ApzBvrohJRNRi
# EFD5+2LIbC7HJNztKOmPXWnHvhDJif9RBn8UpOrdUs89LJZ2r+nnDC/vH8XBemfd
# 0FTvAow1BQLxNgY0H4KeIEwswP3IZqkzu8Xt9gc6oBRH9GM0Q+vyctSZRLCSFFIo
# 9Mdk5Ie3CuvykaSmEhcqKX95SvIuVAMvAc8FUF0GxdgCqxDMQX3QSbYb6q+Zb9GI
# aTXXojHmwPnkoYIBfzCCAXsGCSqGSIb3DQEJBjGCAWwwggFoAgEBMGcwUzELMAkG
# A1UEBhMCVVMxFzAVBgNVBAoTDlZlcmlTaWduLCBJbmMuMSswKQYDVQQDEyJWZXJp
# U2lnbiBUaW1lIFN0YW1waW5nIFNlcnZpY2VzIENBAhA4Jdf6+GGvnvSQ5ya11lrV
# MAkGBSsOAwIaBQCgXTAYBgkqhkiG9w0BCQMxCwYJKoZIhvcNAQcBMBwGCSqGSIb3
# DQEJBTEPFw0xMjAzMDgxNzAwMjNaMCMGCSqGSIb3DQEJBDEWBBQGAnLE9rV993vJ
# LOWdPkdEz19fyjANBgkqhkiG9w0BAQEFAASBgGgCbppEUlH1/2ikRN07ZwWzCZYH
# DB9q6c3fdihk8dqp21zyz9bwuraMdM7KAMtORTcp1l0eR0LJ0jPZVu9EImQVzxxH
# Oxr2xZlVl9FCcLCFUxx5Ckz0KqeimcuJfHgNqXgCzulVV2Pa/0s6/1kqVWq27DcV
# Jmli3nvW1syfx1po
# SIG # End signature block
