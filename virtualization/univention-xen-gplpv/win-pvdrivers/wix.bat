@ECHO OFF

IF "%_BUILDARCH%"=="x86" (SET DIFXLIB=%WIX%bin\difxapp_x86.wixlib) ELSE (SET DIFXLIB=%WIX%bin\difxapp_x64.wixlib)

IF "%_BUILDARCH%"=="x86" (SET MSIARCH=x32) ELSE (SET MSIARCH=x64)

IF "%DDKBUILDENV%"=="chk" (SET MSIBUILD=_debug) ELSE (SET MSIBUILD=)

SET MSIOS=%DDK_TARGET_OS%
IF "%DDK_TARGET_OS%"=="Win2K" (SET MSIOS=2000)
IF "%DDK_TARGET_OS%"=="Win2K" (SET MSIARCH=)
IF "%DDK_TARGET_OS%"=="WinXP" (SET MSIOS=XP)
IF "%DDK_TARGET_OS%"=="WinXP" (SET MSIARCH=)
IF "%DDK_TARGET_OS%"=="WinNET" (SET MSIOS=2003)
IF "%DDK_TARGET_OS%"=="WinLH" (SET MSIOS=Vista2008)

SET MSINAME=gplpv_%MSIOS%%MSIARCH%_%GPLPV_VERSION%%MSIBUILD%.msi

for /F %%x in ('DIR /B %BASEDIR%\redist\wdf\%_BUILDARCH%\WdfCoInstaller?????.dll') do set WDFFILENAME=%%x

"%WIX%\bin\candle" installer.wxs -ext "%WIX%\bin\WixUIExtension.dll" -ext "%WIX%\bin\WixDifxAppExtension.dll" -ext "%WIX%\bin\WixIIsExtension.dll"
"%WIX%\bin\light.exe" -o %MSINAME% installer.wixobj "%DIFXLIB%" -ext "%WIX%\bin\WixUIExtension.dll" -ext "%WIX%\bin\WixDifxAppExtension.dll" -ext "%WIX%\bin\WixIIsExtension.dll"

%SIGNTOOL% sign /v /s PrivateCertStore /n %CERT_NAME% /t http://timestamp.verisign.com/scripts/timestamp.dll %MSINAME%
