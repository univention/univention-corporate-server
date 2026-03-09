# crudeoauth -- OAuth Bearer SASL/PAM Plugins

C library that verifies OAuth Bearer JWT access-tokens (signature and expiry) and grants access for configurable issuers and audiences.

## Binary Packages

- **libsasl2-modules-oauthbearer** -- SASL plugin implementing OAUTHBEARER (RFC 7628).
- **libpam-oauthbearer** -- PAM module for OAuth access-token authentication.

## Key Structure

- `src/` -- C sources and autotools build system.
  - `sasl_oauthbearer.c` -- SASL plugin entry point.
  - `pam_oauthbearer.c` -- PAM module entry point.
  - `oauthbearer.c/.h` -- Shared JWT verification logic.
  - `plugin_common.c/.h` -- Shared SASL utilities.
- `debian/` -- Debian packaging.

## Build Dependencies

Uses librhonabwy for JWT/JWK handling, libjansson for JSON, libsasl2, and libpam.
