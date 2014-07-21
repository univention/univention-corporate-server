Const EWX_LOGOFF   = 0
Const EWX_SHUTDOWN = 1
Const EWX_REBOOT   = 2
Const EWX_POWEROFF = 8
Const EWX_FORCE = 4

Set colOperatingSystems = GetObject("winmgmts:{(Shutdown)}").ExecQuery("Select * from Win32_OperatingSystem")
 
For Each objOperatingSystem in colOperatingSystems
    ObjOperatingSystem.Win32Shutdown(EWX_SHUTDOWN + EWX_FORCE)
Next

WScript.Quit 0
