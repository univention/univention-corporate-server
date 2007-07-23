@echo off
if exist c:\netinst\permcred.bat call c:\netinst\permcred.bat
if exist c:\netinst\tempcred.bat call c:\netinst\tempcred.bat

if not %Y%. == . goto got_drive
set Y=Y:
:got_drive

:: If drive is already mapped, do nothing
if exist %Y%\ goto mapped

if not %Y_PATH%. == . goto got_path
set Y_PATH=\\@%@hostname@%@\install
:got_path

if %Z_USER%. == . goto no_user
set USER_ARG=/user:%Z_USER%
:no_user

:try_again
set COUNT=x%COUNT%
if not %COUNT% == xxx goto mapit
echo Too many retries; giving up
goto hang

:mapit
echo Mapping %Y_PATH% on %Y%...
net use %Y% %Y_PATH% %Z_PASS% %USER_ARG% /persistent:no
if exist %Y%\ goto mapped
net use %Y% /delete
echo Failed; retrying.
if exist C:\Perl\bin\perl.exe C:\Perl\bin\perl.exe -e "sleep 10;"
goto try_again

:mapped
echo ...done.
:: Clean up environment, except for %Z%
set Y_PATH=
set Z_USER=
set Z_PASS=
set USER_ARG=
set COUNT=

:: Invoke command passed as argument
%1 %2 %3 %4 %5 %6 %7 %8 %9
if not errorlevel 1 goto end
echo FAILURE in mapznrun.bat

:hang
goto hang

:end
