# univention-ssl

SSL/TLS certificate authority and certificate management for UCS. Creates a root CA and signs certificates for UCS services.

## Binary Packages

- `univention-ssl`

## Key Files

- `make-certificates.sh` -- CA and certificate creation scripts
- `univention-certificate` -- CLI tool for certificate management
- `univention-certificate-check-validity` -- certificate expiry checker
- `univention-fetch-certificate` -- fetch certificates from remote hosts
- `gencertificate.py` -- LDAP listener module for automatic certificate generation
- `ssl-sync` -- certificate synchronization script
- `conffiles/` -- UCR templates for OpenSSL configuration
- `tests/` -- test suite

## Notes

- Has an LDAP directory listener module (`gencertificate.py`) for automatic cert generation
