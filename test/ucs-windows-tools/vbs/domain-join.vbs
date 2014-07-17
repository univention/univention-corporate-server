Const JOIN_DOMAIN = 1
Const ACCT_CREATE = 2
Const ACCT_DELETE = 4
Const WIN9X_UPGRADE = 16
Const DOMAIN_JOIN_IF_JOINED = 32
Const JOIN_UNSECURE = 64
Const MACHINE_PASSWORD_PASSED = 128
Const DEFERRED_SPN_SET = 256
Const INSTALL_INVOCATION = 262144

if WScript.Arguments.Count <> 3 then
    wscript.quit 10
end if

domain = WScript.Arguments(0)
user = WScript.Arguments(1)
password = WScript.Arguments(2)

Set objNetwork = CreateObject("WScript.Network")
Set objComputer = GetObject("winmgmts:" _
	& "{impersonationLevel=Impersonate,authenticationLevel=Pkt}!\\" & _
	objNetwork.ComputerName & "\root\cimv2:Win32_ComputerSystem.Name='" & _
	objNetwork.ComputerName & "'")

returnValue = objComputer.JoinDomainOrWorkGroup( _
	domain, _
	password, _
	domain & "\" & user, _
	NULL, _
	JOIN_DOMAIN + ACCT_CREATE + DOMAIN_JOIN_IF_JOINED)

If returnValue <> 0 Then
	WScript.Echo "domain join failed with (" & Hex(returnValue) & ")"
    wscript.quit 1
End If

wscript.quit 0
