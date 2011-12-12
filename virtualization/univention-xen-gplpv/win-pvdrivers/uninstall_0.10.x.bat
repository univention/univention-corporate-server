@ECHO OFF

REM stop and remove shutdownmon service
net stop shutdownmon
"%ProgramFiles%\Xen PV Drivers\bin\ShutdownMon.exe" -u

REM remove XEN from Program Files
rmdir /q /s "%ProgramFiles%\Xen PV Drivers"

REM remove start menu stuff
ECHO "Please remove Start Menu stuff manually"

del /q "%SystemRoot%\system32\drivers\xen*"

REM delete inf and pnf files
FOR /F "delims=. tokens=1" %%I IN ('DIR /B "%SYSTEMROOT%\INF\OEM*.INF"') DO (
 TYPE "%SYSTEMROOT%\INF\%%I.inf" | FIND /c /i "xen" >%TEMP%\james
 FOR /f %%c IN (%TEMP%\james) DO (
  IF /I %%c NEQ 0 (
   DEL "%SYSTEMROOT%\INF\%%I.inf"
   DEL "%SYSTEMROOT%\INF\%%I.pnf"
  )
 )
)

REM clean registry
REG DELETE HKLM\SYSTEM\CurrentControlSet\Services\XenHide /f
REG DELETE HKLM\SYSTEM\CurrentControlSet\Services\XenNet /f
REG DELETE HKLM\SYSTEM\CurrentControlSet\Services\XenPci /f
REG DELETE HKLM\SYSTEM\CurrentControlSet\Services\XenVbd /f
REG DELETE HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E96A-E325-11CE-BFC1-08002BE10318} /v UpperFilters /f
REG DELETE HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002bE10318} /v UpperFilters /f
REG DELETE HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E97B-E325-11CE-BFC1-08002BE10318} /v UpperFilters /f
ECHO done
