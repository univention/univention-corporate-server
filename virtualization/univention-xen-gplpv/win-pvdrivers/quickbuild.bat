@echo off

GOTO %DDK_TARGET_OS% 2>nul:
ECHO no target set
GOTO :EOF

REM cmd /C "%DDK_PATH_2K%\bin\setenv.bat %DDK_PATH_2K%\ chk W2K && CD /D "%PV_DIR%" && build -cZg ~xenusb ~copyconfig ~waitnopendinginstallevents
REM cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ chk WXP && CD /D "%PV_DIR%" && build -cZg

REM 2000 and XP don't have storport
:Win2K
:WinXP
build -cZg ~xenvbd_storport
IF NOT %ERRORLEVEL%==0 GOTO :EOF
GOTO sign

REM 2003 may not have virtual storport so build both
:WinNET
build -cZg
IF NOT %ERRORLEVEL%==0 GOTO :EOF
GOTO sign

REM Vista and newer has virtual storport
:WinLH
build -cZg ~xenvbd_scsiport ~xenvbd_filter
IF NOT %ERRORLEVEL%==0 GOTO :EOF
GOTO sign

:sign

CALL quicksign.bat