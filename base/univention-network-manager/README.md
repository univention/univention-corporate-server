# Defining nameservers via DHCP #

UCS systems are able to automatically use nameservers that are transmitted to the UCS system via DHCP.

This mechanism can be disabled completely by setting the UCR variable `nameserver/external=true`.

Note: In UCS 4.x the hook `/etc/dhcp/dhclient-exit-hooks.d/resolvconf` is used, which has a different behavior!

Starting with UCS 5.0-0 the mechanism has been simplified considerably. The exit hook has been removed
and replaced with the new hook `/etc/dhcp/dhclient-enter-hooks.d/resolvconf`.
The new mechanism stops the automatic update of `/etc/resolv.conf` via dhclient and instead ensures
that the UCR variables are set as correctly as possible based on heuristics. Setting the UCR variables
then automatically re-evaluates the UCR template for `/etc/resolv.conf` and thus updates the target
file.

In the case of a joined UCS system with one of the roles "Primary Directory Node", "Backup Directory Node"
or "Replica Directory Node", the nameservers passed by the DHCP server are first actively tested.
This is done by the helperscript [/usr/share/univention-server/univention-fix-ucr-dns](../univention-server/univention-fix-ucr-dns). For each
name server it is tested whether it knows the SRV record `_domaincontroller_master._tcp.` for the Primary Directory Node of the local domain
(`ucr get domainname`). If this is the case, it is assumed that it is a DNS server on a UCS system and
the IP address is entered in `nameserver1`, `nameserver2` or `nameserver3`.
If the DNS server returns a `NXDOMAIN` for the SRV record (entry not known), the IP address is entered
in `dns/forwarder1`, `dns/forwarder2` or `dns/forwarder3`. Please note: if the DNS server is not
available/offline, the DNS server will still be entered in `nameserver1`, `nameserver2` or `nameserver3`.

Since a DNS server is also installed on the local system, the local IP address is automatically entered
in `nameserver1` if it was NOT transmitted via DHCP. Otherwise, the local system is not necessarily in
the variable `nameserver1`.

If it is not a Primary/Backup/Replica Directory Node or if the UCS system has not yet joined the domain, the
nameservers transferred via DHCP are only transferred to the UCR variables `nameserver1` to `nameserver3`.
The IP address of the local system is NOT automatically added to the list of nameservers.

At the start of this evaluation, all DNS servers already configured via UCR (`nameserverX` and
`dns/forwarderX`) are ignored and discarded, regardless of join status and system role.


    IN CASE OF DHCP, THE EXISTING  | Add self to    Add ns to       Add ns to
    UCR CONFIG IS NEVER USED!      | resolv.conf    nameserverX     dns/forwarderX
    -------------------------------|-----------------------------------------------
    Primary Domain Node (joined)   |     X          X (heuristic)   X (heuristic)
    Backup Domain Node (joined)    |     X          X (heuristic)   X (heuristic)
    Replica Domain Node (joined)   |     X          X (heuristic)   X (heuristic)
    Managed Node (joined)          |     -          X               -
    Primary Domain Node (unjoined) |     -          X               -
    Backup Domain Node (unjoined)  |     -          X               -
    Replica Domain Node (unjoined) |     -          X               -
    Managed Node (unjoined)        |     -          X               -
