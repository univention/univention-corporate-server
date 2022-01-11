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
### ucs-master|ucs-backup|ucs-slave|ucs-member
- **Description:** master, backup, slave and member, all DHCP, domain: autotest.local, master is joined, all other systems provisioned (but not joined)
- **Example:** [scenarios/base/ucs-master-backup.cfg](../base/ucs-master-backup.cfg)
- **Base template:** generic-unsafe
### ucs-joined-master|ucs-joined-backup|ucs-joined-slave|ucs-joined-member
- **Description:**  master, backup, slave and member, all DHCP, domain: autotest.local, all systems joined
- **Example:** [scenarios/base/ucs-master-backup-joined.cfg](../base/ucs-master-backup-joined.cfg)
- **Base template:** generic-unsafe
### ucs-school-singleserver-joined TODO
- **Description:** TODO
- **Example:** TODO
- **Base template:** TODO
### ucs-samba-env1-primary|ucs-samba-env1-replica
- **Description:** Primary and replica, both samba DS's (primary is S4 connector), all DHCP, domain: samba.test
- **Example:** [scenarios/base/ucs-samba-env1-primary-replica.cfg](../base/ucs-samba-env1-primary-replica.cfg)
- **Base template:** generic-unsafe
### primary-with-200000-users-kvm-template
- **Description:** Primary with 200000 user objects and 200 groups, DHCP, FQDN: primary.ucs.test
- **Example:** [scenarios/base/ucs-primary-with-200000-users.cfg](../base/ucs-primary-with-200000-users.cfg)
- **Base template:** generic-unsafe
  
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
 . utils.sh && create_version_file_tmp_ucsver "[ENV:TESTING]"
 GET /tmp/ucs.ver ucs.ver
 . base_appliance.sh && appliance_poweroff
 SSH_DISCONNECT
 SERVER virsh event --domain "[replica_KVM_NAME]" --event lifecycle --timeout 120
 SOURCE ucs.ver
 SERVER ucs-kt-put -C single -O Others -c "[replica_KVM_NAME]" "[ucsver]_ucs-samba-replica_amd64" --remove-old-templates='[ENV:TARGET_VERSION]+e*_ucs-samba-replica_amd64.tar.gz' --keep-last-templates=1
```
A naming convention is that the template name should start with the UCS version (including errata level, e.g. 5.0-0+e152). This is the first part in the example above.

_replica_KVM_NAME_ is the name of the instance on the KVM server, _replica_ is the name of the section (hostname) in the scenario file and has to be replaced.

At the end _ucs-kt-put_ is used to create the actual template, _-C single_ and _-O Others_ is the section for the template, _-c_ for compression the template, _[replica_KVM_NAME]_ is the name of the instance and _[ucsver]_ucs-samba-replica_amd64_ the name of the template. To not fill up disk space _ucs-kt-put_ has a built in mechanism to remove old templates. With _--remove-old-templates_  a pattern for removing template files can be given and with _--keep-last-templates_ how many files should be kept (before creating the new template). In the example above only two versions of the template _5.0-0+e*_ucs-samba-replica_amd64.tar.gz_ are kept.

In this example we create a template with the name _5.0-0+e152_ucs-samba-replica_amd64.tar.gz_.

See ucs/test/scenarios/kvm-templates for more examples.

### New Jenkins job for creating the templates

Add a new job to the seed file for the UCS branch jobs (jenkins/seed-jobs/create_ucs_branch_jobs_5.0.groovy) based on the current jobs (CreateJoinedUnsafeKtGetTemplate).

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
