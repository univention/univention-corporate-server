strComputer = "."

Set objWMIService = GetObject("winmgmts:" _
& "{impersonationLevel=impersonate}!\\" _
& strComputer & "\root\cimv2")

Set colService = objWMIService.ExecQuery _
("Select * from Win32_Service")

For Each objService in colService
	WScript.Echo objService.Name & " " & objService.State
Next
