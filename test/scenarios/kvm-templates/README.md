# ucs-kt-get templates

This directory holds files for creating ucs-kt-get (KVM) templates. With these
templates you can easily set up UCS domains without
provisioning/configuration.

_[TOC]_

## Template Life cycle
<details><summary>Click to expand</summary>

1. Create Jenkins job for template
1. Templates are stored in /mnt/omar/vmwares/kvm/single/Others (base template generic-unsafe in /mnt/omar/vmwares/kvm/single/UCS)
1. Create example scenario file for template in [test/scenarios/base](../scenarios/base)
1. Template is started via utils/start-test.sh
1. Internally ucs-kt-get copies the template to /var/lib/libvirt/templates/ on the KVM server
1. For the individual instances cow images are generated from the template
1. Unused template are removed from the server

</details>

## Available templates

### generic-unsafe
- **Description:** base template for standard test, basically a UCS appliance, not provisioned/joined
- **Example:** -
- **Base template:** current DVD
- **Template cfg:** [generic-kvm-template.cfg](./generic-kvm-template.cfg)
### ucs-master|ucs-backup|ucs-slave|ucs-member
- **Description:** master, backup, slave and member, all DHCP, domain: ucs.test, master is joined, all other systems provisioned (but not joined)
- **Example:** [scenarios/base/ucs-master-backup.cfg](../base/ucs-master-backup.cfg)
- **Base template:** generic-unsafe
- **Template cfg:** [role-kvm-templates.cfg](./role-kvm-templates.cfg)
### ucs-joined-master|ucs-joined-backup|ucs-joined-slave|ucs-joined-member
- **Description:**  master, backup, slave and member, all DHCP, domain: ucs.test, all systems joined
- **Example:** [scenarios/base/ucs-master-backup-joined.cfg](../base/ucs-master-backup-joined.cfg)
- **Base template:** generic-unsafe
- **Template cfg:** [joined-kvm-templates.cfg](./joined-kvm-templates.cfg)
### ucs-school-multiserver-primary|ucs-school-multiserver-backup1|ucs-school-multiserver-school1 (replica)
- **Description:** school primary, backup and one school slave (school1), domain: school.test, all joined
- **Example:** [scenarios/base/ucs-school-multiserver-joined-primary-school1.cfg](../base/ucs-school-multiserver-joined-primary-school1.cfg)
- **Base template:** generic-unsafe
- **Template cfg:** [ucs-school-multiserver-joined.cfg](./ucs-school-multiserver-joined.cfg)
### ucs-samba-env1-primary|ucs-samba-env1-replica
- **Description:** Primary and replica, both samba DS's (primary is S4 connector), all DHCP, domain: samba.test
- **Example:** [scenarios/base/ucs-samba-env1-primary-replica.cfg](../base/ucs-samba-env1-primary-replica.cfg)
- **Base template:** generic-unsafe
- **Template cfg:** [samba-primary-replica-kvm-templates.cfg](./samba-primary-replica-kvm-templates.cfg)
### ucs-primary-with-200000-users
- **Description:** Primary with 200000 user objects and 20000 groups (see utils/200.000-users.py for details), DHCP, FQDN: primary.ucs.test
- **Example:** [scenarios/base/ucs-primary-with-200000-users.cfg](../base/ucs-primary-with-200000-users.cfg)
- **Base template:** generic-unsafe
- **Template cfg:** [primary-with-200000-users-kvm-template.cfg](./primary-with-200000-users-kvm-template.cfg)
### ucs-school-performance-env1-primary|ucs-school-performance-env1-backup1
- **Description:** School primary and backup with 250000 school users (see utils/utils-school.sh::create_users_in_template_job for details), domain: school.test
- **Example:** TODO
- **Base template:** generic-unsafe
- **Template cfg:** [ucs-school-performance-env1.cfg](./ucs-school-performance-env1.cfg)

## Usage
The normal use case is to start templates with start-test.sh. Some example cfg files can be found in [test/scenarios/base](../base/README.md)

```
cd git/ucs/test
DOCKER=true ./utils/start-test.sh scenarios/base/ucs-samba-env1-primary-replica.cfg
```

## Add new templates

Templates are currently created via an ucs-kvm-create scenario file and a Jenkins job to start the scenario (to create the template).

### New scenario file

Add a new file to **ucs/test/scenarios/kvm-templates**. In this scenario you can add multiple systems, join systems, do whatever configurtion you need (install software, create users, ...). A requirement is DHCP for all systems.

