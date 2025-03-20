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
* Roles names and and the format of the configuration of role, capabilities and
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

# Roles and permissions

Roles and capabilities, permissions define what an account can do with UMC UDM.

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
This gives accounts with the role `umc:udm:domainadmin` to read, modify, create
and delete all UDM objects on every position in the LDAP tree.
