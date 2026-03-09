# Management

UCS management layer: web console (UMC), directory manager (UDM), LDAP server/client/listener/notifier/replication, portal, App Center, domain join, self-service, and related UMC modules. All subdirectories are Debian source packages (contain `debian/` directories).

## Packages

- [univention-admingrp-user-passwordreset/AGENTS.md](univention-admingrp-user-passwordreset/AGENTS.md) -- LDAP ACLs granting password reset ability to a helpdesk user group.
- [univention-appcenter/AGENTS.md](univention-appcenter/AGENTS.md) -- Univention App Center: app installation, Docker integration, and UMC modules.
- [univention-authorization/AGENTS.md](univention-authorization/AGENTS.md) -- Python authorization utilities for UCS.
- [univention-directory-listener/AGENTS.md](univention-directory-listener/AGENTS.md) -- LDAP change notification client that invokes Python handler modules.
- [univention-directory-logger/AGENTS.md](univention-directory-logger/AGENTS.md) -- Listener module that logs LDAP changes with chained hash auditing.
- [univention-directory-manager-modules/AGENTS.md](univention-directory-manager-modules/AGENTS.md) -- UDM core: Python modules, CLI tools, and LDAP object management.
- [univention-directory-manager-rest/AGENTS.md](univention-directory-manager-rest/AGENTS.md) -- REST API service for UCS Directory Manager.
- [univention-directory-notifier/AGENTS.md](univention-directory-notifier/AGENTS.md) -- Propagates LDAP changes to listening clients (Directory Listener).
- [univention-directory-policy/AGENTS.md](univention-directory-policy/AGENTS.md) -- Directory policy handler scripts.
- [univention-directory-replication/AGENTS.md](univention-directory-replication/AGENTS.md) -- Client-initiated LDAP replication via Notifier/Listener.
- [univention-directory-reports/AGENTS.md](univention-directory-reports/AGENTS.md) -- PDF report generation for UDM objects.
- [univention-dojo/AGENTS.md](univention-dojo/AGENTS.md) -- Dojo Toolkit JavaScript source files for UMC frontend.
- [univention-join/AGENTS.md](univention-join/AGENTS.md) -- Domain join scripts for UCS systems.
- [univention-ldap/AGENTS.md](univention-ldap/AGENTS.md) -- OpenLDAP server/client configuration, schemas, and ACLs.
- [univention-ldap-overlay-memberof/AGENTS.md](univention-ldap-overlay-memberof/AGENTS.md) -- Configuration for OpenLDAP memberOf overlay module.
- [univention-management-console/AGENTS.md](univention-management-console/AGENTS.md) -- UMC: web-based management console (server, frontend, web server, Python library).
- [univention-management-console-module-adtakeover/AGENTS.md](univention-management-console-module-adtakeover/AGENTS.md) -- UMC module for Active Directory takeover.
- [univention-management-console-module-diagnostic/AGENTS.md](univention-management-console-module-diagnostic/AGENTS.md) -- UMC module for system diagnostics.
- [univention-management-console-module-ipchange/AGENTS.md](univention-management-console-module-ipchange/AGENTS.md) -- UMC module for IP address registration in LDAP.
- [univention-management-console-module-join/AGENTS.md](univention-management-console-module-join/AGENTS.md) -- UMC module for domain join actions.
- [univention-management-console-module-lib/AGENTS.md](univention-management-console-module-lib/AGENTS.md) -- UMC module with low-level commands for UMC server control.
- [univention-management-console-module-passwordchange/AGENTS.md](univention-management-console-module-passwordchange/AGENTS.md) -- UMC module for password change of the logged-in user.
- [univention-management-console-module-reboot/AGENTS.md](univention-management-console-module-reboot/AGENTS.md) -- UMC module for system reboot.
- [univention-management-console-module-services/AGENTS.md](univention-management-console-module-services/AGENTS.md) -- UMC module for managing system services.
- [univention-management-console-module-top/AGENTS.md](univention-management-console-module-top/AGENTS.md) -- UMC module for process overview.
- [univention-management-console-module-ucr/AGENTS.md](univention-management-console-module-ucr/AGENTS.md) -- UMC module for Univention Config Registry.
- [univention-management-console-module-udm/AGENTS.md](univention-management-console-module-udm/AGENTS.md) -- UMC module for UCS Directory Manager.
- [univention-management-console-module-welcome/AGENTS.md](univention-management-console-module-welcome/AGENTS.md) -- UMC module for first-steps wizard after installation.
- [univention-portal/AGENTS.md](univention-portal/AGENTS.md) -- Central portal web page for a UCS domain.
- [univention-self-service/AGENTS.md](univention-self-service/AGENTS.md) -- User self-service: password reset, invitations, account management.
- [univention-server-overview/AGENTS.md](univention-server-overview/AGENTS.md) -- Web interface showing overview of all servers in a UCS domain.
- [univention-system-info/AGENTS.md](univention-system-info/AGENTS.md) -- System information collection and UMC module.
- [univention-web/AGENTS.md](univention-web/AGENTS.md) -- UMC JavaScript library, CSS/style assets, and web frontend build.
