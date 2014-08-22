strComputer = "."

service = WScript.Arguments(0) 
timeout = WScript.Arguments(1)

Set objWMIService = GetObject("winmgmts:" _
& "{impersonationLevel=impersonate}!\\" _
& strComputer & "\root\cimv2")

Set colService = objWMIService.ExecQuery _
("Select * from Win32_Service")

For i = 0 To timeout
	For Each objService in colService
		WScript.Echo objService.Name & " " & objService.State
		If UCase(objService.Name) = UCase(service) Then  
			If UCase(objService.State) = "RUNNING" Then
				wscript.quit 0
			End If
		End If
	Next
	WScript.Sleep 1000
Next
