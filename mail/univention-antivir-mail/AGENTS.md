# univention-antivir-mail

UCS anti-virus mail scanning configuration. Integrates amavisd-new with ClamAV (and optional alternatives) for scanning incoming/outgoing mail. Depends on `univention-spamassassin`.

## Binary Packages

- `univention-antivir-mail`

## Directory Structure

- `conffiles/` -- UCR templates for amavisd-new and ClamAV configuration.
- `daily.cvd`, `main.cvd` -- ClamAV virus database seed files.
- `debian/` -- Debian packaging, UCR variable definitions.
