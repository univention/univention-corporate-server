# Authorization in UDM

Historically authorization in UDM was just realised via LDAP ACL's.
A new approach, embedding authorization in UDM has been created.


```
                                     User
                                       |
                  +--------------------+----------------------+
                  |                    |                      |
         +--------v--------+   +-------v---------+   +--------v---------+
         | UMC             |   | UDM REST        |   | UDM CLI          |
         | udm.ACLs.enable |   | udm.ACLs.enable |   | ACLs not enabled |
         +-----------------+   +-----------------+   +------------------+
              |  |                 |  |                  |
              |  |       admin conn|  |user con          |user conn
              |  |                 |  |                  |
   admin conn |  |user conn        |  |                  |
              |  |                 |  |                  |
            +-v--v-+             +-v--v-+             +--v--+
     +----->| UDM  |      +----->| UDM  |             | UDM |
 authorize  +------+  authorize  +------+             +-----+
     |          |         |          |                   |
+----v-----+    |         |          |                   |
| Guardian |<---|---------+          |                   |
+----------+    |                    |                   |
                |                    |                   |
            admin conn           admin conn          user conn
                |                    |                   |
             +--v-------+        +---v------+        +---v------+
             | OpenLDAP |        | OpenLDAP |        | OpenLDAP |
             +----------+        +----------+        +----------+
```

## How to initialize a service to enable the authorization engine?
```python
import univention.admin.uldap
from univention.admin.authorization import Authorization


def init_the_service()
    base = ucr.get('ldap/base')
    lo_admin = univention.admin.uldap.getAdminConnection()  # cache somehwere
    admin_connection_getter = lambda: lo_admin
    Authorization.enable(admin_connection_getter)

    # get user connection
    lo = univention.admin.uldap.access(binddn='uid=ou1admin,cn=users,dc=ucs,dc=test', bindpw='univention', base=base)
    po = position(lo.base)
    lo = Authorization.inject_ldap_connection(lo)  # extend user connection to have admin powers

    users = modules.get('users/user')
    modules.init(lo, po, users)
    user = users.object(None, lo, po, )
    user.create()
```

This injects the user LDAP connection, so that it provides `lo.authz_connection`, which can be used for certain LDAP operations.
In general the regular user connection is passed to every other function call like when receiving other UDM objects.

Only when doing direct LDAP operations, the admin connection has to be used, for example the `simpleLDAP.create()` method uses it like:

```python
class simpleLDAP:

    def __init__(self):
       self.authz = Authorization()

    def create(self):
        self.authz.is_create_allowed(self)
        self.lo.authz_connection.add(dn, al)
```
This has to be applied for all operations like `get_schema()`, `add()`, `modify()`, `rename()`, `delete()`, `getPolicies()`.
Additionally the methods `get()`, `getAttr()`, `search()` and `searchDn()` must not be used but replaced with equivalents, which filter the results for information the user is allowed to read.
It's very important that it raises the same exception signature like LDAP would do, if no permissions exists, otherwise with that information leak it would be possible to find out whch objects exsits, especially if the user has control over the used LDAP filter, it can be used to obtain arbitrary domain data.

Examples of a filtered search:

1. using a LDAP search, searching for all attributes (assuming the results are only `users/user` objects!)
```python
user_mod = modules.get('users/user')
user = user_mod.object(None, lo, po)

results = lo.search_filtered({'module': user.module}, user_filter, user_base)
```

2. using a LDAP search with DNs as result set (assuming the results are only `users/user` objects!)
```python
user_mod = modules.get('users/user')
user = user_mod.object(None, lo, po)

results = lo.search_dn_filtered({'module': user.module}, user_filter, user_base)
```
