Option Explicit
Dim strUserName
Dim strGroupName
Dim objRootLDAP
Dim objContainer
Dim objNewUser
Dim objNewGroup
Dim objGroup
Dim objUser
Dim objCommand
Dim objConnection
Dim objRecordSet
Dim counterUsers
Dim counterGroups
Dim strName
Dim intStart
Dim intEnd
Dim intUsersInGroup
Dim i
Dim j
Dim intUAC

Const ADS_UF_ACCOUNTDISABLE = 2

strUserName = "testuser"
strGroupName = "testgroup"
counterUsers = 1500
counterGroups = 40
 
Set objRootLDAP = GetObject("LDAP://rootDSE")
Set objCommand = CreateObject("ADODB.Command") 
Set objConnection = CreateObject("ADODB.Connection")

objConnection.Open "Provider=ADsDSOObject;"
objCommand.ActiveConnection = objConnection
 
' You can give your own OU like <i>LDAP://OU=TestOU</i> instead of <i>LDAP://CN=Users</i>
Set objContainer = GetObject("LDAP://CN=Users," & objRootLDAP.Get("defaultNamingContext"))

' check if object exists
Function QueryAD(strName, strScope)

	objCommand.CommandText = _
		"SELECT AdsPath FROM 'LDAP://" & _
		objRootLDAP.Get("defaultNamingContext") & "' " & _
		"WHERE objectCategory='" & strScope & "' " & _
		"AND samAccountName = '" & strName & "'"

	Set objRecordSet = objCommand.Execute
	If objRecordset.RecordCount = 0 then
		QueryAD = False
	Else
		QueryAD = True
	End If
End Function

' users
For i = 1 To counterUsers
	strName = strUserName & i
	If QueryAD(strName, "user") = False Then 
		Set objNewUser = objContainer.Create("User", "cn=" & strName)
		objNewUser.Put "sAMAccountName", strName
		objNewUser.Put "givenName", "testuser" & i
		objNewUser.Put "sn", "TestUser" & i
		objNewUser.Put "displayName", "TestUser" & i
		objNewUser.Put "Description", "AD User created by VB Script"
		objNewUser.Put "userAccountControl", 544
		objNewUser.SetInfo
		objNewUser.SetPassword "Univention.99"
		objNewUser.Put "PasswordExpired", CLng(1)
		objNewUser.AccountDisabled = FALSE
	End If
Next

' groups
For i = 1 To counterGroups
	strName = strGroupName & i
	If QueryAD(strName, "group") = False Then
		Set objNewGroup = objContainer.Create("Group", "cn=" & strName)
		objNewGroup.Put "sAMAccountName", strName
		objNewGroup.Put "Description", "AD User created by VB Script"
		objNewGroup.SetInfo
	End If
Next

' add users to group
intUsersInGroup = Int(counterUsers / counterGroups)
intStart = 1
For i = 1 to counterGroups
	Set objGroup = GetObject("LDAP://CN=" & strGroupName & i & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))
	For j = intStart to (intStart + intUsersInGroup)
		strName = strUserName & j
		Set objUser = GetObject("LDAP://CN=" & strName & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))
		If Not objGroup.IsMember(objUser.ADsPath) Then
			objGroup.add(objUser.ADsPath)
		End If
	Next
	intStart = intStart + intUsersInGroup
Next

' one user in all groups
For i = 1 to counterGroups
	Set objGroup = GetObject("LDAP://CN=" & strGroupName & i & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))
	Set objUser = GetObject("LDAP://CN=" & strUserName & "1" & ",CN=Users," & objRootLDAP.Get("defaultNamingContext"))
	If Not objGroup.IsMember(objUser.ADsPath) Then
		objGroup.add(objUser.ADsPath)
	End If
Next

MsgBox ("New Active Directory User created successfully by using VB Script...")
 
WScript.Quit
