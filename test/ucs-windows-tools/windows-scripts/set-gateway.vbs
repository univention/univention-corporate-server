On Error Resume Next
 
strComputer = "."

if WScript.Arguments.Count <> 1 then
	Wscript.Echo "need gateway as option"
	wscript.quit 1
end if

strGateway = Array(WScript.Arguments(0))

Set objWMIService = GetObject("winmgmts:" _
	& "{impersonationLevel=impersonate}!\\" & strComputer & "\root\cimv2")
Set colNicConfigs = objWMIService.ExecQuery _
	("SELECT * FROM Win32_NetworkAdapterConfiguration WHERE IPEnabled = True")
 
For Each objNicConfig In colNicConfigs
	objNicConfig.SetGateways(strGateway)
Next

wscript.quit 0
