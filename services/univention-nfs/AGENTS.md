# univention-nfs

Configures the NFS kernel server for UCS. Shares are managed through the UDM share infrastructure and applied via directory listener modules.

## Binary Packages

- `univention-nfs-server` -- NFS server configuration and listener modules

## Directory Structure

- `conffiles/` -- UCR templates for NFS configuration
- `nfs-homes.py` -- directory listener module for home share exports
- `nfs-shares.py` -- directory listener module for general NFS shares
