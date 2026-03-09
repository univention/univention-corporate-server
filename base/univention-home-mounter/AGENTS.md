# univention-home-mounter

Mounts users' home directories from remote NFS servers at login. Requires home directory locations in LDAP user objects.

## Binary Packages

- `univention-home-mounter`

## Key Files

- `conffiles/` -- UCR templates
- `univention-mount-homedir` -- mount script (called at login)
- `univention-umount-homedirs` -- unmount script
