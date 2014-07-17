On Error Resume Next

if WScript.Arguments.Count <> 4 then
	wscript.quit 10
end if

strObjectClass = WScript.Arguments(0)
strObjectCategory = WScript.Arguments(1)
strAttr = WScript.Arguments(2)
strValue = WScript.Arguments(3)
retval = 0

' Get OU
strOU = GetObject("LDAP://rootdse").Get("defaultnamingcontext")

' Create connection to AD
Set objConnection = CreateObject("ADODB.Connection")
objConnection.Open "Provider=ADsDSOObject;"

' Create command
Set objCommand = CreateObject("ADODB.Command")
objCommand.ActiveConnection = objConnection
objCommand.Properties("Page Size") = 1000
objCommand.CommandText = "<LDAP://" & strOU & ">;" & _
	"(&" & _
		"(objectclass=" & strObjectClass & ")" & _
		"(objectcategory=" & strObjectCategory & ")" & _
		"(" & strAttr & "=" & strValue & ")" & _
	");" & strAttr & ";subtree"

Set objRecordSet = objCommand.Execute
If objRecordSet.recordcount <> 1 Then
	retval = 13
End If

' Clean up
objRecordSet.Close
objConnection.Close

wscript.quit retval
