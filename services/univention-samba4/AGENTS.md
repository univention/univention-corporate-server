# univention-samba4

Integrates Samba4 as an Active Directory Domain Controller into UCS. Includes sysvol replication, idmap configuration, and a custom PAM module.

## Binary Packages

- `univention-samba4` -- Samba4 AD DC configuration, join scripts, helper tools
- `univention-samba4-sysvol-sync` -- sysvol replication via rsync

## Directory Structure

- `conffiles/` -- UCR templates for Samba4/AD configuration
- `scripts/` -- setup and migration scripts
- `sbin/` -- administrative commands
- `lib/` -- shell library functions
- `sysvol-sync-scripts/` -- sysvol synchronisation scripts
- `samba-shares.py`, `samba4-idmap.py` -- directory listener modules
- `pam_univentionsambadomain.c` -- custom PAM module (C)
- `server_password_change.d/` -- machine password rotation hooks
