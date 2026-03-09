# univention-mail-dovecot

UCS Dovecot IMAP/POP3 server configuration. Provides IMAP, POP3, LMTP delivery, and Sieve filtering with LDAP-based authentication and mailbox lookup. Includes listener modules for shared folder management and quota warnings.

## Binary Packages

- `univention-mail-dovecot`

## Directory Structure

- `conffiles/` -- UCR templates for Dovecot configuration (`etc/`, `usr/`, `var/`).
- `modules/univention/mail/` -- Python library for Dovecot mail operations.
- `dovecot.py` -- Directory listener module for mailbox provisioning.
- `dovecot-shared-folder.py` -- Listener module for shared IMAP folders.
- `dovecot-postlogin.py` -- Post-login script helper.
- `quota-warning.sh` -- Quota warning notification script.
- `usr/` -- Additional installed files (lib, share).
- `82univention-mail-dovecot.inst` -- Join script.
- `debian/` -- Debian packaging.
