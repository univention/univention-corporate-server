@echo off
if exist c:\netinst\permcred.bat call c:\netinst\permcred.bat
if exist c:\netinst\tempcred.bat call c:\netinst\tempcred.bat

if not %Z%. == . goto got_drive
set Z=Z:
:got_drive

:: If drive is already mapped, do nothing
if exist %Z%\ goto mapped

if not %Z_PATH%. == . goto got_path
set Z_PATH=\\@%@hostname@%@\install
:got_path

if %Z_USER%. == . goto no_user
set USER_ARG=/user:%Z_USER%
:no_user

:try_again
set COUNT=x%COUNT%
if not %COUNT% == xxxxxxxxxxxxxxxxxxxx goto mapit
echo Too many retries; giving up
goto hang

:mapit
echo Mapping %Z_PATH% on %Z%...
net use %Z% %Z_PATH% %Z_PASS% %USER_ARG% /persistent:no
if exist %Z%\ goto mapped
net use %Z% /delete
echo Failed; retrying.
if exist C:\Perl\bin\perl.exe C:\Perl\bin\perl.exe -e "sleep 10;"
goto try_again

:mapped
echo ...done.
:: Clean up environment, except for %Z%
set Z_PATH=
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
