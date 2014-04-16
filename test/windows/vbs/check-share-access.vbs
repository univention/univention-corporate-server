if WScript.Arguments.Count <> 3 then
    wscript.quit 10
end if

ServerShare = WScript.Arguments(0)
UserName = WScript.Arguments(1)
Password = WScript.Arguments(2)
Retval = 0

Set NetworkObject = CreateObject("WScript.Network")
Set FSO = CreateObject("Scripting.FileSystemObject")

Err.Clear
On Error Resume Next
NetworkObject.MapNetworkDrive "", ServerShare, False, UserName, Password
If Err <> 0 Then
	WScript.Echo "NetworkObject.MapNetworkDrive failed with (" & Hex(Err) & ")"
	Retval = 1
End If

NetworkObject.RemoveNetworkDrive ServerShare, True, False

wscript.quit Retval
