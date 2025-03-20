# Delegated administration

TODO introduction

# Features

* UMC's UDM back-end checks authorization before accessing the LDAP database
* Roles can be defined, capabilities (a list of permissions with a condition,
  currently the position of the target object) for roles can be defined
* In a permission you can define what role can to what UDM objects
* The feature is available for all UMC UDM modules (but only to those)
* Default role for `domainadmins` and `ouadmins`

# Not implemented

* UMC has its own authorization for UMC endpoint and UMC modules in the portal.
  This is not yet moved to the new authorization model and has to be configured
  separately
* The currently implementation is object based, not attributes based
  - so once you can read one attribute for an object, you can read the whole object
  - once you can write one attribute you can write all attributes
  (but the concept allows this in the future, just needs to be implemented)

# Know issues

* Only available on primary and backup nodes
* Roles names and the format of the configuration of role, capabilities and
  permissions can and will change in the future

# Setup of test environment with ouadmin

The preview will be released as a normal errata update. The feature can be activated
for testing but is NOT production ready.

## Preparation

* Add the role `umc:udm:domainadmin` as `guardianMemberRoles` to the group `Domain Admins` - this is a
  default role to allow access to the LDAP database for "Administrators"
* Install the latest errata updates

## Enable delegated administration

* Enable delegated administration and restart UMC
  ```
  ucr set umc/udm/delegation=true
  service univention-management-console-server restart
  ```
* Enable UMC UDM modules for all users, TODO

## Preparation for testing the ouadmin default role
- ...

# Roles, role contexts  and permissions

Roles, capabilities and permissions define what an account can do with UMC UDM.

Roles are stored on user accounts as `guardianRoles` or groups as `guardianMemberRoles`.
User accounts inherit roles from the groups that they are member of (not
nested group!).

Roles have a prefix, currently `umc:udm`, and a name, which is just a string.
There are two default roles:
- `umc:udm:domainadmin`
  - can do everything
- `umc:udm:ouadmin`
  - can do everything on its context (see next chapter)
  - can read global groups

## Role context

Roles can have an optional context. This context is an LDAP DN (without the
LDAP base) and defines the position in the LDAP tree where the permissions for
this role applies.

And example would be `ouadmins`. We have one definition for
what this role can do, but we may need to differentiate between different
`ouadmins` for different organizational units.

This can be achieved by setting a context:
```
user1 -> role -> umc:udm:ouadmin&um:udm:ou=bremen
user2 -> role -> umc:udm:ouadmin&um:udm:ou=berlin
```
- `umc:udm:` is just a prefix,
- `ouadmin` is the role
- `&` is the separator
- `ou=bremen` is a position in the LDAP tree (without the LDAP base)

So `user1` and `user2` have the same permissions - derived from the `ouadmin`
role - but for different positions in the LDAP tree - derived from the
context.

## Definition of roles capabilities and permissions

Currently a simple python data structure defines the available roles and permissions

```
{
    ROLE_NAME: [
        { # this is a capability
            "condition": {
                "position": *|LDAP_DN|$CONTEXT
            }
            "permission": {
                UDM_MODULE|*: {
                    "attributes": {
                        ATTRIBUTE|*: read|write
                    }
                    "create": True|False,
                    "delete": True|False,
                 }
                )
            )
            "permission": { ...
        },
        { # another capability
        ...
        }
   ],
   ROLE_NAME: [ ...
}
```
- `ROLE_NAME` - can be any string
- `LDAP_DN` - can be any position in the LDAP tree without the LDAP base
- `$CONTEXT` - is a keyword, that is replaced by the context of a role
- `UDM_MODULE` - can be any UDM module name (users/user)
- `ATTRIBUTE` - is the name of a UDM module attribute
- `True,False` - enable or disable the action
- `*` - wildcard, stand for everything

A concrete example for the role `domainadmin` is:
```
    "domainadmin": [
        {
            "condition": {
                "position": "*",
            },
            "permissions": {
                "*": {
                    "attributes": {
                        "*": "write",
                    },
                    "create": True,
                    "delete": True,
                },
            },
        },
    ],
```
This gives accounts with the role `umc:udm:domainadmin` the right to  read,
modify, create and delete all UDM objects in every position in the LDAP tree.

## Priorities within permission

## Position condition

Every capability is bound to a position. In this position a LDAP DN, the
keyword `$CONTEXT` and a wildcard `*` can be used. These different kind of
position definitions have priorities, from lower to higher priority
- `*`
- `$CONTEXT`
- `LDAP DN`
The match of a capability position with the target object position by a real
LDAP DN has the highest priority (and `*` the lowest).

## UDM modules in permissions

In permissions you can define an UDM module names or a wildcard `*`.
If there is a permission for the UDM module of the target object
it will be used, otherwise the `*` permission (if existing).

## Everything else

What comes first wins.
