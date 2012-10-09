Sub DoWaitForDevices()
  strComputer = "."
  Set objWMIService = GetObject("winmgmts:\\" & strComputer & "\root\cimv2")

  Set colMonitoredEvents = objWMIService.ExecNotificationQuery _
    ("SELECT * FROM __InstanceOperationEvent WITHIN 5 WHERE " _
        & "Targetinstance ISA 'Win32_PnPEntity'")
  
  Set colItems = objWMIService.ExecQuery _
    ("Select * from Win32_PnPEntity WHERE DeviceID LIKE 'XEN\\%' OR DeviceID LIKE 'PCI\\VEN_5853&DEV_0001%'")
  
  XenExistsFlag = False

  For Each objItem in colItems
    If AreWeOkay(objItem) Then
      XenExistsFlag = True
      Exit For
    End If
  Next

  Do While Not XenExistsFlag
    Set objEventObject = colMonitoredEvents.NextEvent()
    Set objItem = objEventObject.Targetinstance
    If AreWeOkay(objItem) Then
      XenExistsFlag = True
    End If
  Loop
End Sub


Function AreWeOkay(objItem)
  AreWeOkay = False
  If LCase(Left(objItem.DeviceID, 4)) = "xen\" Then
    ' At least one Xen\* item has been enumerated
    AreWeOkay = True
    Exit Function
  End If
  If LCase(Left(objItem.DeviceID, 21)) = "pci\ven_5853&dev_0001" Then
    If objItem.ConfigManagerErrorCode = 28 And LCase(objItem.Service) = "xenpci" Then
      ' Probably we need a reboot here... assume we're installed
      AreWeOkay = True
      Exit Function
    End If
  End If
End Function
