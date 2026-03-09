# univention-server

Server role metapackages for UCS. Each role pulls in the appropriate set of services and configuration.

## Binary Packages

- `univention-server-master` -- Primary Directory Node
- `univention-server-backup` -- Backup Directory Node
- `univention-server-slave` -- Replica Directory Node
- `univention-server-member` -- Managed Node
- `univention-role-server-common` -- common files for all server roles
- `univention-container-role-server-common` -- common files for containerized roles
- `univention-role-common` -- common files for all system roles
- `univention-container-role-common` -- common files for containerized system roles

## Key Directories

- `conffiles/` -- UCR templates
- `etc/` -- default configuration
- `server_password_change.d/` -- password rotation scripts
- `univention-directory-policy/` -- directory policy scripts
- `usr/` -- helper scripts

## Key Files

- `server_password_change` -- server password change orchestration
- `univention-ldap-server-available` -- LDAP availability check
