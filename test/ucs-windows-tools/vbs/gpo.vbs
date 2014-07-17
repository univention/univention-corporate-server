'Set WshShell = CreateObject("Wscript.Shell")
'Result = WshShell.Run("gpupdate /force",0,true)

Set gpm = CreateObject( "GPMGMT.GPM" )
Dim Constants : Set Constants = GPM.GetConstants()
Set gpmRSOP = gpm.GetRSOP( Constants.RSOPModeLogging, "", 0 )
'gpmRSOP.LoggingFlags=Constants.RsopLoggingNoUser
gpmRSOP.LoggingComputer = "."
gpmRSOP.LoggingUser = "w2k12.test\Administrator"
gpmRSOP.CreateQueryResults()
Set gmpResult = gpmRSOP.GenerateReport( Constants.ReportXML )
Wscript.echo gmpResult.result
gpmRSOP.ReleaseQueryResults()

'Function getGPOHTMLReport(strDomain, strGPOCN)
'  Set objGPM = CreateObject("GPMgmt.GPM")
' Set objGPMConstants = objGPM.GetConstants()
' Set objGPMDomain = objGPM.GetDomain(strDomain, "", objGPMConstants.UseAnyDC)
'     Set objGPO = objGPMDomain.GetGPO(strGPOCN)
'     Set objGPMReport = objGPO.GenerateReport(objGPMConstants.ReportHTML)
'     getGPOHTMLReport = objGPMReport.result
'   End Function
'Wscript.echo getGPOHTMLReport("w2k12.test", "{3746100450-113509357-4236447858-500}")



'' computer gpo
'strComputer = "."
'Set objWMIService = GetObject("winmgmts:\\" & strComputer & "\root\rsop\computer")
'Set colItems = objWMIService.ExecQuery("Select * from RSOP_GPO")
'For Each objItem in colItems  
'    Wscript.Echo "Name: " & objItem.Name
'    Wscript.Echo "GUID Name: " & objItem.GUIDName
'    Wscript.Echo "ID: " & objItem.ID
'    Wscript.Echo "Access Denied: " & objItem.AccessDenied
'    Wscript.Echo "Enabled: " & objItem.Enabled
'    Wscript.Echo "File System path: " & objItem.FileSystemPath
'    Wscript.Echo "Filter Allowed: " & objItem.FilterAllowed
'    Wscript.Echo "Filter ID: " & objItem.FilterId
'    Wscript.Echo "Version: " & objItem.Version
'    Wscript.Echo
'Next
'
'Function getSid()
'	Set net = CreateObject("WScript.Network")
'	Set wmi = GetObject("winmgmts://./root/cimv2")
'	Set objAccount = wmi.Get("Win32_UserAccount.Name='" & net.Username & "',Domain='" & net.UserDomain & "'")
'	getSID = objAccount.SID
'End Function
'
'SID = getSid()
'
'strComputer = "."
'Set objWMIService = GetObject("winmgmts:{impersonationLevel=impersonate}!\\" & strComputer & "\root\cimv2")
'strWMISID = replace (SID,"-","_")
'Set objWMIService = Nothing
'Set objWMIService = GetObject("winmgmts:{impersonationLevel=impersonate}!\\" & strComputer & "\root\rsop\user\" & strWMISID)
'Set colItems = objWMIService.ExecQuery("Select * from RSOP_GPO")
'For Each objItem In colItems
'Wscript.Echo "Name: " & objItem.Name
'Wscript.Echo "GUID Name: " & objItem.GUIDName
'Wscript.Echo "ID: " & objItem.ID
'Wscript.Echo "Access Denied: " & objItem.AccessDenied
'Wscript.Echo "Enabled: " & objItem.Enabled
'Wscript.Echo "File System path: " & objItem.FileSystemPath
'Wscript.Echo "Filter Allowed: " & objItem.FilterAllowed
'Wscript.Echo "Filter ID: " & objItem.FilterId
'Wscript.Echo "Version: " & objItem.Version
'Wscript.Echo
'Next
'
'' ------ SCRIPT CONFIGURATION ------
'strDomain = "w2k12.test" ' e.g. rallencorp.com
'' ------ END CONFIGURATION --------
'
'set objGPM = CreateObject("GPMgmt.GPM")
'set objGPMConstants = objGPM.GetConstants( )
'
'' Initialize the Domain object
'set objGPMDomain = objGPM.GetDomain(strDomain, "", objGPMConstants.UseAnyDC)
'
'' Create an empty search criteria
'set objGPMSearchCriteria = objGPM.CreateSearchCriteria
'set objGPOList = objGPMDomain.SearchGPOs(objGPMSearchCriteria)
'
'' Print the GPOs
'WScript.Echo "Found " & objGPOList.Count & " GPOs in " & strDomain & ":"
'for each objGPO in objGPOList
'   WScript.Echo "   " & objGPO.DisplayName
'next
