# Univention S4 Connector

## General Operation

* By itself, the S4-Connector doesn't perform automatic reconciliation, i.e. it doesn't actively scan OpenLDAP
  and Samba/AD to keep all objects in sync, neither during start up nor periodically.
* The S4-Connector only synchronizes a subset of all attributes, objects and OUs/containers. This subset is
  defined by the mapping.
* Customers must not adjust the `mapping.py` manually anymore (since UCS 5.0) and should instead create a `localmapping.py`.
* When the S4-Connector starts, it first syncs from UDM/OpenLDAP to Samba/AD. But it doesn't re-sync everything at that
  point, it just waits for changes.
* Changes from the OpenLDAP site are communicated by the Listener module to S4-Connector via Python `pickle` files
  written into the directory `/var/lib/univention-connector/s4/`. The main loop of the S4-Connector periodically
  checks that directory.
* During each replication cycle, the S4-Connector first checks for changes from OpenLDAP and attempts to write them to
  Samba/AD. If an object modification works, the `pickle` file gets removed. If the object modification fails,
  e.g. with a Python traceback, its DN is stored into a table `S4 rejected` in `s4internal.sqlite` in the directory
  `/etc/univention/connector/`.
* During each replication cycle the S4-Connector polls the Samba/AD-LDAP for changes (`usnChanged`/`usnCreated` higher
  than the last value of `highestCommittedUSN` the S4-Connector has seen during the previous replication cycle.
  The last seen value of `highestCommittedUSN` is stored in `s4internal.sqlite`. The S4-Connector attempts to write
  the change to OpenLDAP. If possible it uses the Python UDM API to write changes to OpenLDAP. If object modification
  fails, e.g. with a Python traceback, its DN is stored into a table `UCS rejected` in `s4internal.sqlite`.

## Developer Information

### Extending S4-Connector to synchronize additional attributes

Udpates need special attention when extending S4C to synchronize additional attributes:

#### Active reconciliation for newly added attributes

* Adding new attributes to the S4-Connector mapping doesn't automatically sync all objects with those attributes
  during startup of the S4-Connector. Only for newly modified objects the new mapping is considered.
* Until now we trigger the initial synchronization by creating a script, e.g. `msGPOWQLFilter.py`, which we
  called in the joinscript. For that the joinscript version needs to be increased, which must not be done
  during an errata update.
* A careful decision need to be made here. There are two options: Either you run the script to first sync from
  OpenLDAP to Samba/AD, preferring values in OpenLDAP and possibly overwriting values in Samba/AD customized by
  a MS/AD-Admin. The other option is to first trigger a sync from Samba/AD to OpenLDAP, which may be preferable.
* Special care needs to be taken for UCS@school environments to avoid a situation where e.g. one School site server
  has already been updated, its S4-Connector now running with the new mapping, and then the next School site server
  updates and its S4-Connector overwrites the customized attribute values in the second School site server (not
  good). Or, if you decided to trigger the sync from Samba/AD to OpenLDAP first, then it's even worse: When
  the joinscript runs on the second School site server, this may cause values from that schools Samba/AD to flow
  to the Samba/AD in the central school department, possibly causing a sudden, unexpected, unintended change,
  e.g. of domain wide policies. And next this flows to the first School site server (and all others that already
  have been updated). As a result, the update script should treat UCS@school site servers differently than
  the central S4-Connector and first write OpenLDAP values to Samba/AD. This has to be considered on a case
  by case basis. If no domain wide objects are affected (e.g. only objects below a School OU) then it's probably
  preferable to sync from Samba/AD to OpenLDAP fists on the School servers, to avoid overwriting values
  customized in Samba/AD by a MS/AD School admin.
* See e.g. `git log -p --grep "remove msGPOWQLFilter.py"` for an example how we handled this in the past.

