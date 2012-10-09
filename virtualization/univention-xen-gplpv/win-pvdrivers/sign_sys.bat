@ECHO OFF
IF NOT EXIST SIGN_CONFIG.BAT GOTO DONT_SIGN
CALL SIGN_CONFIG.BAT
%DDK_PATH%\bin\selfsign\signtool sign /v /n %CERT_NAME% /t http://timestamp.verisign.com/scripts/timestamp.dll target\%1\%2\xennet.sys target\%1\%2\xenpci.sys target\%1\%2\xenvbd.sys target\%1\%2\xenstub.sys target\%1\%2\xenhide.sys target\%1\%2\xenscsi.sys
:DONT_SIGN
