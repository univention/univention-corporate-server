# univention-directory-notifier

Propagates LDAP changes to listening clients (Directory Listener). Transfers only the DN of altered objects; clients maintain their own caches for attribute-level comparison.

## Binary packages

- `univention-directory-notifier`

## Directory structure

- `src/` -- C source code for the notifier daemon
- `conffiles/` -- UCR templates
- `tests/` -- Test suite
- `doc/` -- Documentation
- `etc/` -- Default configuration files
- `debian/` -- Debian packaging
