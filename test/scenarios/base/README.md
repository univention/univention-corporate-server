# Example cfg files
Example cfg files for ucs-kt-get/start-test.sh to create various test environments. 

## ucs-samba-env1-primary-replica.cfg
Joined UCS primary and replica, both as samba DC's.
- **Templates:** `[ucsver]_ucs-samba-env1-primary`, `[ucsver]_ucs-samba-env1-replica`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-samba-env1-primary-replica.cfg`

## ucs-ad-connector-w2k12.cfg
UCS base appliance, setup as primary with samba, promote windows server 2012 as AD, setup AD Connector connection.
- **Templates:** `[ucsver]_generic-unsafe`, `2012_de-winrm`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-ad-connector-w2k12.cfg`

## w2k19-ad.cfg
Promote Windows server 2019 as AD with certification authority.
- **Templates:** `2019-server_de-winrm-credssp`, `[ucsver]_generic-unsafe`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/w2k19-ad.cfg`

## master-windows-clients.cfg
Joined UCS primary, setup as samba DC, join two Windows 10 clients.
- **Templates:** `[ucsver]_ucs-joined-master`, `win10_de-winrm-credssp`
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/master-windows-clients.cfg`

## ucs-win2012.cfg
UCS base appliance, setup as primary with, installation of ad connector, promote windows server 2012 as AD.
- **Templates:** ``
- **Usage:** `DOCKER=true ./utils/start-test.sh scenarios/base/ucs-win2012.cfg`

### to test
- ucs-master-backup-joined.cfg
- w2k19-ad-example-org.cfg
- school.cfg
- ucs-master-backup.cfg
