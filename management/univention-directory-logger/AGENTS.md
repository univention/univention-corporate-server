# univention-directory-logger

Directory Listener module that logs LDAP changes as protocol records. Each record includes a timestamp, modification type, initiator DN, changed attributes, and a chained hash for audit integrity.

## Binary packages

- `univention-directory-logger`

## Directory structure

- `directory_logger.py` -- Listener module implementation
- `conffiles/` -- UCR templates
- `debian/` -- Debian packaging
