# Univention AD-Connector

## General Operation

* By itself, the AD-Connector doesn't perform automatic reconciliation, i.e. it doesn't actively scan OpenLDAP
  and Active Directory to keep all objects in sync, neither during start up nor periodically.
* The AD-Connector only synchronizes a subset of all attributes, objects and OUs/containers. This subset is
  defined by the mapping.
* Customers must not adjust the `mapping.py` manually anymore (since UCS 5.0) and should instead create a `localmapping.py`.
* When the AD-Connector starts, it first syncs from UDM/OpenLDAP to Active Directory. But it doesn't re-sync everything
  at that point, it just waits for changes.
* Changes from the OpenLDAP site are communicated by the Listener module to AD-Connector via Python `pickle` files
  written into the directory `/var/lib/univention-connector/ad/`. The main loop of the AD-Connector periodically
  checks that directory.
* During each replication cycle, the AD-Connector first checks for changes from OpenLDAP and attempts to write them to
  Active Directory. If an object modification works, the `pickle` file gets removed. If the object modification fails,
  e.g. with a Python traceback, its DN is stored into a table `AD rejected` in `internal.sqlite` in the directory
  `/etc/univention/connector/`.
* During each replication cycle the AD-Connector polls the Active Directory via LDAP for changes (`usnChanged`/
  usnCreated` higher than the last value of `highestCommittedUSN` the AD-Connector has seen during the previous
  replication cycle.
  The last seen value of `highestCommittedUSN` is stored in `internal.sqlite`. The AD-Connector attempts to write
  the change to OpenLDAP. If possible it uses the python UDM API to write changes to OpenLDAP. If object modification
  fails, e.g. with a Python traceback, its DN is stored into a table `UCS rejected` in `internal.sqlite`.

## Developer Information

### Extending AD-Connector to synchronize additional attributes

Updates need special attention when extending ADC to synchronize additional attributes:

#### Active reconciliation for newly added attributes

* Adding new attributes to the AD-Connector mapping doesn't automatically sync all objects with those attributes
  during startup of the AD-Connector. Only for newly modified objects the new mapping is considered.
* Until now we trigger the initial synchronization by creating a script, e.g. `msGPOWQLFilter.py` in the S4-Connector
  which we called in the joinscript. For that the joinscript version needs to be increased, which must not be done
  during an errata update.
* A careful decision need to be made here. There are two options: Either you run the script to first sync from
  OpenLDAP to Active Directory, preferring values in OpenLDAP and possibly overwriting values in Active Directory
  customized by a MS/AD-Admin. The other option is to first trigger a sync from Active Directory to OpenLDAP,
  which may be preferable.
* See e.g. `git log -p --grep "remove msGPOWQLFilter.py"` in S4-Connector for an example how we handled this in the
  past.

Check list for DEV and QA:
==========================
* scripts/prepare-new-instance must work (Regression Bug #50713)
* Instances created with scripts/prepare-new-instance before the
  update must continue to work (see also Bug #51918)

Caveats:
========
* object['attributes'] may contain a mix of OL and AD attributes.
  This can be nasty for attributes like "mail", which exist
  in both object types.

* Warning: mapping of mail related attributes is especially nasty:
** git log --grep "Bug #51647: fix regression of Bug #18501"
** git log --grep "Bug #18501: Fix handling of proxyAddresses mapping"
** git log --grep "Bug #43216: Revised mapping for MS-Exchange related 'proxyAddresses'"

Improvement Suggestions:
========================
* Rename "object" and seprate object["attributes"] into "ldap_obj_ol" and "ldap_obj_ad"
  and pass them around to all functions (e.g. ucs_create_functions),
  so they have all required info, can pick the correct attribute values (OL vs AD) in searches
  and don't need to search stuff over and over again.
* Maybe replace "object" by a "obj_replication_state", which holds "ldap_obj_ol" and "ldap_obj_ad"
* Differenciate between "ldap_obj_ol_from_listener" and "ldap_obj_ol_current"
