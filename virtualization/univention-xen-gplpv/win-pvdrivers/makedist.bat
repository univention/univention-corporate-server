@echo off
IF NOT EXIST set_ddk_path.bat ECHO >set_ddk_path.bat SET DDK_PATH=C:\WinDDK\7600.16385.0
IF NOT EXIST set_ddk_path_2k.bat ECHO >set_ddk_path_2k.bat SET DDK_PATH_2K=C:\WinDDK\6001.18002

SET VERSION=0.11.0
SET BUILD_NUMBER=0
IF EXIST build_number.bat CALL build_number.bat

SET GPLPV_VERSION=%VERSION%.%BUILD_NUMBER%

SET /A NEW_BUILD_NUMBER=%BUILD_NUMBER%+1
ECHO >build_number.bat SET BUILD_NUMBER=%NEW_BUILD_NUMBER%

ECHO BUILDING %GPLPV_VERSION%

CALL set_ddk_path.bat
CALL set_ddk_path_2K.bat

SET PV_DIR=%CD%

SET SIGNTOOL=%DDK_PATH%\bin\x86\signtool.exe
IF NOT EXIST %SIGNTOOL% SET SIGNTOOL=%DDK_PATH%\bin\selfsign\signtool.exe
SET CERT_NAME=GPLPV_Test_Cert

REM IF NOT EXIST SIGN_CONFIG.BAT GOTO DONT_SIGN
REM CALL SIGN_CONFIG.BAT

IF NOT EXIST gplpv.cer "%DDK_PATH%"\bin\selfsign\x86\makecert -r -pe -ss PrivateCertStore -n "CN=GPLPV_Test_Cert" gplpv.cer

mkdir symbols\%GPLPV_VERSION%

cmd /C "%DDK_PATH_2K%\bin\setenv.bat %DDK_PATH_2K%\ chk W2K && CD /D "%PV_DIR%" && build -cZg ~xenusb ~copyconfig ~waitnopendinginstallevents && call sign.bat && call archive.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ chk WXP && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call archive.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ chk WNET && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call archive.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ chk x64 WNET && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call archive.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ chk WLH && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call archive.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ chk x64 WLH && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call archive.bat && call wix.bat"

cmd /C "%DDK_PATH_2K%\bin\setenv.bat %DDK_PATH_2K%\ fre W2K && CD /D "%PV_DIR%" && build -cZg ~xenusb ~copyconfig ~waitnopendinginstallevents && call sign.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ fre WXP && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ fre WNET && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ fre x64 WNET && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ fre WLH && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call wix.bat"

cmd /C "%DDK_PATH%\bin\setenv.bat %DDK_PATH%\ fre x64 WLH && CD /D "%PV_DIR%" && build -cZg && call sign.bat && call wix.bat"

IF NOT EXIST TAG_HG GOTO DONT_TAG
IF EXIST BUILD*.WRN GOTO DONT_TAG
IF EXIST BUILD*.ERR GOTO DONT_TAG

hg tag %GPLPV_VERSION%

:DONT_TAG