# crudesaml -- SAML Assertion SASL/PAM Plugins

C library that verifies SAML authentication assertions (signature and validity dates) and grants access based on a configurable attribute. Built from an upstream tarball with Univention patches applied via quilt.

## Binary Packages

- **pam-saml** -- PAM module for SAML assertion authentication.
- **cy2-saml** -- Cyrus SASL plugin for SAML assertion authentication.

## Key Structure

- `crudesaml-1.9.tar.gz` -- Upstream source tarball.
- `patches/` -- Quilt patch series applied on top of upstream.
- `debian/` -- Debian packaging.

## Notes

Replay protection relies solely on assertion validity date checks; assertions must be kept secret (analogous to authentication cookies).
