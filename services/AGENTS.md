# services/

Infrastructure services for UCS. Each subdirectory is a Debian source package that integrates a third-party service (DNS, DHCP, LDAP connectors (AD and Samba4), Samba, RADIUS, Apache, NFS, databases, printing etc.) into the UCS platform via UCR templates, join scripts, and listener modules.

## Packages

- [univention-ad-connector/AGENTS.md](univention-ad-connector/AGENTS.md) -- Synchronisation between UCS LDAP and Microsoft Active Directory.
- [univention-admin-diary/AGENTS.md](univention-admin-diary/AGENTS.md) -- Admin activity logging with database backend and UMC frontend.
- [univention-apache/AGENTS.md](univention-apache/AGENTS.md) -- Apache2 web server configuration and virtual host management.
- [univention-bind/AGENTS.md](univention-bind/AGENTS.md) -- BIND9 DNS server with LDAP/Samba4 zone backend.
- [univention-dhcp/AGENTS.md](univention-dhcp/AGENTS.md) -- ISC DHCP server with LDAP-based configuration.
- [univention-keycloak/AGENTS.md](univention-keycloak/AGENTS.md) -- Keycloak identity provider client integration.
- [univention-ldb-modules/AGENTS.md](univention-ldb-modules/AGENTS.md) -- Custom LDB modules for Samba4 AD integration.
- [univention-mariadb/AGENTS.md](univention-mariadb/AGENTS.md) -- MariaDB server configuration.
- [univention-nfs/AGENTS.md](univention-nfs/AGENTS.md) -- NFS server with LDAP-managed shares.
- [univention-pkgdb/AGENTS.md](univention-pkgdb/AGENTS.md) -- Software package monitoring database.
- [univention-postgresql/AGENTS.md](univention-postgresql/AGENTS.md) -- PostgreSQL server configuration.
- [univention-printserver/AGENTS.md](univention-printserver/AGENTS.md) -- CUPS print server with UDM-managed printers.
- [univention-radius/AGENTS.md](univention-radius/AGENTS.md) -- FreeRADIUS 802.1X authentication integration.
- [univention-s4-connector/AGENTS.md](univention-s4-connector/AGENTS.md) -- Synchronisation between UCS LDAP and local Samba4 LDB directory.
- [univention-samba/AGENTS.md](univention-samba/AGENTS.md) -- Samba member server (file/print/auth for Windows clients).
- [univention-samba4/AGENTS.md](univention-samba4/AGENTS.md) -- Samba4 Active Directory Domain Controller integration.
- [univention-sasl/AGENTS.md](univention-sasl/AGENTS.md) -- SASL2 authentication configuration.
- [univention-squid/AGENTS.md](univention-squid/AGENTS.md) -- Squid web proxy integration.
- [univention-squid-kerberos/AGENTS.md](univention-squid-kerberos/AGENTS.md) -- Kerberos (negotiate) authentication for Squid proxy.
- [univention-tftp/AGENTS.md](univention-tftp/AGENTS.md) -- TFTP server for PXE network boot.
