Randomize
@!@
ldapserver = ""
ldapsearch = 'ldapsearch.exe'

if baseConfig['ldap/base']:
    print 'dim ldapsearchBaseDN : ldapsearchBaseDN = "%s"' % baseConfig['ldap/base']
else:
    print 'wscript.echo "Baseconfig-Variable ldap/base nicht gesetzt. Bitte informieren Sie Ihren Administrator."'
    print 'wscript.quit'

if baseConfig['printer/assignment/ldapserver']:
    ldapserver = baseConfig['printer/assignment/ldapserver']
else:
    if baseConfig['ldap/server/name']:
        ldapserver += " " + baseConfig['ldap/server/name']
    if baseConfig['ldap/server/addition']:
        ldapserver += " " + baseConfig['ldap/server/addition'].replace('"','')

ldapserverlist = []
for x in ldapserver.split(" "):
    if x:
        ldapserverlist.append(x)
ldapserver = ' '.join(ldapserverlist)

if len(ldapserver) == 0:
    print 'wscript.echo "Baseconfig-Variable printer/assignment/ldapserver nicht gesetzt. Bitte informieren Sie Ihren Administrator."'
    print 'wscript.quit'

if baseConfig['printer/assignment/ldapsearch']:
    ldapsearch = baseConfig['printer/assignment/ldapsearch']

if ldapsearch and ldapserver:
    print 'dim ldapserverlist: ldapserverlist = Split("%s")' % ldapserver
    print 'dim srvnum: srvnum = CInt(UBound(ldapserverlist) * Rnd + 0.49)'
    print 'dim ldapsearchCmd : ldapsearchCmd = "%s -x -LLL -h " & ldapserverlist(srvnum)' % ldapsearch

if baseConfig['printer/assignment/removeall'] and baseConfig['printer/assignment/removeall']=='yes':
    print 'dim flagRemoveAllPrinters: flagRemoveAllPrinters = 1'
else:
    print 'dim flagRemoveAllPrinters: flagRemoveAllPrinters = 0'

if baseConfig['printer/assignment/debug'] and baseConfig['printer/assignment/debug']=='yes':
    print 'dim showDebug: showDebug = 1'
else:
    print 'dim showDebug: showDebug = 0'
@!@

dim LOGONSERVER
set shell = createobject("wscript.shell")
LOGONSERVER = mid(shell.Environment("PROCESS")("LOGONSERVER"),3)

Set WshShell = WScript.CreateObject("WScript.Shell")
SESSIONNAME = WshShell.ExpandEnvironmentStrings("%SESSIONNAME%")
Set WshSysEnv = WshShell.Environment("SYSTEM")

COMPUTERNAME = WshShell.ExpandEnvironmentStrings("%COMPUTERNAME%")
Set WshSysEnv = WshShell.Environment("SYSTEM")

Set WshShell = WScript.CreateObject("WScript.Shell")
CLIENTNAME = WshShell.ExpandEnvironmentStrings("%CLIENTNAME%")

if CLIENTNAME = "Console" And SESSIONNAME = "Console" Then
  CLIENTNAME = COMPUTERNAME
End If

if CLIENTNAME = "%CLIENTNAME%" Then
  CLIENTNAME = COMPUTERNAME
End If


If Left(ldapsearchCmd,1) <> "\" Then
  ldapsearchCmd = "\\" & LOGONSERVER & "\netlogon\" & ldapsearchCmd
End If

Set WSHNetwork = WScript.CreateObject("WScript.Network")

if showDebug = 1 Then
  Wscript.echo "LDAPSEARCH: " & ldapsearchCmd
  Wscript.echo "COMPUTERNAME: " & COMPUTERNAME
  Wscript.echo "LOGONSERVER: " & LOGONSERVER
  wscript.echo "CLIENTNAME: " & CLIENTNAME
  Wscript.echo "SESSIONNAME: " & SESSIONNAME
End If

' remove if printers should be deleted before adding new ones
If flagRemoveAllPrinters = 1 Then
    RemoveAllPrinters()
End if

dim attrlist
dim clientdn
' get DN for CLIENTNAME
dim dnlist: dnlist = RunExternalCmd(ldapsearchCmd & " -b " & ldapsearchBaseDN & " (uid=" & CLIENTNAME & "$) dn")
dnlist = replace(dnlist, vbCrLf & " ", "")
if showDebug Then
  Wscript.echo "client dn: " & dnlist
