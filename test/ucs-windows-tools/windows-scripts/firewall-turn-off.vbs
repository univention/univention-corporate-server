' maybe better use ...
' netsh advfirewall set allprofiles state off
' netsh advfirewall set allprofiles state on

option explicit
Const NET_FW_PROFILE2_DOMAIN = 1
Const NET_FW_PROFILE2_PRIVATE = 2
Const NET_FW_PROFILE2_PUBLIC = 4

Dim fwPolicy2
Set fwPolicy2 = CreateObject("HNetCfg.FwPolicy2")
fwPolicy2.FirewallEnabled(NET_FW_PROFILE2_DOMAIN) = FALSE
fwPolicy2.FirewallEnabled(NET_FW_PROFILE2_PRIVATE) = FALSE
fwPolicy2.FirewallEnabled(NET_FW_PROFILE2_PUBLIC) = FALSE

wscript.quit 0
