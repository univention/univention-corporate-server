'#
'# Warning: This file is auto-generated and might be overwritten by
'#          univention-baseconfig.
'#          Please edit the files in the following directory instead:
'# Warnung: Diese Datei wurde automatisch generiert und kann durch
'#          univention-baseconfig ueberschrieben werden.
'#          Bitte bearbeiten Sie an Stelle dessen die Dateien in
'#          folgendem Verzeichnis:
'#
'#       /etc/univention/templates/files/var/lib/samba/netlogon/univention-netlogon-proxy.vbs
'#

'
' set constants (maybe changed by baseconfig)
'

@!@
host = "%s.%s" % (baseConfig['hostname'], baseConfig['domainname'])
if baseConfig.has_key('samba/netlogonscript/proxy/host') and baseConfig['samba/netlogonscript/proxy/host']:
    host = baseConfig['samba/netlogonscript/proxy/host']

print 'PROXYHOST = "%s"' % host

port = 3128
if baseConfig.has_key('samba/netlogonscript/proxy/port') and baseConfig['samba/netlogonscript/proxy/port']:
    port = baseConfig['samba/netlogonscript/proxy/port']

print 'PROXYPORT = "%s"' % port

whitelist = "localhost 127.0.0.1 %s.%s" % (baseConfig['hostname'], baseConfig['domainname'])
if baseConfig.has_key('samba/netlogonscript/proxy/whitelist') and baseConfig['samba/netlogonscript/proxy/whitelist']:
    whitelist = baseConfig['samba/netlogonscript/proxy/whitelist']

print 'PROXYWHITELIST = "%s"' % whitelist

firefox_enabled = 'True'
if baseConfig.has_key('samba/netlogonscript/proxy/enable/firefox'):
    if not baseConfig['samba/netlogonscript/proxy/enable/firefox'].lower() in [ 'yes', 'true', '1' ]:
        firefox_enabled = 'False'
print 'ENABLEDFIREFOX = %s' % firefox_enabled

IE_enabled = 'True'
if baseConfig.has_key('samba/netlogonscript/proxy/enable/iexplorer'):
    if not baseConfig['samba/netlogonscript/proxy/enable/iexplorer'].lower() in [ 'yes', 'true', '1' ]:
        IE_enabled = 'False'
print 'ENABLEDIEXPLORER = %s' % IE_enabled
@!@

Const ForReading = 1, ForWriting = 2, ForAppending = 8

'user_pref("network.proxy.ftp", "10.101.118.2");
'user_pref("network.proxy.ftp_port", 8080);
'user_pref("network.proxy.gopher", "10.101.118.2");
'user_pref("network.proxy.gopher_port", 8080);
'user_pref("network.proxy.http", "10.101.118.2");
'user_pref("network.proxy.http_port", 8080);
'user_pref("network.proxy.no_proxies_on", "localhost, 127.0.0.1, dc011, 10.101.118.0/24");
'user_pref("network.proxy.share_proxy_settings", true);
'user_pref("network.proxy.ssl", "10.101.118.2");
'user_pref("network.proxy.ssl_port", 8080);
'user_pref("network.proxy.type", 1);

' INDEX
' 0 = regex
' 1 = complete entry
' 2 = "entry changed" flag

