# univention-mail-dovecot

Debian source package: IMAP configuration. The UCS dovecot IMAP mail package.

## Key contents
- `modules/univention/mail/` - `univention.mail` Python module (no setup.py; installed via debian packaging)
- `dovecot.py` - UCR template module for dovecot configuration
- `dovecot-shared-folder.py` - Shared folder management via listener/UCR
- `dovecot-postlogin.py` - Post-login script handling
- `quota-warning.sh` - Mailbox quota warning script
- `conffiles/` - UCR templates and configuration files
- `82univention-mail-dovecot.inst` - Join script
