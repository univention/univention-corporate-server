# univention-directory-replication

Client-initiated LDAP replication based on the Directory Notifier/Listener infrastructure.

## Binary packages

- `univention-directory-replication`

## Directory structure

- `replication.py` -- Listener module implementing LDAP replication
- `oid_skip.py`, `oid_skip.txt` -- OID skip configuration
- `conffiles/` -- UCR templates
- `univention-directory-replication-resync` -- Resync tool
- `debian/` -- Debian packaging
