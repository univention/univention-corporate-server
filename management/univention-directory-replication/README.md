OIDs
====

OIDs are a distributed naming scheme.
They are used most by SNMP and LDAP schema.
In addition to multiple names each LDAP objectClass, attributeType each have a unique OID.
In addition to LDAP schema files OpenDLAP itself includes several built-in schema.
They are automatically enabled when certain modules are loaded.

Care must be taken to not define a schema twice as otherwise `slapd` refuses to start.
[replication.py](replication.py) replicates the schema from the Primary below `cn=Subschema`.
It includes all entries from both schema files and OpenLDAP internal schema.
Those must be filtered out.

For that [replication.py](replication.py) has a built-in list of OIDs to exclude: `BUILTIN_OIDS`.
They are listed in the file [oid_skip.txt](oid_skip.txt).
The file is compiled to `/usr/share/univention-ldap/oid_skip` during package build time.
That file is then loaded by [replication.py](replication.py) when the UDL module is loaded.

[oid_skip.py](oid_skip.py) can be used to extract all OIDs defined by OpenLDAP.
It starts a dummy `slapd` and all modules one at a time to extract the schema definition.
They should be merged into [oid_skip.txt](oid_skip.txt).

Newer versions of OpenLDAP may also remove OIDs when functions are deprecated.
For now they should not be removed.

The file may also be used by `slapd.postinst` to make sure, that the listed OIDs are excluded.
