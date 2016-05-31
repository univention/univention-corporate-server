ps = '''
$ErrorActionPreference = "Stop"
$NICs = Get-WMIObject Win32_NetworkAdapterConfiguration -computername . -ErrorAction Stop | where{$_.IPEnabled -eq "TRUE"}
$DNSServers = "%(dnsserver)s"
Foreach($NIC in $NICs) {
        $x = $NIC.SetDNSServerSearchOrder($DNSServers)
        if ($x.ReturnValue -ne 0) {
                Throw "SetDNSServerSearchOrder failed"
        }
}
'''

description = 'Set dns server for all non DHCP interfaces'

name = 'set_dns_server'

args = dict(
	dnsserver=dict(help='DNS Server ip'),
)
