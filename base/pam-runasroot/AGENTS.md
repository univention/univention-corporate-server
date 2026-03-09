# pam-runasroot

PAM module to execute scripts during authentication. Runs scripts during the auth and session setup phases; optionally saves the password for use by those scripts.

## Binary Packages

- `pam-runasroot` (Architecture: any)

## Key Files

- `pam_runasroot.c` -- C source for the PAM module
- `Makefile` -- builds the shared library
