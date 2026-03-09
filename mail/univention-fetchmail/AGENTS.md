# univention-fetchmail

UDM integration for remote mail retrieval via fetchmail. Provides LDAP schema extensions and UDM hooks/syntax for managing fetchmail settings per user.

## Binary Packages

- `univention-fetchmail` -- UDM extensions, listener module, and fetchmailrc generator.
- `univention-fetchmail-schema` -- LDAP schema for fetchmail attributes.

## Directory Structure

- `conffiles/` -- UCR templates for fetchmail configuration.
- `share/hooks.d/`, `share/syntax.d/` -- UDM hook and syntax extensions.
- `scripts/migrate-fetchmail.py` -- Migration script.
- `fetchmailrc.py` -- Listener module generating `/etc/fetchmailrc`.
- `univention-fetchmail.schema` -- LDAP schema file.
- `92univention-fetchmail.inst` / `92univention-fetchmail-schema.inst` -- Join scripts.
- `debian/` -- Debian packaging.
