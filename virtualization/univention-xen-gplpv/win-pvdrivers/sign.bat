@ECHO OFF

IF NOT EXIST SIGN_CONFIG.BAT GOTO DONT_SIGN

IF %_BUILDARCH%==x86 (SET BUILDDIR=obj%BUILD_ALT_DIR%\i386) ELSE (SET BUILDDIR=obj%BUILD_ALT_DIR%\amd64)
IF %DDK_TARGET_OS%==Win2K SET SIGN_OS=2000
IF %DDK_TARGET_OS%==WinXP SET SIGN_OS=XP_X86
IF %DDK_TARGET_OS%%_BUILDARCH%==WinNETx86 SET SIGN_OS=Server2003_X86
IF %DDK_TARGET_OS%%_BUILDARCH%==WinNETAMD64 SET SIGN_OS=XP_X64,Server2003_X64
IF %DDK_TARGET_OS%%_BUILDARCH%==WinLHx86 SET SIGN_OS=Vista_X86,Server2008_X86
IF %DDK_TARGET_OS%%_BUILDARCH%==WinLHAMD64 SET SIGN_OS=Vista_X64,Server2008_X64

ECHO DDK_TARGET_OS=%DDK_TARGET_OS%
ECHO _BUILDARCH=%_BUILDARCH%
ECHO BUILDDIR=%BUILDDIR%
ECHO SIGN_OS=%SIGN_OS%

for /F %%x in ('DIR /B %BASEDIR%\redist\wdf\%_BUILDARCH%\WdfCoInstaller?????.dll') do set WDFFILENAME=%%x
xcopy /I /D %BASEDIR%\redist\wdf\%_BUILDARCH%\%WDFFILENAME% xenpci\%BUILDDIR%\
xcopy /I /D %BASEDIR%\redist\wdf\%_BUILDARCH%\%WDFFILENAME% xenusb\%BUILDDIR%\

%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenpci\%BUILDDIR%\xenpci.sys
%DDK_PATH%\bin\selfsign\inf2cat /driver:xenpci\%BUILDDIR% /os:%SIGN_OS%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenpci\%BUILDDIR%\xenpci.cat

COPY xenvbd_filter\%BUILDDIR%\xenvbdfilter.sys xenvbd_scsiport\%BUILDDIR%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenvbd_scsiport\%BUILDDIR%\xenvbd.sys
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenvbd_scsiport\%BUILDDIR%\xenvbdfilter.sys
%DDK_PATH%\bin\selfsign\inf2cat /driver:xenvbd_scsiport\%BUILDDIR% /os:%SIGN_OS%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenvbd_scsiport\%BUILDDIR%\xenvbd.cat

%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xennet\%BUILDDIR%\xennet.sys
%DDK_PATH%\bin\selfsign\inf2cat /driver:xennet\%BUILDDIR% /os:%SIGN_OS%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xennet\%BUILDDIR%\xennet.cat

IF %DDK_TARGET_OS%==Win2K GOTO DONT_SIGN

%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenusb\%BUILDDIR%\xenusb.sys
%DDK_PATH%\bin\selfsign\inf2cat /driver:xenusb\%BUILDDIR% /os:%SIGN_OS%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenusb\%BUILDDIR%\xenusb.cat

IF %DDK_TARGET_OS%==WinXP GOTO DONT_SIGN

%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenvbd_storport\%BUILDDIR%\xenvbd.sys
%DDK_PATH%\bin\selfsign\inf2cat /driver:xenvbd_storport\%BUILDDIR% /os:%SIGN_OS%
%SIGNTOOL% sign /v %CERT_CROSS_CERT_FLAG% /f %CERT_FILENAME% %CERT_PASSWORD_FLAG% /t http://timestamp.verisign.com/scripts/timestamp.dll xenvbd_storport\%BUILDDIR%\xenvbd.cat

:DONT_SIGN
