# base/ -- Core System Packages

Core system packages for UCS: config registry, PAM, SSL/TLS, firewall, Kerberos, updater, system setup, and foundational libraries. Every subdirectory is a Debian source package (contains `debian/`).

## Subdirectories

| Directory | Description |
|-----------|-------------|
| [pam-runasroot](pam-runasroot/AGENTS.md) | PAM module to execute scripts during authentication |
| [univention-archive-key](univention-archive-key/AGENTS.md) | APT archive signing keys for UCS repositories |
| [univention-base-files](univention-base-files/AGENTS.md) | Base configuration files and metapackage for default UCS installations |
| [univention-bootsplash](univention-bootsplash/AGENTS.md) | Graphical boot screen (Plymouth) and welcome screen |
| [univention-config-registry](univention-config-registry/AGENTS.md) | Univention Config Registry (UCR) -- the central configuration manager |
| [univention-debmirror](univention-debmirror/AGENTS.md) | Local APT repository mirror configuration |
| [univention-debug](univention-debug/AGENTS.md) | C debugging/logging library |
| [univention-debug-python](univention-debug-python/AGENTS.md) | Python bindings for the debugging/logging library |
| [univention-dvd](univention-dvd/AGENTS.md) | DVD/ISO build settings and trigger files |
| [univention-errata-level](univention-errata-level/AGENTS.md) | Errata level tracking for patch management |
| [univention-firewall](univention-firewall/AGENTS.md) | iptables firewall integration with UCR |
| [univention-group-membership-cache](univention-group-membership-cache/AGENTS.md) | Local cache for user/group membership (avoids LDAP queries) |
| [univention-grub](univention-grub/AGENTS.md) | GRUB2 boot loader configuration |
| [univention-heimdal](univention-heimdal/AGENTS.md) | Kerberos (Heimdal) KDC, member, and common packages |
| [univention-home-mounter](univention-home-mounter/AGENTS.md) | NFS-based remote home directory mounting at login |
| [univention-initrd](univention-initrd/AGENTS.md) | Initial ramdisk (initramfs) scripts |
| [univention-ipcalc](univention-ipcalc/AGENTS.md) | IP address/network calculation tool |
| [univention-l10n-fr](univention-l10n-fr/AGENTS.md) | French language translations for UCS |
| [univention-lib](univention-lib/AGENTS.md) | Common Python and shell scripting libraries |
| [univention-licence](univention-licence/AGENTS.md) | License validation C library and import tool |
| [univention-licence-python](univention-licence-python/AGENTS.md) | Python bindings for the license validation library |
| [univention-maintenance](univention-maintenance/AGENTS.md) | System monitoring/statistics (filesystem, load) |
| [univention-maintenance-mode](univention-maintenance-mode/AGENTS.md) | Minimal web server shown during release updates |
| [univention-network-manager](univention-network-manager/AGENTS.md) | Network configuration tools (ifplugd, common networking) |
| [univention-newsid](univention-newsid/AGENTS.md) | Tool to generate a new Samba SID |
| [univention-pam](univention-pam/AGENTS.md) | PAM/NSS login configuration (LDAP, Kerberos, SSSD) |
| [univention-policy](univention-policy/AGENTS.md) | LDAP group policy library and tools |
| [univention-printclient](univention-printclient/AGENTS.md) | CUPS print client configuration |
| [univention-python](univention-python/AGENTS.md) | Common Python modules (univention base package) |
| [univention-python-heimdal](univention-python-heimdal/AGENTS.md) | Python bindings for the Heimdal Kerberos library |
| [univention-quota](univention-quota/AGENTS.md) | Filesystem quota management and UMC module |
| [univention-server](univention-server/AGENTS.md) | Server role metapackages (Primary, Backup, Replica, Managed Node) |
| [univention-skel](univention-skel/AGENTS.md) | Skeleton files for user home directories (transitional) |
| [univention-ssh](univention-ssh/AGENTS.md) | SSH utility scripts and configuration |
| [univention-ssl](univention-ssl/AGENTS.md) | SSL/TLS CA and certificate management |
| [univention-sudo](univention-sudo/AGENTS.md) | Default sudo rules |
| [univention-system-activation](univention-system-activation/AGENTS.md) | System activation web service for virtual appliances |
| [univention-system-setup](univention-system-setup/AGENTS.md) | System setup wizard (name, domain, network, software) |
| [univention-updater](univention-updater/AGENTS.md) | System upgrade/update tool and UMC module |
