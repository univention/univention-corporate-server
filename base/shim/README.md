# shim
boot loader to chain-load signed boot loaders under Secure Boot

## shim
This package provides a minimalist boot loader which allows verifying signatures of other UEFI binaries against either the Secure Boot DB/DBX or against a built-in signature database.  Its purpose is to allow a small, infrequently-changing binary to be signed by the UEFI CA, while allowing an OS distributor to revision their main bootloader independently of the CA.