To create the template add the following steps for every system in the scenario file:
```
recover: 9
…
[section]
…
command8:
 . utils.sh && create_version_file_tmp_ucsver "[ENV:TESTING]"
 GET /tmp/ucs.ver ucs_[SELF].ver
 . base_appliance.sh && appliance_poweroff
 SSH_DISCONNECT
 SERVER id=$(virsh domid SELF_KVM_NAME) && [ -n "${id#-}" ] && virsh event --domain "$id" --event lifecycle --timeout 120 --timestamp || :
 SOURCE ucs_[SELF].ver
 SERVER ucs-kt-put -C single -O Others -c "[SELF_KVM_NAME]" "[ucsver]_ucs-samba-replica_amd64" --remove-old-templates='[ENV:TARGET_VERSION]+e*_ucs-samba-replica_amd64.tar.gz' --keep-last-templates=1
command9:
 LOCAL rm -f ucs_[SELF].ver
```
A naming convention is that the template name should start with the UCS version (including errata level, e.g. 5.0-0+e152). This is the first part in the example above.

_SELF_KVM_NAME_ is the name of the instance on the KVM server, _replica_ is the name of the section (hostname) in the scenario file and has to be replaced.

At the end _ucs-kt-put_ is used to create the actual template, _-C single_ and _-O Others_ is the section for the template, _-c_ for compression the template, _[SELF_KVM_NAME]_ is the name of the instance and _[ucsver]_ucs-samba-replica_amd64_ the name of the template. To not fill up disk space _ucs-kt-put_ has a built in mechanism to remove old templates. With _--remove-old-templates_  a pattern for removing template files can be given and with _--keep-last-templates_ how many files should be kept (before creating the new template). In the example above only two versions of the template _5.0-0+e*_ucs-samba-replica_amd64.tar.gz_ are kept.

In this example we create a template with the name _5.0-0+e152_ucs-samba-replica_amd64.tar.gz_.

See ucs/test/scenarios/kvm-templates for more examples.

### New Jenkins job for creating the templates

Add a new job to the seed file for the UCS branch jobs `jenkins/seed-jobs/create_ucs_branch_jobs_5.0.groovy` based on the current jobs (CreateJoinedUnsafeKtGetTemplate).

Add the new job to the KVM templates view:
```
...
listView("${c.jenkins_folder_name}/KVM Templates") {
    jobs {
        ...
        + name('YourJob')
    }
```

### Create templates

To create the template, go to Jenkins UCS-X.X / UCS-X.X-X / KVM Templates and start your job.

## Windows Templates

Here some hints how to prepare such a windows template

* start/install the windows system on our KVM environment (add virtio iso before installation and use virtio hd and network interface, during the setup you can install the virtio hd driver)
* deactivate the firewall (TODO, add the correct exceptions instead of deactivating) for all network profiles
* add VirtIO drivers
* set DCHP for the network
* activate Administrator account and set password -> univention (clients), Univention.99 (server)
* set network profie to "Private"
  * powershell
  * Get-NetConnectionProfile
  * Set-NetConnectionProfile -Name "NetworkName" -NetworkCategory Private
* activate winrm
  * winrm quickconfig
  * Restart-Service winrm
* apply the ucs-winrm default settings (!! important, otherwise ucs-winrm will not work later)
  ```
  Enable-WSManCredSSP -Role Server -Force
  Enable-WSManCredSSP -Role Client -DelegateComputer * -Force
  Set-Item -Path "wsman:\localhost\service\auth\credSSP" -Value $True -Force
  Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
  New-Item -Path HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation -Name AllowFreshCredentialsWhenNTLMOnly -Force
  New-ItemProperty -Path HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation\AllowFreshCredentialsWhenNTLMOnly -Name 1 -Value * -PropertyType String -Force
  winrm set winrm/config '@{MaxTimeoutms="7200000"}'
  winrm set winrm/config/winrs '@{MaxMemoryPerShellMB="0"}'
  winrm set winrm/config/winrs '@{MaxProcessesPerShell="0"}'
  winrm set winrm/config/winrs '@{MaxShellsPerUser="0"}'
  winrm set winrm/config/service '@{AllowUnencrypted="true"}'
  winrm set winrm/config/service/auth '@{Basic="true"}'
  winrm set winrm/config/client/auth '@{Basic="true"}'
  winrm set winrm/config/client '@{TrustedHosts="*"}'
  Restart-Service winrm
  ```
  * test connection with `python3 ucs-winrm run-ps --cmd ls  --client "10.207.67.241" --user univention --password univention` in `dist/ucs-winrm/src`
* cleanup windows (disk cleanup to save disk space)
* stop instance
* use `ucs-kt-put` on the KVM server to create a template
  ```
  ucs-kt-put -C single -O Windows \
    -c "$INSTANCE_NAME" \
    "win11-pro-winrm-20290218_en-winrm-credssp_amd64"
  ```
