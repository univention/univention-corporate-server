# univention-samba

Configures a Samba member server providing file sharing, print services, and authentication for Windows clients (NT-style domain, no AD DC).

## Binary Packages

- `univention-samba` -- Samba member server configuration, listener modules
- `univention-samba-local-config` -- UCR-based local share configuration

## Directory Structure

- `conffiles/` -- UCR templates for smb.conf and related files
- `python/` -- Python helper modules
- `scripts/` -- helper scripts
- `samba-shares.py`, `samba-privileges.py` -- directory listener modules
- `server_password_change.d/` -- machine password rotation hooks
- `examples/` -- example configuration files
