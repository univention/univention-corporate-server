# univention-licence

UCS license validation C library and license import tool.

## Binary Packages

- `libunivention-license0` -- shared library
- `libunivention-license-dev` -- development headers
- `univention-license-import` -- CLI tool to import new licenses

## Key Directories

- `lib/` -- C library source (autotools)
- `include/` -- C header files
- `tools/` -- license import tool

## Notes

- Built with autotools (`configure.ac`, `Makefile.am`)
- Links against libldap, libssl, libunivention-config, libunivention-debug, libunivention-policy
