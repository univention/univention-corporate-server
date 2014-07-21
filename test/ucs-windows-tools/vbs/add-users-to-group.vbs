if WScript.Arguments.Count <> 4 then
	Wscript.Echo "wrong number of options"
	wscript.quit 1
end if

strUserName = WScript.Arguments(0)
strNumberOfUsers = WScript.Arguments(1)
strGroupName = WScript.Arguments(2)
strNumberOfGroups = WScript.Arguments(3)

On Error Resume Next

Set objRootLDAP = GetObject("LDAP://rootDSE")
Set objContainer = GetObject("LDAP://CN=Users," & objRootLDAP.Get("defaultNamingContext"))

For i = 1 To strNumberOfGroups


	strGName = strGroupName & i
	Set objGroup = GetObject("LDAP://CN=" & strGName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))

	If objGroup Then
		For j = 1 To strNumberOfUsers
			strName = strUserName & j
			Set objUser = GetObject("LDAP://CN=" & strName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))
			If objUser Then
				' add user to group
				If Not objGroup.IsMember(objUser.ADsPath) Then
					Err.Clear
					objGroup.add(objUser.ADsPath)
					If Err <> 0 Then
						WScript.Echo "objGroup.add failed to group " & strGName & " and user " & strName & "(" & Hex(Err) & ")"
						wscript.quit 1
					End If
				End If
				objUser = Null
			Else
				WScript.Echo "user cn=" & strName & " not found"
				wscript.quit 1
			End If
		Next
		objGroup = Null
	Else
		WScript.Echo "group cn=" & strGName & " not found"
		wscript.quit 1
	End If


Next

WScript.Quit 0
