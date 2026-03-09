# univention-mail-postfix

UCS Postfix mail transport agent configuration. Provides LDAP-based mail routing, SASL authentication, TLS setup, and hosted domain management.

## Binary Packages

- `univention-mail-postfix` -- Core Postfix configuration with LDAP integration.
- `univention-mail-postfix-forward` -- Transitional package (can be safely removed).
- `univention-mail-server` -- Meta-package pulling in Postfix, Dovecot, and SASL.

## Directory Structure

- `conffiles/` -- UCR templates for Postfix configuration (`main.cf`, `master.cf`, LDAP maps, etc.).
- `share/` -- Helper scripts: `aliases.sh`, `listfilter.py`, `postmap-transport.sh`, `create-dh-parameter-files.sh`.
- `hosteddomains.py` -- Listener module for hosted mail domains.
- `usr/lib/` -- Additional library files.
- `dh_512.pem`, `dh_2048.pem` -- Default Diffie-Hellman parameter files.
- `67univention-mail-server.inst` -- Join script.
- `debian/` -- Debian packaging, UCR variable/service definitions.
