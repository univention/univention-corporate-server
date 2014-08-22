if WScript.Arguments.Count <> 2 then
	Wscript.Echo "wrong number of options"
	wscript.quit 1
end if

strGroupName = WScript.Arguments(0)
strNumberOfGroups = WScript.Arguments(1)

On Error Resume Next

Set objRootLDAP = GetObject("LDAP://rootDSE")
Set objContainer = GetObject("LDAP://CN=Users," & objRootLDAP.Get("defaultNamingContext"))

For i = 1 To strNumberOfGroups
 
	strName = strGroupName & i

	Set objGroup = GetObject("LDAP://CN=" & strName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))

	If objGroup Then
		WScript.Echo "group cn=" & strName & " already exists"
		objGroup = Null
	Else
		Set objNewGroup = objContainer.Create("Group", "cn=" & strName)
		objNewGroup.Put "sAMAccountName", strName
		objNewGroup.Put "Description", "AD User created by VB Script"
		Err.Clear
		objNewGroup.SetInfo
		If Err <> 0 Then
			WScript.Echo "objNewGroup.SetInfo failed (" & Hex(Err) & ")"
			wscript.quit 1
		End If
		WScript.Echo "group " & strName & " created"
	End If
Next

WScript.Quit 0
