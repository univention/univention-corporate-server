Set objSysInfo = CreateObject( "ADSystemInfo" )
arrComputerName = Split(objSysInfo.ComputerName, "=", -1)
ComputerName = Split(arrComputerName(1), ",", 2)(0)
WScript.Echo "Computername: " & ComputerName
