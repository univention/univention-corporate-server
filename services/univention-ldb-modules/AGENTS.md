# univention-ldb-modules

UCS-specific LDB modules for Samba4 Active Directory integration. Built as native C shared libraries using the waf build system.

## Binary Packages

- `libunivention-ldb-modules` -- compiled LDB module shared libraries

## Directory Structure

- `modules/` -- C source for LDB modules
- `tests/` -- module tests
- `third_party/` -- vendored dependencies
- `buildtools/` -- waf build tools
- `wscript` -- waf build script
- `Makefile` -- top-level build entry point
