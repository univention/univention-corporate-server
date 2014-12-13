if WScript.Arguments.Count <> 3 then
	Wscript.Echo "wrong number of options"
	wscript.quit 1
end if

strUserName = WScript.Arguments(0)
strUserPassword = WScript.Arguments(1)
strGroupName = WScript.Arguments(2)

On Error Resume Next

Const ADS_UF_ACCOUNTDISABLE = 2
Set objRootLDAP = GetObject("LDAP://rootDSE")
Set objContainer = GetObject("LDAP://CN=Users," & objRootLDAP.Get("defaultNamingContext"))


Set objUser = GetObject("LDAP://CN=" & strUserName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext")) 

If objUser Then
	Err.Clear
	objUser.SetPassword strUserPassword
	If Err <> 0 Then
	   WScript.Echo "objNewUser.SetPassword failed (" & Hex(Err) & ")"
	   wscript.quit 1
	End If
	WScript.Echo "user " & strUserName & " modified"
	objUser = Null
Else

	Set objNewUser = objContainer.Create("User", "cn=" & strUserName)
	objNewUser.Put "sAMAccountName", strUserName
	objNewUser.Put "givenName", strUserName
	objNewUser.Put "sn", strUserName
	objNewUser.Put "displayName", strUserName
	objNewUser.Put "Description", "AD User created by VB Script"
	objNewUser.Put "userAccountControl", 544

	Err.Clear
	objNewUser.SetInfo
	If Err <> 0 Then
		WScript.Echo "objNewUser.SetInfo failed (" & Hex(Err) & ")"
		wscript.quit 1
	End If
	 
	Err.Clear
	objNewUser.SetPassword strUserPassword
	If Err <> 0 Then
		WScript.Echo "objNewUser.SetPassword failed (" & Hex(Err) & ")"
		wscript.quit 1
	End If
	
	objNewUser.Put "PasswordExpired", CLng(1)
	objNewUser.AccountDisabled = FALSE

	WScript.Echo "user " & strUserName & " created"
End If

Set objGroup = GetObject("LDAP://CN=" & strGroupName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))

If objGroup Then
	Set objUser = GetObject("LDAP://CN=" & strUserName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))
	If objUser Then
		' add user to group
		If Not objGroup.IsMember(objUser.ADsPath) Then
			Err.Clear
			objGroup.add(objUser.ADsPath)
			If Err <> 0 Then
				WScript.Echo "objGroup.add failed to group " & strGroupName & " and user " & strUserName & "(" & Hex(Err) & ")"
				wscript.quit 1
			End If
		End If
		objUser = Null
	Else
		WScript.Echo "user cn=" & strUserName & " not found"
		wscript.quit 1
	End If
Else
	WScript.Echo "group cn=" & strGroupName & " not found"
	wscript.quit 1
End If

WScript.Quit 0
