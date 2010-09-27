@echo off

%SYSTEMROOT%\UCS-AD-Connector\ucs-ad-connector.exe -install
net start "UCS AD Connector"
sc config "UCS AD Connector" start= auto

