' activate remote desktop

Set objWMIService = GetObject("winmgmts:\\.\root\cimv2\terminalservices")
Set colTerminalService = objWMIService.ExecQuery("select * from Win32_TerminalServiceSetting")

On Error Resume Next

For Each objService in colTerminalService
	Err.Clear
	objService.SetAllowTSConnections(1)
	If Err <> 0 Then
		WScript.Echo "objService.SetAllowTSConnections failed (" & Hex(Err) & ")"
		WScript.quit 1
	End If
Next

WScript.quit 0
