if WScript.Arguments.Count <> 3 then
	Wscript.Echo "wrong number of options"
	wscript.quit 1
end if

strUserName = WScript.Arguments(0)
strUserPassword = WScript.Arguments(1)
strNumberOfUsers = WScript.Arguments(2)

On Error Resume Next

Const ADS_UF_ACCOUNTDISABLE = 2
Set objRootLDAP = GetObject("LDAP://rootDSE")
Set objContainer = GetObject("LDAP://CN=Users," & objRootLDAP.Get("defaultNamingContext"))

For i = 1 To strNumberOfUsers
 
	strName = strUserName & i

	Set objUser = GetObject("LDAP://CN=" & strName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext")) 

	If objUser Then
		Err.Clear
		objUser.SetPassword strUserPassword
		If Err <> 0 Then
		   WScript.Echo "objNewUser.SetPassword failed (" & Hex(Err) & ")"
		   wscript.quit 1
		End If
		WScript.Echo "user " & strName & " modified"
		objUser = Null
	Else

		Set objNewUser = objContainer.Create("User", "cn=" & strName)
		objNewUser.Put "sAMAccountName", strName
		objNewUser.Put "givenName", strName
		objNewUser.Put "sn", strName
		objNewUser.Put "displayName", strName
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

		WScript.Echo "user " & strName & " created"
	End If

Next

WScript.Quit 0
