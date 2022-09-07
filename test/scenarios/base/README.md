# Example cfg files
Example cfg files for [start-test.sh](../../utils/start-test.sh) to create various test environments.

[[_TOC_]]

## [ucs-samba-env1-primary-replica.cfg](ucs-samba-env1-primary-replica.cfg)
Joined UCS primary and replica, both as Samba DC's.
- **Templates:** `[ucsver]_ucs-samba-env1-primary`, `[ucsver]_ucs-samba-env1-replica`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-samba-env1-primary-replica.cfg`

## [ucs-ad-connector-w2k12.cfg](ucs-ad-connector-w2k12.cfg)
UCS base appliance, setup as primary with Samba, promote Windows server 2012 as AD, setup AD Connector connection.
- **Templates:** `[ucsver]_generic-unsafe`, `2012_de-winrm`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-ad-connector-w2k12.cfg`

## [w2k19-ad.cfg](w2k19-ad.cfg)
Promote Windows Server 2019 as AD with certification authority.
- **Templates:** `2019-server_de-winrm-credssp`, `[ucsver]_generic-unsafe`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/w2k19-ad.cfg`

## [master-windows-clients.cfg](master-windows-clients.cfg)
Joined UCS primary, setup as samba DC, join two Windows 10 clients.
- **Templates:** `[ucsver]_ucs-joined-master`, `win10_de-winrm-credssp`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/master-windows-clients.cfg`

## [ucs-win2012.cfg](ucs-win2012.cfg)
UCS base appliance, setup as primary with, installation of AD connector, promote windows server 2012 as AD.
- **Templates:** `???`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-win2012.cfg`

## [ucs-primary-with-200000-users.cfg](ucs-primary-with-200000-users.cfg)
UCS pre-joined primary with 200k user objects.
- **Templates:** `[ucsver]_ucs-primary-with-200000-users`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-primary-with-200000-users.cfg`

## to test
- [ucs-master-backup-joined.cfg](ucs-master-backup-joined.cfg)
- [w2k19-ad-example-org.cfg](w2k19-ad-example-org.cfg)
- [school.cfg](school.cfg)
- [ucs-master-backup.cfg](ucs-master-backup.cfg)
