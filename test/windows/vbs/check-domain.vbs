if WScript.Arguments.Count <> 1 then
	WScript.Echo "domain argument is required"
	wscript.quit 1
end if

DomainName = WScript.Arguments(0)
Set objSysInfo = CreateObject( "ADSystemInfo" )

Err.Clear
On Error Resume Next
If DomainName <> objSysInfo.DomainDNSName Then
	WScript.Echo "domain is " & objSysInfo.DomainDNSName & ", expected " & DomainName
	wscript.quit 1
End If

If Err <> 0 Then
	WScript.Echo "failed to get domain (" & Hex(Err) & ")"
	wscript.quit 1
End If

WScript.Echo "DNS-Domain: " & objSysInfo.DomainDNSName
wscript.quit 0
