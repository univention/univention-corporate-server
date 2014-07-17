Const EWX_LOGOFF   = 0
Const EWX_SHUTDOWN = 1
Const EWX_REBOOT   = 2
Const EWX_FORCE    = 4
Const EWX_POWEROFF = 8

Set OpSysSet = GetObject("winmgmts:{(Shutdown)}//./root/cimv2").ExecQuery("select * from Win32_OperatingSystem where Primary=true")
for each OpSys in OpSysSet
	OpSys.Reboot(EWX_REBOOT + EWX_FORCE)
next

wscript.quit 0
