@ECHO OFF
IF NOT EXIST SIGN_CONFIG.BAT GOTO DONT_SIGN
CALL SIGN_CONFIG.BAT
IF %_BUILDARCH%==x86 SET BUILDDIR=%BUILD_ALT_DIR%\i386 ELSE SET BUILDDIR=%BUILD_ALT_DIR%\amd64
%DDK_PATH%\bin\selfsign\inf2cat /driver:%BUILD_ALT_DIR%/xenpci.inf /os:%2
%DDK_PATH%\bin\selfsign\signtool sign /v /n %CERT_NAME% /t http://timestamp.verisign.com/scripts/timestamp.dll target\%1\%2\xennet.sys target\%1\%2\xenpci.sys target\%1\%2\xenvbd.sys target\%1\%2\xenstub.sys target\%1\%2\xenhide.sys target\%1\%2\xenscsi.sys
%DDK_PATH%\bin\selfsign\signtool sign /v /n %CERT_NAME% /t http://timestamp.verisign.com/scripts/timestamp.dll target\%1\xengplpv.cat
:DONT_SIGN
(env.BUILD_ALT_DIR)\$(var.ARCHDIR)