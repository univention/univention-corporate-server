On Error Resume Next

' Get OU
strOU = GetObject("LDAP://rootdse").Get("defaultnamingcontext")

' Create connection to AD
Set objConnection = CreateObject("ADODB.Connection")

Err.Clear
objConnection.Open "Provider=ADsDSOObject;"
If Err <> 0 Then
	WScript.Echo "ad search failed (" & Hex(Err) & ")"
	wscript.quit 1
End If

' Create command
Set objCommand = CreateObject("ADODB.Command")
objCommand.ActiveConnection = objConnection
objCommand.Properties("Page Size") = 1000
objCommand.CommandText = "<LDAP://" & strOU & ">;" & _
	"(&" & _
		"(objectclass=user)" & _
		"(objectcategory=person)" & _
	");sAMAccountName,adspath;subtree"

'Err.Clear
Set objRecordSet = objCommand.Execute
If Err <> 0 Then
	WScript.Echo "ad search failed (" & Hex(Err) & ")"
	wscript.quit 1
End If
objRecordSet.MoveFirst
Do Until objRecordSet.EOF
	Wscript.Echo objRecordSet.Fields("sAMAccountName").Value & " (" & objRecordSet.Fields("adspath") & ")"
	objRecordSet.MoveNext
Loop

' Clean up
objRecordSet.Close
objConnection.Close

wscript.quit 0
