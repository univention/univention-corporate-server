# univention-squid

Integrates the Squid web proxy into UCS with LDAP-based NTLM and basic authentication.

## Binary Packages

- `univention-squid` -- Squid proxy configuration, join scripts, auth helpers

## Directory Structure

- `conffiles/` -- UCR templates for Squid configuration
- `squid_ldap_ntlm_auth` -- NTLM authentication helper
- `basic_ldap_auth_encoding_wrapper` -- basic auth encoding wrapper
- `squid-pw-rotate` -- proxy password rotation script
- `local_bottom.conf`, `local_rules.conf` -- local configuration snippets
