# univention-quota

Filesystem quota management for UCS. Sets default quotas for users at login based on LDAP share policies. Includes a UMC module.

## Binary Packages

- `univention-quota` -- quota management scripts
- `univention-management-console-module-quota` -- UMC web module

## Key Directories

- `conffiles/` -- UCR templates
- `umc/` -- UMC module (Python + JS/XML definitions)
- `files/` -- helper files
- `test/` -- tests

## Key Files

- `quota.py` -- quota management logic
- `35univention-management-console-module-quota.inst` -- join script

## Notes

- Includes a UMC (Univention Management Console) module
