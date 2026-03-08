# base/

Base system packages for UCS. Contains Debian source packages for core OS-level functionality: configuration registry, system setup, authentication (PAM/Kerberos), SSL certificates, boot configuration, firewall, updater, and shared Python/C libraries.

## Subdirectories

| Directory | Description |
|---|---|
| [pam-runasroot](pam-runasroot/AGENTS.md) | PAM module to execute scripts during authentication |
| [univention-archive-key](univention-archive-key/AGENTS.md) | Archive signing key for UCS repositories |
| [univention-base-files](univention-base-files/AGENTS.md) | Metapackage for default UCS installation |
| [univention-bootsplash](univention-bootsplash/AGENTS.md) | Graphical boot screen configuration |
| [univention-config-registry](univention-config-registry/AGENTS.md) | Univention Config Registry (UCR) Python library |
| [univention-debmirror](univention-debmirror/AGENTS.md) | Local repository configuration |
| [univention-debug](univention-debug/AGENTS.md) | Debugging and logging library (C) |
| [univention-debug-python](univention-debug-python/AGENTS.md) | Debugging and logging library (Python 3 interface) |
| [univention-dvd](univention-dvd/AGENTS.md) | DVD build settings |
| [univention-errata-level](univention-errata-level/AGENTS.md) | Errata level handling |
| [univention-firewall](univention-firewall/AGENTS.md) | Firewall integration (iptables + UCR) |
| [univention-group-membership-cache](univention-group-membership-cache/AGENTS.md) | Group membership cache (includes nested groups) |
| [univention-grub](univention-grub/AGENTS.md) | Grub2 boot loader configuration |
| [univention-heimdal](univention-heimdal/AGENTS.md) | Kerberos KDC with LDAP backend |
| [univention-home-mounter](univention-home-mounter/AGENTS.md) | Mount home directories via NFS |
| [univention-initrd](univention-initrd/AGENTS.md) | Initial ramdisk scripts |
| [univention-ipcalc](univention-ipcalc/AGENTS.md) | IP calculation tool |
| [univention-l10n-fr](univention-l10n-fr/AGENTS.md) | French translations |
| [univention-lib](univention-lib/AGENTS.md) | Common Python 3 and shell scripting functions |
| [univention-licence](univention-licence/AGENTS.md) | License validation library (C) |
| [univention-licence-python](univention-licence-python/AGENTS.md) | License validation library (Python 3) |
| [univention-maintenance](univention-maintenance/AGENTS.md) | Maintenance and monitoring tools |
| [univention-maintenance-mode](univention-maintenance-mode/AGENTS.md) | Minimal web server for update maintenance mode |
| [univention-network-manager](univention-network-manager/AGENTS.md) | Transitional package |
| [univention-newsid](univention-newsid/AGENTS.md) | Generate new Samba SID |
| [univention-pam](univention-pam/AGENTS.md) | PAM and NSS configuration (LDAP, Kerberos) |
| [univention-policy](univention-policy/AGENTS.md) | Group policy library (reads from LDAP) |
| [univention-printclient](univention-printclient/AGENTS.md) | Printing client configuration |
| [univention-python](univention-python/AGENTS.md) | Common Python 3 modules for UCS |
| [univention-python-heimdal](univention-python-heimdal/AGENTS.md) | Python 3 bindings for Heimdal Kerberos |
| [univention-quota](univention-quota/AGENTS.md) | User quota management |
| [univention-server](univention-server/AGENTS.md) | Primary Directory Node installation |
| [univention-skel](univention-skel/AGENTS.md) | Transitional package |
| [univention-ssh](univention-ssh/AGENTS.md) | SSH scripts |
| [univention-ssl](univention-ssl/AGENTS.md) | SSL/TLS CA and certificate management |
| [univention-sudo](univention-sudo/AGENTS.md) | Sudo rules |
| [univention-system-activation](univention-system-activation/AGENTS.md) | System activation for virtual appliances |
| [univention-system-setup](univention-system-setup/AGENTS.md) | System setup tools (name, domain, network) |
| [univention-updater](univention-updater/AGENTS.md) | System upgrading tool |
