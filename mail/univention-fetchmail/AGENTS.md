# univention-fetchmail

Debian source package: Fetchmail integration for UDM. UDM extensions for integrating remote mail retrieval via fetchmail.

## Key contents
- `fetchmailrc.py` - UCR template for fetchmail configuration
- `univention-fetchmail.schema` - LDAP schema for fetchmail attributes
- `92univention-fetchmail-schema.inst` - Join script for schema registration
- `scripts/migrate-fetchmail.py` - Migration script
- `share/hooks.d/`, `share/syntax.d/` - UDM hooks and syntax definitions
- `conffiles/` - UCR templates and configuration files
