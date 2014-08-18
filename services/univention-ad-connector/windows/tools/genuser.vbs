'
' Univention AD Connector
'  this scripts automatically generates users in the Active Directory
'
' Copyright 2004-2014 Univention GmbH
'
' http://www.univention.de/
'
' All rights reserved.
'
' The source code of this program is made available
' under the terms of the GNU Affero General Public License version 3
' (GNU AGPL V3) as published by the Free Software Foundation.
'
' Binary versions of this program provided by Univention to you as
' well as other copyrighted, protected or trademarked materials like
' Logos, graphics, fonts, specific documentations and configurations,
' cryptographic keys etc. are subject to a license agreement between
' you and Univention and not subject to the GNU AGPL V3.
'
' In the case you use this program under the terms of the GNU AGPL V3,
' the program is provided in the hope that it will be useful,
' but WITHOUT ANY WARRANTY; without even the implied warranty of
' MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
' GNU Affero General Public License for more details.
'
' You should have received a copy of the GNU Affero General Public
' License with the Debian GNU/Linux or Univention distribution in file
' /usr/share/common-licenses/AGPL-3; if not, see
' <http://www.gnu.org/licenses/>.

Option Explicit

'-------------------------------------------------------------------------
' usage:
'  genuser.vbs cn=Users,dc=addom,dc=de 10 <Salt>
'-------------------------------------------------------------------------

Dim i, username, StdOut, objRootDSE, objContainer, objusr
Dim shell, cmdLine, result, tmp, salt
Set shell = CreateObject("Wscript.Shell")
salt=""

' Setze CScript.exe als default
cmdLine = "%COMSPEC% /C cscript //H:CScript "
result = shell.Run(cmdLine,0,True)

Set StdOut = WScript.StdOut

If WScript.Arguments.Count=0 Then
	StdOut.WriteLine "Bitte OU und Anzahl angeben"
	StdOut.WriteLine "Bsp.: " & WScript.ScriptName & " cn=Users,dc=addom,dc=de 10 <Salt>"
	WScript.quit(255)
End If

If 	(WScript.Arguments.item(1)>999999) _
	OR  (WScript.Arguments.item(1) < 1 ) Then
	StdOut.WriteLine "Bitte zwischen 1 und 999999 User anlegen"
	WScript.quit(255)
End If

If (WScript.Arguments.Count<=2) Then
	StdOut.WriteLine "No Salt"
	salt=""
Else
	StdOut.WriteLine "Salt: " & WScript.Arguments.item(2)
	salt = WScript.Arguments.item(2)
End If

Set objRootDSE = GetObject("LDAP://rootDSE")
Set objContainer = GetObject("LDAP://"& WScript.Arguments.Item(0))

For i = 1 To WScript.Arguments.Item(1)
	username= Replace(Space(5-Int(Log(i)/Log(10)))," ","0") & i  ' führende Nullen
	StdOut.WriteLine "Schreibe User: " & username
	Set objusr = objContainer.Create("User", "cn=genuser" & salt & "-" & username)

' Allgemeine AD Informationen
	objusr.put "sAMAccountName", "genuser-" & username
	objusr.put "Description", "GenUser Script"
'	objusr.givenName = username
'	objusr.sn = "genuser"
'	objusr.displayName = "GenUser, " & username
' Und schreiben !!
	objusr.SetInfo

	objusr.setPassword "$dem0Gu1do"
	objusr.AccountDisabled = False
	objusr.SetInfo
	
	StdOut.WriteLine " - DONE"
Next
StdOut.WriteLine i-1 & " User erzeugt."

' Zurücksetzen, WScript.exe als default
cmdLine = "%COMSPEC% /C cscript //H:WScript "
result = shell.Run(cmdLine,0,True)

WScript.quit(0)
