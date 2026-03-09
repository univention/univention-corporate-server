# univention-debug

C debugging and logging library used throughout UCS. Provides structured logging with configurable log levels.

## Binary Packages

- `libunivention-debug1` -- shared library
- `libunivention-debug-dev` -- development headers
- `univention-debug-tools` -- `univention-viewlog` tool to filter/view log files

## Key Directories

- `lib/` -- C library source (autotools)
- `include/` -- C header files
- `tools/` -- univention-viewlog
- `tests/` -- test suite

## Notes

- Built with autotools (`configure.in`, `Makefile.am`)
