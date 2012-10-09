@ECHO OFF

ver | find " 5.00." > nul
if %ERRORLEVEL% == 0 goto ver_2k

ver | find " 5.1." > nul
if %ERRORLEVEL% == 0 goto ver_xp

ver | find " 5.2." > nul
if %ERRORLEVEL% == 0 goto ver_2k3

ver | find " 6.0." > nul
if %ERRORLEVEL% == 0 goto ver_2k8

echo No automatic uninstall available or machine not supported.
goto exit

:ver_xp
echo Windows XP Detected... Uninstalling...
shutdownmon -u
cd winxp
copy /y ..\common\i386\dpinst.exe . >nul
dpinst.exe /U xennet.inf
dpinst.exe /U xenenum.inf
dpinst.exe /U xenscsi.inf
dpinst.exe /U xenvbd.inf
dpinst.exe /U xenstub.inf
dpinst.exe /U xenpci.inf
cd ..
echo Done
goto exit

:ver_2k
echo Windows 2000 Detected... Uninstalling...
shutdownmon -u
cd win2k
copy /y ..\common\i386\dpinst.exe . >nul
dpinst.exe /U xennet.inf
dpinst.exe /U xenenum.inf
dpinst.exe /U xenscsi.inf
dpinst.exe /U xenvbd.inf
dpinst.exe /U xenstub.inf
dpinst.exe /U xenpci.inf
cd ..
echo Done
goto exit


:ver_2k3
if %PROCESSOR_ARCHITECTURE% == AMD64 goto ver_2k3_amd64
echo Windows 2003 (i386) Detected... Uninstalling...
shutdownmon -u
cd winnet
copy /y ..\common\i386\dpinst.exe . >nul
dpinst.exe /U xennet.inf
dpinst.exe /U xenenum.inf
dpinst.exe /U xenscsi.inf
dpinst.exe /U xenvbd.inf
dpinst.exe /U xenstub.inf
dpinst.exe /U xenpci.inf
cd ..
echo Done
goto exit

:ver_2k3_amd64
echo Windows 2003 (amd64) Detected... Uninstalling...
shutdownmon -u
cd winnet
copy /y ..\common\amd64\dpinst.exe . >nul
dpinst.exe /U xennet.inf
dpinst.exe /U xenenum.inf
dpinst.exe /U xenscsi.inf
dpinst.exe /U xenvbd.inf
dpinst.exe /U xenstub.inf
dpinst.exe /U xenpci.inf
cd ..
echo Done
goto exit

:ver_2k8
if %PROCESSOR_ARCHITECTURE% == AMD64 goto ver_2k8_amd64
echo Windows Vista/2008 (i386) Detected... Uninstalling...
shutdownmon -u
cd winlh
copy /y ..\common\i386\dpinst.exe . >nul
dpinst.exe /U xennet.inf
dpinst.exe /U xenenum.inf
dpinst.exe /U xenscsi.inf
dpinst.exe /U xenvbd.inf
dpinst.exe /U xenstub.inf
dpinst.exe /U xenpci.inf
cd ..
echo Done
goto exit

:ver_2k8_amd64
echo Windows Vista/2008 (amd64) Detected... Uninstalling...
shutdownmon -u
cd winlh
copy /y ..\common\amd64\dpinst.exe . >nul
dpinst.exe /U xennet.inf
dpinst.exe /U xenenum.inf
dpinst.exe /U xenscsi.inf
dpinst.exe /U xenvbd.inf
dpinst.exe /U xenstub.inf
dpinst.exe /U xenpci.inf
cd ..
echo Done
goto exit

pause
:exit