' WARNING: please adjust '12' if a new regular expression has been added
REGEXCNT = 12
Dim regex_list(12,3)
regex_list(0,0) = "(user_pref\(""network.proxy.ftp"", ""[^""]+""\);)"
regex_list(0,1) = "user_pref(""network.proxy.ftp"", """ & PROXYHOST & """);"
regex_list(0,2) = False

regex_list(1,0) = "(user_pref\(""network.proxy.ftp_port"", [0-9]+\);)"
regex_list(1,1) = "user_pref(""network.proxy.ftp_port"", " & PROXYPORT & ");"
regex_list(1,2) = False

regex_list(2,0) = "(user_pref\(""network.proxy.http"", ""[^""]+""\);)"
regex_list(2,1) = "user_pref(""network.proxy.http"", """ & PROXYHOST & """);"
regex_list(2,2) = False

regex_list(3,0) = "(user_pref\(""network.proxy.http_port"", [0-9]+\);)"
regex_list(3,1) = "user_pref(""network.proxy.http_port"", " & PROXYPORT & ");"
regex_list(3,2) = False

regex_list(4,0) = "(user_pref\(""network.proxy.gopher"", ""[^""]+""\);)"
regex_list(4,1) = "user_pref(""network.proxy.gopher"", """ & PROXYHOST & """);"
regex_list(4,2) = False

regex_list(5,0) = "(user_pref\(""network.proxy.gopher_port"", [0-9]+\);)"
regex_list(5,1) = "user_pref(""network.proxy.gopher_port"", " & PROXYPORT & ");"
regex_list(5,2) = False

regex_list(6,0) = "(user_pref\(""network.proxy.socks"", ""[^""]+""\);)"
regex_list(6,1) = "user_pref(""network.proxy.socks"", """ & PROXYHOST & """);"
regex_list(6,2) = False

regex_list(7,0) = "(user_pref\(""network.proxy.socks_port"", [0-9]+\);)"
regex_list(7,1) = "user_pref(""network.proxy.socks_port"", " & PROXYPORT & ");"
regex_list(7,2) = False

regex_list(8,0) = "(user_pref\(""network.proxy.ssl"", ""[^""]+""\);)"
regex_list(8,1) = "user_pref(""network.proxy.ssl"", """ & PROXYHOST & """);"
regex_list(8,2) = False

regex_list(9,0) = "(user_pref\(""network.proxy.ssl_port"", [0-9]+\);)"
regex_list(9,1) = "user_pref(""network.proxy.ssl_port"", " & PROXYPORT & ");"
regex_list(9,2) = False

regex_list(10,0) = "(user_pref\(""network.proxy.type"", [0-9]+\);)"
regex_list(10,1) = "user_pref(""network.proxy.type"", 1);"
regex_list(10,2) = False

wlist = replace(PROXYWHITELIST, " ", ", ")
regex_list(11,0) = "(user_pref\(""network.proxy.no_proxies_on"", ""[^""]+""\);)"
regex_list(11,1) = "user_pref(""network.proxy.no_proxies_on"", """ & wlist & """);"
regex_list(11,2) = False

'
' get required environment variables
'
Set fso = CreateObject("Scripting.FileSystemObject")

Set WshShell = WScript.CreateObject("WScript.Shell")

APPDATA = WshShell.ExpandEnvironmentStrings("%APPDATA%")

TMPDIR = WshShell.ExpandEnvironmentStrings("%TEMP%")
If TMPDIR = "" Then
  TMPDIR = WshShell.ExpandEnvironmentStrings("%TMP%")
End If


'
' setup logging
'
Set debugf = fso.OpenTextFile(TMPDIR & "\netlogon-set-proxy.log", ForAppending, True)

'
' only set proxy if firefox is enabled
'
If ENABLEDFIREFOX = True Then
    
    '
    ' check if user has all needed firefox profile directories
    '
    Dim dirList
    dirname = APPDATA
    dirList = split( "Mozilla\Firefox\Profiles", "\")
    For Each folder in dirList
      dirname = dirname & "\" & folder
      If Not fso.FolderExists( dirname ) Then
        debugf.WriteLine( "WARNING: creating directory " & dirname )
        fso.CreateFolder( dirname )
      End If
    Next
    
    '
    ' create firefox profile if missing
    '
    profini = APPDATA & "\Mozilla\Firefox\profiles.ini"
    If Not fso.FileExists( profini ) Then
      debugf.WriteLine( "WARNING: creating new profile: " & profini )
      ' create profiles.ini if non-existent
      Set f = fso.OpenTextFile( profini, ForWriting, True)
      f.WriteLine("[General]")
      f.WriteLine("StartWithLastProfile=1")
      f.WriteLine("")
      f.WriteLine("[Profile0]")
      f.WriteLine("Name=default")
      f.WriteLine("IsRelative=1")
      f.WriteLine("Path=Profiles/x99grm2l.default")
      f.Close
      ' create new profile folder
      fso.CreateFolder( APPDATA & "\Mozilla\Firefox\Profiles\x99grm2l.default" )
      ' create new prefs.js
      prefs = APPDATA & "\Mozilla\Firefox\Profiles\x99grm2l.default\prefs.js"
      Set f = fso.OpenTextFile( prefs, ForWriting, True)
      f.WriteLine("user_pref(""network.proxy.type"", 1);")
      f.Close
    End If
    
    '
    ' check for existing profiles
    '
    Dim profilenames 
    profilenames = getProfileNameArray( APPDATA & "\Mozilla\Firefox\Profiles\" , "\prefs.js" )
    changed = False
    For Each profname In profilenames
    '  wscript.echo profname
      path = fso.GetAbsolutePathName( profname )
    
      If fso.FileExists(profname) Then
        ' read content
        Set f = fso.OpenTextFile(profname, ForReading, True)
        content = ""
        Do While Not f.AtEndOfStream
          line = f.ReadLine 
          ' change lines if neccessary
          line = handleConfigLine( line )
          content = content & "<***UniventionLineWrapper***>" & line
        Loop
        f.close
    
        ' write content
        Set f = fso.OpenTextFile(profname, ForWriting, True)
        For Each line In split(content, "<***UniventionLineWrapper***>")
            f.WriteLine(line)
        Next
    
        ' write missing lines
        For i = 0 To ( REGEXCNT - 1 )
          If regex_list(i,2) <> True Then
            f.WriteLine( regex_list(i,1) )
          End If
        Next
    
        changed = True
      Else
        debugf.WriteLine( "WARNING: firefox profile " & profname & " not found" )
      End If
    Next
    
    If Not changed Then
      debugf.WriteLine( "ERROR: no firefox profile present" )
    End If
End If


'
' only set proxy if firefox is enabled
'
If ENABLEDIEXPLORER = True Then
    '
    ' create temporary registry file and add it to registry
    '
    
    ' [HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings]
    ' "ProxyEnable"=dword:00000001
    ' "ProxyServer"="10.200.18.30:12345"
    ' "ProxyOverride"="localhost; 127.0.0.1; dc002; adam.schule.bremen.de"
    
    wlist = replace(PROXYWHITELIST, " ", "; ")
    regfile = TMPDIR & "\set-proxy.reg"
    Set f = fso.OpenTextFile( regfile, ForWriting, True, True)
    f.WriteLine("Windows Registry Editor Version 5.00")
    f.WriteLine("")
    f.WriteLine("[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings]")
    f.WriteLine("""ProxyEnable""=dword:00000001")
    f.WriteLine("""ProxyServer""=""" & PROXYHOST & ":" & PROXYPORT & """")
    f.WriteLine("""ProxyOverride""=""" & wlist & """")
    f.Close
    
    runExternalCmd( "regedit.exe /S " & regfile )
End If    
    
debugf.Close 

wscript.quit

'------------------------------------------------------------
'
'                    HELPER FUNCTIONS
'
'------------------------------------------------------------

Function handleConfigLine(ByVal line)
  Set regEx = New RegExp
  regEx.IgnoreCase = True
  regEx.Global = True
  regEx.MultiLine = False

  ' iterate over all regex entrys
  For i = 0 to ( REGEXCNT - 1 )
    regEx.Pattern = regex_list(i,0)

    ' find line
    Set currentMatches = regEx.Execute(line)
    If currentMatches.Count >= 1 Then
      ' replace line with new value
      line = regEx.Replace( line, regex_list(i,1) )
      regex_list(i,2) = True
    End If
  Next
  handleConfigLine = line
End Function


Function getProfileNameArray(ByVal folder, suffix)
  Dim fso, f
  Set fso = CreateObject("Scripting.FileSystemObject")
  Set f = fso.GetFolder( folder )
  resultstr = ""
  For Each folderIdx In f.subfolders
    If resultstr <> "" Then
       resultstr = resultstr & "<br>"
    End If
    resultstr = resultstr & folder & folderIdx.Name & suffix
  Next
  getProfileNameArray = split( resultstr, "<br>" )
End Function


Function runExternalCmd (ByVal cmd)
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
