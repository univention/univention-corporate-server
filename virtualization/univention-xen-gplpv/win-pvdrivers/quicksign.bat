@ECHO OFF

CALL set_ddk_path.bat

IF %_BUILDARCH%==x86 (SET BUILDDIR=obj%BUILD_ALT_DIR%\i386) ELSE (SET BUILDDIR=obj%BUILD_ALT_DIR%\amd64)
IF %DDK_TARGET_OS%==Win2K SET SIGN_OS=2000
IF %DDK_TARGET_OS%==WinXP SET SIGN_OS=XP_X86
IF %DDK_TARGET_OS%%_BUILDARCH%==WinNETx86 SET SIGN_OS=Server2003_X86
IF %DDK_TARGET_OS%%_BUILDARCH%==WinNETAMD64 SET SIGN_OS=XP_X64,Server2003_X64
IF %DDK_TARGET_OS%%_BUILDARCH%==WinLHx86 SET SIGN_OS=Vista_X86,Server2008_X86
IF %DDK_TARGET_OS%%_BUILDARCH%==WinLHAMD64 SET SIGN_OS=Vista_X64,Server2008_X64

SET CERT_FILENAME=
SET CERT_PASSWORD=
SET CERT_CROSS_CERT_FILENAME=
SET CERT_PUBLIC_FILENAME=
call sign_config.bat

SET SIGNTOOL=%DDK_PATH%\bin\x86\signtool.exe
IF NOT EXIST %SIGNTOOL% SET SIGNTOOL=%DDK_PATH%\bin\selfsign\signtool.exe

ECHO DDK_TARGET_OS=%DDK_TARGET_OS%
ECHO _BUILDARCH=%_BUILDARCH%
ECHO BUILDDIR=%BUILDDIR%
ECHO SIGN_OS=%SIGN_OS%
ECHO SIGNTOOL=%SIGNTOOL%
SET CERT_CROSS_CERT_FLAG=
IF DEFINED CERT_CROSS_CERT_FILENAME SET CERT_CROSS_CERT_FLAG=/ac %CERT_CROSS_CERT_FILENAME%
SET CERT_PASSWORD_FLAG=
IF DEFINED CERT_PASSWORD SET CERT_PASSWORD_FLAG=/p %CERT_PASSWORD%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xenpci\%BUILDDIR%\xenpci.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xenvbd_scsiport\%BUILDDIR%\xenvbd.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xenvbd_filter\%BUILDDIR%\xenvbd_filter.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xenvbd_storport\%BUILDDIR%\xenvbd.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xennet\%BUILDDIR%\xennet.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xenusb\%BUILDDIR%\xenusb.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timstamp.dll xencache\%BUILDDIR%\xencache.sys
