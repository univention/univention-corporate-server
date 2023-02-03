from univention.uldap import getMachineConnection

lo = getMachineConnection()
for dn, attr in lo.search("(cn=admin)", attr=["dn"]):
    print(dn)
for dn in lo.searchDn("(cn=admin)"):
    print(dn)
