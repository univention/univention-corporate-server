On Error Resume Next
 
strComputer = "."

if WScript.Arguments.Count <> 1 then
	Wscript.Echo "need dns server as option"
	wscript.quit 1
end if

strNewDNSServer = WScript.Arguments(0)
 
Set objWMIService = GetObject("winmgmts:" _
	& "{impersonationLevel=impersonate}!\\" & strComputer & "\root\cimv2")
Set colNicConfigs = objWMIService.ExecQuery _
	("SELECT * FROM Win32_NetworkAdapterConfiguration WHERE IPEnabled = True")
 
For Each objNicConfig In colNicConfigs
	arrNewDNSServerSearchOrder = Array(strNewDNSServer)
	intSetDNS = objNicConfig.SetDNSServerSearchOrder(arrNewDNSServerSearchOrder)
	If intSetDNS <> 0 Then
		wscript.quit intSetDNS
	End If
Next

wscript.quit 0
