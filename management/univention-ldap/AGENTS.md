# univention-ldap

OpenLDAP server and client configuration for UCS, including LDAP schemas, ACLs, base LDIF, and management scripts.

## Binary packages

- `univention-ldap-server` -- LDAP server configuration
- `univention-ldap-client` -- LDAP client configuration
- `univention-ldap-config` -- Common LDAP configuration and schemas
- `univention-ldap-config-master` -- Config for Primary/Backup Directory Nodes
- `univention-ldap-acl-master` -- ACLs for Primary/Backup Directory Nodes
- `univention-ldap-acl-slave` -- ACLs for Replica Directory Nodes

## Directory structure

- `schema/` -- LDAP schema files
- `acl/` -- LDAP ACL definitions
- `conffiles/` -- UCR templates
- `listener/` -- Directory Listener modules
- `scripts/` -- Helper scripts
- `base.ldif`, `*.ldif` -- Base LDAP data
- `doc/` -- Documentation
- `debian/` -- Debian packaging
