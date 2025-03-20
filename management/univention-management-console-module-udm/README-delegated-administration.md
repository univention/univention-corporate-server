# Delegated administration

TODO introduction

# Features

* UMC's udm backend checks authorization before accessing the LDAP DATABASE
* Roles can be defined, capabilities (a list of permissions with a condition,
  currently the position of the target object) for roles can be defined
* In permissions you can define what UDM objects can be created, modified
  deleted or read.

# Not implemented

* UMC has its own authorization for UMC endpoint and UMC modules in the portal.
  This is not yet moved to the new authorization model and has to be configured
  separatly
* The currently implementation is object based, not attributes based
  - so once you can read one attribute for an object, you can read the whole object
  - once you can write one attribute you can write all attributes
  (but the concept allows this in the future, just needs to be implemented)

# Setup

The preview will be released as a normal errata update. The feature can be activated
for testing but is NOT production ready.

## Preparation

## Enable delegated administration

# Know issues

* Only available on primary and backup nodes
*


Roles and permissions:

We have tow pre-defined role "domainadmin" and "ouadmin".
Currently hard-coded in the code

ROLES = {
    "ROLE_NAME": [
        {
            "target": {
                "position": "POSITION",  # LDAP position, $CONTEXT or *
            }
            "permissions": {
                "UDM_MODULE": {  # udm module, "*"
                    "attributes": {
                        "ATTRIBUTE": "write or read",  # udm attribute or *
                        "..."
                    },
                    "create": True,
                    "delete": True,
                "UDM_MODULE": ...
                }
            }
        },
        {
            "target": { ...
        }
    ]

Setup:
 * add 'umc:udm:domainadmin' as ''guardianMemberRoles' to group ''Domain Admins'
   to give members of 'Domain Admins' the correct rights
 *
