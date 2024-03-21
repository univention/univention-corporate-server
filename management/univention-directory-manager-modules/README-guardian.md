## UDM for RAM

Three new properties have been added to UDM.

##### guardianRoles
GuardianRoles is the property on which roles are saved that directly apply to
an object. Available in LDAP on every univentionObject.
Available in UDM as a porperty on each computer and user module
This property does not include roles that were inherited by group membership.

##### guardianMemberRoles
Available on groups. This property contains roles that do not directly affect the
object they are saved on, but only affects their members.
This is used to calculate the inherited roles of a user.

##### guardianInheritedRoles
Available on every computer and user module. This contain all roles that were inherited to
the object by group memberships.
This property is not saved in LDAP, but calculated on demand.
It is not retreived by default on opening the object, but only when explicitely requested.
Though it is always shown in the UMC on the Advanced Tab.


All properties including guardianInheritedRoles can be retreived in UDM CLI:

```
udm users/user list --filter "uid=Administrator" --properties="guardianInheritedRoles" --properties='*'
```

All properties including guardianInheritedRoles can be retreived in UDM REST client:

```
from univention.admin.rest.client import UDM
uri = 'http://localhost/univention/udm/'
udm = UDM.http(uri, 'Administrator', 'univention')
module = udm.get('users/user')
obj = module.get("uid=Administrator,cn=users,dc=school,dc=test", properties=['guardianInheritedRoles', '*'])

```

<u>**TODOS for the Guardian Apps:**</u>

- The extended attribute guardianRole can be removed. These properties need to be migrated on upgrade to

- guardianRoles and guardianMemberRoles.
- The UDM REST client fork in the Guardian App needs to be updated to the new version, so that guardianInheritedRoles can be
- requested.
- The new app version needs to depend on the errata which released the new features.

