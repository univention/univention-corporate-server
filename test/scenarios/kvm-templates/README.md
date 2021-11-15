# ucs-kt-get templates

This directory holds files for creating ucs-kt-get (KVM) templates. With these
templates you can easily set up UCS domains without
provisioning/configuration.

## Current templates

- generic-unsafe - based on current DVD
  - base template for standard test, basically a UCS appliance, not provisioned/joined
- ucs-master|ucs-backup|ucs-slave|ucs-member - based on generic-unsafe
  - master, backup, slave and member, all DHCP, domain: autotest.local, master is joined, all other systems provisioned (but not joined)
- ucs-joined-master|ucs-joined-backup|ucs-joined-slave|ucs-joined-member
  - master, backup, slave and member, all DHCP, domain: autotest.local, all systems joined
- ucs-school-singleserver-joined TODO - based on generic-unsafe
- ucs-samba-primary|ucs-samba-replica - based on generic-unsafe
  - primary and replica, both samba DS's (primary is S4 connector), all DHCP, domain: samba.test

## Usage

### Interactive

- TODO ucs-kt-get -O Others ucs-joined-backup

### With scenario file

Create a scenario file for ucs-kvm-create and set **kvm_operating_system: Others** and **kvm_template: TEMPLATE_NAME**

```
[Global]

# These settings can be overwritten by the instance
logfile: autotest-ucs-joined-templates.log

kvm_server: [ENV:KVM_BUILD_SERVER]
kvm_user: [ENV:KVM_USER]
kvm_dhcp: 1
kvm_interface: eth0
kvm_extra_label: ucs-joined-templates
kvm_template: [ENV:KVM_TEMPLATE]
kvm_ucsversion: [ENV:KVM_UCSVERSION]
kvm_architecture: amd64

recover: 2

[master]
kvm_template: ucs-joined-master
kvm_operating_system: Others
command1:
 . utils.sh && basic_setup
 . utils.sh && basic_setup_ucs_joined "[ENV:master_IP]"
 . utils.sh && import_license
 . utils.sh && add_tech_key_authorized_keys
command2:
 . utils.sh && prepare_results
 LOCAL utils/utils-local.sh fetch-results "[ENV:master_IP]" master
files:
 ~/ec2/license/license.secret /etc/

[backup]
kvm_template: ucs-joined-backup
kvm_operating_system: Others
command1:
 . utils.sh && basic_setup
 . utils.sh && basic_setup_ucs_joined "[ENV:master_IP]"
 . utils.sh && add_tech_key_authorized_keys
command3:
 . utils.sh && prepare_results
 LOCAL utils/utils-local.sh fetch-results "[ENV:backup_IP]" backup
```

Start the scenario
```
cd git/ucs/test
DOCKER=true ./utils/start-test.sh /tmp/example.cfg
```

## Add new templates

Templates are currently created via an ucs-kvm-create scenario file and a Jenkins job to start the scenario (to create the template).

### New scenario file

Add a new file to **ucs/test/scenarios/kvm-templates**. In this scenario you can add multiple systems, join systems, do whatever configurtion you need (install software, create users, ...). oA requirement is DHCP for all systems.

To create the template add the following steps for every system in the scenario file:
```
if [ "x[ENV:TESTING]" = "xtrue" ];  then echo "ucsver=@%@version/version@%@-@%@version/patchlevel@%@+$(date +%Y-%m-%d)"          | ucr filter>/tmp/ucs.ver
; fi
 if [ "x[ENV:TESTING]" = "xfalse" ]; then echo 'ucsver=@%@version/version@%@-@%@version/patchlevel@%@+e@%@version/erratalevel@%@' | ucr filter>/tmp/ucs.ver
; fi
 GET /tmp/ucs.ver ucs.ver
 # stop the instance
 . base_appliance.sh && appliance_poweroff
 SSH_DISCONNECT
 SERVER virsh event --domain "[replica_KVM_NAME]" --event lifecycle --timeout 120
 # create template
 SOURCE ucs.ver
 SERVER ucs-kt-put -C single -O Others -c "[replica_KVM_NAME]" "[ucsver]_ucs-samba-replica_amd64"
```
A naming convention is that the template name should start with the UCS version (including errata level, e.g. 5.0-0+e152). This is the first part in the example above.

_replica_KVM_NAME_ is the name of the instance on the KVM server, _replica_ is the name of the section (hostname) in the scenario file and has to be replaced.

At the end _ucs-kt-put_ is used to create the actual template, _-C single_ and _-O Others_ is the section for the template, _-c_ for compression the template, _[replica_KVM_NAME]_ is the name of the instance and _[ucsver]_ucs-samba-replica_amd64_ the name of the template.

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
