$ErrorActionPreference = "Stop"
$NICs = Get-WMIObject Win32_NetworkAdapterConfiguration -computername . -ErrorAction Stop | where{$_.IPEnabled -eq "TRUE"}
$DNSServers = "%(dns_server)s"
Foreach($NIC in $NICs) {
        $x = $NIC.SetDNSServerSearchOrder($DNSServers)
        if ($x.ReturnValue -ne 0) {
                Throw "SetDNSServerSearchOrder failed"
        }
}

