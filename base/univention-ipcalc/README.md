`univention-ipcalc{,6} --calcdns` is used to create DNS reverse zones in UDM.

This is often done indirectly via `/usr/share/univention-directory-manager-tools/univention-dnsedit`

UDM expects the network name as "subnet" in forward notation `(1.2, 0000:1111:2222:3333)` and internally converts that to the backward notation as used in DNS `(2.1.in-addr.arpa, 3.3.3.3.2.2.2.2.1.1.1.1.0.0.0.0.ip6.arpa)`

```
--output network
    Network address in forward notation.
    IPv4: 0-4 octets
    IPv6: 0-32 nibbles

--output reverse
    Network address in forward notation suitable for DNS.
    IPv4: 1-3 octets
    IPV6: 1-31 nibbles

--output pointer
    Host address in reverse notation.
    IPv1: 3-1 octets
    IPv6: 31-1 nibbles
```

```
base/univention-system-setup/usr/lib/univention-system-setup/scripts/net/10interfaces
base/univention-system-setup/usr/lib/univention-system-setup/scripts/net/11ipv6interfaces
    ipcalc{,6} {reverse,pointer}
    using univention-dnsedit to create reverse zone and ptr entry within.

management/univention-join/univention-server-join
    ipcalc network
    using udm to create ptr entry for host

management/univention-ldap/10univention-ldap-server.inst
    ipcalc6 reverse
    using univention-dnsedit to create reverse zone

services/univention-bind/05univention-bind.inst
    ipcalc6 {reverse,pointer}
    using univention-dnsedit to create reverse zone and ptr entry within.
```