end If
' extract requested attributes
attrlist = GetAttribute(dnlist,"dn")
' if attribute list is empty then quit
if UBound(attrlist) < 0 Then
   if showDebug Then
      Wscript.echo "cannot find dn of " & CLIENTNAME
   end If
   wscript.quit
End if
clientdn = attrlist(0)


' get assigned printers for CLIENTNAME
dim prnlist: prnlist = RunExternalCmd(ldapsearchCmd & " -b " & ldapsearchBaseDN & " ""(&(objectClass=univentionGroup)(uniqueMember=" & clientdn & ")(univentionAssignedPrinter=*))"" univentionAssignedPrinter")
prnlist = replace(prnlist, vbCrLf & " ", "")
if showDebug Then
  Wscript.echo "Assigned printers: " & prnlist
end If
' extract requested attributes
attrlist = GetAttribute(prnlist,"univentionAssignedPrinter")
' if attribute list is empty then quit
if UBound(attrlist) < 0 Then
  wscript.quit
End if

Dim defaultPrinterSet : defaultPrinterSet = 0

' get printerserver for each printer dn
for each prndn in attrlist
   dim prnout : prnout = RunExternalCmd(ldapsearchCmd & " -b " & prndn)
   prnout = replace(prnout, vbCrLf & " ", "")
   dim prnname : prnname = GetAttribute(prnout, "cn")
   dim prnspoolerlist : prnspoolerlist = GetAttribute(prnout, "univentionPrinterSpoolHost")
   for each prnspooler in prnspoolerlist
      'on error resume next

      if showDebug = 1 Then
         wscript.echo "SPOOLER of " & prndn & " is \\" & prnspooler & "\" & prnname(0)
      End If

      ' connect printer
      Set WshNetwork = CreateObject("WScript.Network")
      WshNetwork.AddWindowsPrinterConnection "\\" & prnspooler & "\" & prnname(0)
      If defaultPrinterSet = 0 Then
        WshNetwork.SetDefaultPrinter "\\" & prnspooler & "\" & prnname(0)
        defaultPrinterSet = 1
        if showDebug = 1 Then
          wscript.echo "Default printer is set to " & prnname(0) & " at " & prnspooler
        End If
      End if
   next
next

wscript.quit


sub RemoveAllPrinters()
  dim oPrinters, aPrinter
  Set objNetwork = WScript.CreateObject("Wscript.Network")
  Set oPrinters = objNetwork.EnumPrinterConnections
  For i = 0 to oPrinters.Count - 1 Step 2
     on error resume next
     aPrinter = split(uCase(oPrinters.Item(i+1)),"\",-1, 1)  '"
     if not UBound(aPrinter) = 0 then  'this is not a local printer, process code
        wscript.echo "PRINTER: " & aPrinter
        objNetwork.RemovePrinterConnection oPrinters.Item(i+1), True, True
        If Err.Number = 0 Then
           if showDebug = 1 Then
              wscript.echo "Success: Removed printer: " & oPrinters.Item(i+1)
           End If
        else
           if showDebug = 1 Then
             wscript.echo "Failed:  Removing printer: " & oPrinters.Item(i+1)
           end if
        end if
     end if
     aPrinter = ""
     on error goto 0
  next
end sub


Function GetAttribute(ByVal attrlist, attrname)
  dim outval : outval = ""
  dim lines : lines = split(attrlist, vbCrLf)
  for each line in lines
     'wscript.echo "LINE: " & line
     if left(line, len(attrname) + 2) = attrname & ": " Then
        if len(outval) > 0 Then
           outval = outval & vbCrLf
        End If
        outval = outval & mid(line, len(attrname)+3)
     End If
  next
  GetAttribute = split(outval, vbCrLf)
End Function


Function RunExternalCmd (ByVal cmd)
   Dim outp: outp = ""
   Dim sh: Set sh = CreateObject("WScript.Shell")
   Dim wsx: Set wsx = Sh.Exec(cmd)
   If wsx.ProcessID = 0 And wsx.Status = 1 Then
      ' (The Win98 version of VBScript does not detect WshShell.Exec errors)
      Err.Raise vbObjectError,,"WshShell.Exec failed."
   End If
   Do
      Dim Status: Status = wsx.Status
      outp = outp & wsx.StdOut.ReadAll() & wsx.StdErr.ReadAll()
      If Status <> 0 Then Exit Do
      WScript.Sleep 10
   Loop
   RunExternalCmd = outp
End Function

