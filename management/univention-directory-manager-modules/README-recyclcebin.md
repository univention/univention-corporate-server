This document describes implementation notices for the Recyclebin feature in UDM.

[TOC]

# (Re)moving Objects to the RecycleBin

## Object representation

The recyclebin is located in a secondary LDAP database under `cn=internal`.
This ensures that deleted objects are no longer visible through regular LDAP searches, preventing applications that use generic LDAP filters from returning deleted entries.

Recycle bin objects retain their original LDAP structure, except for LDAP operational attributes, and use the `extensibleObject` object class.
This allows regular LDAP tools to operate on them without requiring schema mapping or serialization formats (such as JSON blobs) that could break binary attribute encodings (e.g. `jpegPhoto`).

Objects are created below `cn=recyclebin,cn=internal` with the original DN and original object identifier encoded as the first multivalued RDN, for example:

```
univentionRecycleBinOriginalDN=uid\=Test\,cn\=users\,dc\=example\,dc\=org+univentionObjectIdentifier=43026e47-f1e8-4e85-bc87-b3adde0b3f4d,cn=recyclebin,cn=internal
```

This makes lookups straightforward (at least before the UOI was added).

Each recyclebin object includes metadata such as:

* Original UDM object type
* Original DN
* Original `univentionObjectIdentifier`
* Original `entryUUID`
* Original list of object classes
* Deletion timestamp
* Expiration timestamp (when it will be permanently removed)
* References from other objects that pointed to this object
* (Optionally) author DN - currently unavailable because listener modules lack that information

## Automatic removal via LDAP

Recyclebin objects also have the `dynamicObject` object class, provided by the Dynamic Directory Services (DDS) overlay module.
Their lifetime is defined via the operational attribute `entryTtl`, specified in seconds from now.

When the object expires, OpenLDAP logs the removal if the `STATS` log level is enabled.
The log entry appears in syslog at `INFO` level, for example:

```
DDS dn="univentionRecycleBinOriginalDN=uid\=Test\,cn\=users\,dc\=example\,dc\=org+univentionObjectIdentifier=43026e47-f1e8-4e85-bc87-b3adde0b3f4d,cn=recyclebin,cn=internal"
```

This approach eliminates the need for scheduled cleanup jobs.

## Ensurance of uniqueness
If, for example, a `uid=exam-foo,...` was removed, later on a similar object re-added with the same DN, and finally removed again the corresponding recyclebin entry would already exists.
By adding the `univentionObjectIdentifier` to the DN of the recyclebin object, it was ensured that even those entries can be added to the recyclebin.

## Implementation via Listener module

The move of objects into the recyclebin is implemented using a listener module.

**Reasoning:**
UDM code may run on different machines than the DC Primary and uses the credentials of the currently logged-in user.
Allowing these components direct write access to the recyclebin would create a security risk - e.g., a user could inject fake references (like adding themselves to "Domain Admins") and later restore to gain elevated privileges.
Therefore, only the DC Primary, via a listener module, performs the "move" operation.

The listener runs asynchronously, so it doesn't affect UDM performance.
It also provides a form of atomicity by processing all LDAP changes resulting from overlays such as `refint`, ensuring complete and consistent state transitions that UDM itself cannot guarantee.

### Listener Cache limitation

The listener may not always have an up-to-date view of an object's state.
Each listener maintains a cache of object attributes. If an object is modified shortly before deletion, and the notifier has not yet propagated those changes, the listener cache may be outdated.
As a result, an inaccurate version of the object could be moved to the recyclebin.

Similarly, if an object is created and deleted in rapid succession, the listener may never see the object, and nothing will be moved to the recyclebin.

### Recommended LDAP overlay approach

Ideally, the listener module should be replaced with an LDAP overlay module.
This could either:

* Implement an LDAP **extended operation** to perform the move instead of a regular delete, or
* Support a **custom LDAP control**, e.g. `"move-to-recyclebin"`, passed with the delete request and the intended retention time.

## Reference handling

LDAP supports various reference types, such as forward references (e.g. `secretary`, `memberOf`) and backward references (e.g. `uniqueMember`).
UDM does not expose these references declaratively - only through business logic - so generic handling is limited.
Currently, only `users/user` and `groups/group` object types are supported.
Custom extended attributes and hooks are not.

References are stored in the recyclebin object using a URL-encoded format, for example:

```
univentionRecycleBinReference=dn:groups/group:users:uuid:550e8400-e29b-41d4-a716-446655440000
```

This means:
The deleted object's DN should be placed in the `users` attribute of the `groups/group` object identified by the given UUID of the `uuid` attribute.

The listener observes both deletions and modifications.
If a user is removed from a group and a corresponding recyclebin object exists, that object is extended with a reference to the group.
If the group was deleted before the user, the listener's local cache detects this and still adds the appropriate reference to the user's recyclebin entry.

**TODO:** verify this behavior.

# Configuring RecycleBin policies

A `policies/recyclebin` object can be created like any other UDM policy to control recyclebin behavior within specific LDAP subtrees.

Policy settings include:

* Enable/disable flag
* Supported UDM modules
* Retention time (in days)

Policies inherit values from parent policy objects along the LDAP tree.

# Restoring objects from the RecycleBin

Restoration is only supported on the DC Primary because it requires `manage` ACL privileges to recreate entries with their original `entryUUID`.
This permission is only available to `cn=admin` (or members of the Domain Admins group?).

Handling references during restore is delicate.
Consider a user and a group that were both deleted:

* If the **user** is restored first, the original group may not yet exist, preventing membership restoration.
* If the **group** is restored first, it may contain an invalid reference to a non-existent user. Ideally, this is not removed by the `refint` overlay, and the proof-unique-member script must not run.

Two possible strategies exist:

1. **Strict:** Deny user restoration if their groups have not been restored yet (but this may complicate nested groups).
2. **Lazy:** Restore the user but skip group memberships; they are reattached automatically when the group is later restored.

Currently, strategy **2** is implemented.

# Comparison with Active Directory RecycleBin

Active Directory provides several mechanisms to achieve recycle-bin functionality:

* [Restore deleted accounts and groups in AD (Microsoft Docs)](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/retore-deleted-accounts-and-groups-in-ad)
* [Active Directory RecycleBin in Windows Server 2008 R2](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-R2-and-2008/dd392261%28v=ws.10%29)

The main Active Directory RecycleBin (ADRB) method uses attributes like:

* `isDeleted` - marks objects as restorable
* `isRecycled` - marks permanently removed objects
* `msDS-deletedObjectLifetime` - defines how long deleted objects are retained (defaults to `tombstoneLifetime`, typically 180 days)

Deleted objects are moved to `OU=Deleted Objects`, and their former parent is recorded in `lastKnownParent`.

Alternative "authoritative restore" methods exist as well, such as restoring from `.ldf` backups, but ADRB remains the primary mechanism.
AD removes group memberships but retains the `memberOf` attribute on deleted user objects.
