# Tests

## UCS

### [Default](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/)

* [scenarios/check-maintained/check-maintained.cfg](scenarios/check-maintained/check-maintained.cfg)

#### [MultiEnv: AMI<5.0, join, upgrade=5.0, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/AutotestUpgrade/)

1. previous AMI
2. join
3. upgrade

* [scenarios/autotest-070-update-master-no-samba.cfg](scenarios/autotest-070-update-master-no-samba.cfg)
* [scenarios/autotest-070-update-master-part-II-no-samba.cfg](scenarios/autotest-070-update-master-part-II-no-samba.cfg)
* [scenarios/autotest-071-update-master-part-II-s4.cfg](scenarios/autotest-071-update-master-part-II-s4.cfg)
* [scenarios/autotest-071-update-master-s4.cfg](scenarios/autotest-071-update-master-s4.cfg)
* [scenarios/autotest-072-update-backup-no-samba.cfg](scenarios/autotest-072-update-backup-no-samba.cfg)
* [scenarios/autotest-073-update-backup-s4.cfg](scenarios/autotest-073-update-backup-s4.cfg)
* [scenarios/autotest-074-update-slave-no-samba.cfg](scenarios/autotest-074-update-slave-no-samba.cfg)
* [scenarios/autotest-075-update-slave-s4.cfg](scenarios/autotest-075-update-slave-s4.cfg)
* [scenarios/autotest-076-update-member-no-samba.cfg](scenarios/autotest-076-update-member-no-samba.cfg)
* [scenarios/autotest-077-update-member-s4.cfg](scenarios/autotest-077-update-member-s4.cfg)

#### [MultiEnv: AMI=5.0, errata, join, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/AutotestJoin/)
#### [MultiEnv: AMI=5.0, only released errata, join, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/AutotestJoinReleased/)

1. current AMI
2. errata
3. join

* [scenarios/autotest-090-master-no-samba.cfg](scenarios/autotest-090-master-no-samba.cfg)
* [scenarios/autotest-090-master-part-II-no-samba.cfg](scenarios/autotest-090-master-part-II-no-samba.cfg)
* [scenarios/autotest-091-master-part-II-s4.cfg](scenarios/autotest-091-master-part-II-s4.cfg)
* [scenarios/autotest-091-master-s4.cfg](scenarios/autotest-091-master-s4.cfg)
* [scenarios/autotest-092-backup-no-samba.cfg](scenarios/autotest-092-backup-no-samba.cfg)
* [scenarios/autotest-093-backup-s4.cfg](scenarios/autotest-093-backup-s4.cfg)
* [scenarios/autotest-094-slave-no-samba.cfg](scenarios/autotest-094-slave-no-samba.cfg)
* [scenarios/autotest-095-slave-s4.cfg](scenarios/autotest-095-slave-s4.cfg)
* [scenarios/autotest-096-member-no-samba.cfg](scenarios/autotest-096-member-no-samba.cfg)
* [scenarios/autotest-097-member-s4.cfg](scenarios/autotest-097-member-s4.cfg)

#### [Tests - AD Connector (ec2)](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/ADConnectorMultiEnv/)

1. AD connector setups with different windows versions

* [scenarios/ad-connector/autotest-231-adsync-w2k12-german.cfg](scenarios/ad-connector/autotest-231-adsync-w2k12-german.cfg)
* [scenarios/ad-connector/autotest-232-adsync-w2k8r2-english.cfg](scenarios/ad-connector/autotest-232-adsync-w2k8r2-english.cfg)
* [scenarios/ad-connector/autotest-232-adsync-w2k8r2-english-same-domain.cfg](scenarios/ad-connector/autotest-232-adsync-w2k8r2-english-same-domain.cfg)
* [scenarios/ad-connector/autotest-233-adsync-w2k12r2-france.cfg](scenarios/ad-connector/autotest-233-adsync-w2k12r2-france.cfg)
* [scenarios/ad-connector/autotest-234-adsync-w2k16-german.cfg](scenarios/ad-connector/autotest-234-adsync-w2k16-german.cfg)
* [scenarios/ad-connector/autotest-235-adsync-w2k19-english.cfg](scenarios/ad-connector/autotest-235-adsync-w2k19-english.cfg)
* [scenarios/ad-connector/autotest-236-adsync-w2k8r2-german.cfg](scenarios/ad-connector/autotest-236-adsync-w2k8r2-german.cfg)
* [scenarios/ad-connector/autotest-237-adsync-s4connector-w2k19-english.cfg](scenarios/ad-connector/autotest-237-adsync-s4connector-w2k19-english.cfg)

#### [Tests - AD Member Mode (ec2)](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-r/job/ADMemberMultiEnv/)

1. AD member setups for installation/module with different windows versions

* [scenarios/ad-membermode/autotest-221-admember-w2019-english.cfg](scenarios/ad-membermode/autotest-221-admember-w2019-english.cfg)
* [scenarios/ad-membermode/autotest-222-admember-w2k8r2-german.cfg](scenarios/ad-membermode/autotest-222-admember-w2k8r2-german.cfg)
* [scenarios/ad-membermode/autotest-223-admember-w2k12-german-slave.cfg](scenarios/ad-membermode/autotest-223-admember-w2k12-german-slave.cfg)
* [scenarios/ad-membermode/autotest-224-admember-w2k12-german-other-join-user.cfg](scenarios/ad-membermode/autotest-224-admember-w2k12-german-other-join-user.cfg)
* [scenarios/ad-membermode/autotest-225-admember-w2k12r2-france.cfg](scenarios/ad-membermode/autotest-225-admember-w2k12r2-france.cfg)

#### [Tests - App Appliance](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/App%20Appliance%20Tests/)

UCS with pre-installed App, to check if changes in UCS break the appliance setup

* [scenarios/app-appliance-base.cfg](scenarios/app-appliance-base.cfg): Create base image for App Appliance (Stable.ISO)
* [scenarios/app-appliance.cfg](scenarios/app-appliance.cfg): Create App Appliance (Stable.ISO → $mm-99 → +App → `$BS2/mirror/appcenter.test/univention-apps/current/`KVM,VMware,ESX,VirtualBox)
* [scenarios/appliance-testing/app-appliance-errata-test.cfg](scenarios/appliance-testing/app-appliance-errata-test.cfg)
* [scenarios/appliance-testing/app-appliance-only-released.cfg](scenarios/appliance-testing/app-appliance-only-released.cfg)

#### [Tests - DVD Installation](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/Installation%20Tests/)

1. Various UCS installation tests (fail immediately if one setup step fails, only basic tests)

* [scenarios/install-testing/ad-member.cfg](scenarios/install-testing/ad-member.cfg)
* [scenarios/install-testing/base.cfg](scenarios/install-testing/base.cfg)
* [scenarios/install-testing/master-english-static-ip.cfg](scenarios/install-testing/master-english-static-ip.cfg)
* [scenarios/install-testing/master-french-static-ip.cfg](scenarios/install-testing/master-french-static-ip.cfg)
* [scenarios/install-testing/master-german.cfg](scenarios/install-testing/master-german.cfg)
* [scenarios/install-testing/net-installer.cfg](scenarios/install-testing/net-installer.cfg)
* [scenarios/install-testing/samba-env.cfg](scenarios/install-testing/samba-env.cfg)
* [scenarios/install-testing/school.cfg](scenarios/install-testing/school.cfg)
* [scenarios/install-testing/school-dev.cfg](scenarios/install-testing/school-dev.cfg)
* [scenarios/install-testing/school-scope.cfg](scenarios/install-testing/school-scope.cfg)

#### [Tests - S4Connector](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/S4Connector/)

1. Install/Update/OnlyReleasedErrata scenario for S4Connector tests.

* [scenarios/s4-connector/master-only-released-errata-s4connector.cfg](scenarios/s4-connector/master-only-released-errata-s4connector.cfg)
* [scenarios/s4-connector/master-s4connector.cfg](scenarios/s4-connector/master-s4connector.cfg)
* [scenarios/s4-connector/update-master-s4connector.cfg](scenarios/s4-connector/update-master-s4connector.cfg)

### [Tests - UCS update](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/job/Update%20Tests/)

1. Various UCS update tests (fail immediately if one setup step fails, only basic tests)

* [scenarios/update-testing/update-from-1.2-backup2master.cfg](scenarios/update-testing/update-from-1.2-backup2master.cfg): Update from old UCS 1.2 system
* [scenarios/update-testing/update-from-2.4-start-4.4-7.cfg](scenarios/update-testing/update-from-2.4-start-4.4-7.cfg): Update from old UCS 2.4 system
* [scenarios/update-testing/update-from-4.2-4.cfg](scenarios/update-testing/update-from-4.2-4.cfg): Update system with all UCS components

-----

### [Appliances](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/view/Appliances/)

* [scenarios/appliances/ucs-appliance.cfg](scenarios/appliances/ucs-appliance.cfg): Create UCS Appliance (Stable.ISO → $mm-99 → `$BS2/temp/build/appliance/`KVM,VMware,ESX,VirtualBox,HyperV)
* [scenarios/appliances/ec2-appliance.cfg](scenarios/appliances/ec2-appliance.cfg): Create UCS ec2 image (Stable.ISO → `$VIRT/images/`KVM → EC2)

#### [Test UCS Appliance](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/view/Appliances/job/TestUCSAppliance/)

* [scenarios/ucs-appliance-testing/ad-member.cfg](scenarios/ucs-appliance-testing/ad-member.cfg)
* [scenarios/ucs-appliance-testing/master.cfg](scenarios/ucs-appliance-testing/master.cfg)
* [scenarios/ucs-appliance-testing/master-slave.cfg](scenarios/ucs-appliance-testing/master-slave.cfg)

#### [Test EC2 UCS Appliance](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/view/Appliances/job/TestEC2UCSAppliance/)

* [scenarios/ucs-appliance-testing/ad-member-ec2.cfg](scenarios/ucs-appliance-testing/ad-member-ec2.cfg)
* [scenarios/ucs-appliance-testing/master-ec2.cfg](scenarios/ucs-appliance-testing/master-ec2.cfg)
* [scenarios/ucs-appliance-testing/master-slave-ec2.cfg](scenarios/ucs-appliance-testing/master-slave-ec2.cfg)

-----

### [KVM Templates](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/view/KVM%20Templates/)

* [scenarios/kvm-templates/generic-kvm-template.cfg](scenarios/kvm-templates/generic-kvm-template.cfg): Create generic `ucs-kt-get` template
* [scenarios/kvm-templates/joined-kvm-templates.cfg](scenarios/kvm-templates/joined-kvm-templates.cfg): Create `ucs-kt-get` templates for joined UCS roles
* [scenarios/kvm-templates/role-kvm-templates.cfg](scenarios/kvm-templates/role-kvm-templates.cfg): Create `ucs-kt-get` templates for UCS roles
* [scenarios/kvm-templates/w2k19-ad-template.cfg](scenarios/kvm-templates/w2k19-ad-template.cfg): Create `ucs-kt-get` template for provisioned w2k19 ad
* [scenarios/kvm-templates/ucs-school-multiserver-joined.cfg](scenarios/kvm-templates/ucs-school-multiserver-joined.cfg): Create `ucs-kt-get` templates for UCS@School environment
* [scenarios/kvm-templates/ucs-school-performance-env1.cfg](scenarios/kvm-templates/ucs-school-performance-env1.cfg): Create `ucs-kt-get` templates for UCS@School performance environment
* [scenarios/kvm-templates/primary-with-200000-users-kvm-template.cfg](scenarios/kvm-templates/primary-with-200000-users-kvm-template.cfg) Create `ucs-kt-get` templates for UCS performance environment
* [scenarios/kvm-templates/samba-primary-replica-kvm-templates.cfg](scenarios/kvm-templates/samba-primary-replica-kvm-templates.cfg): Create `ucs-kt-get` templates for UCS samba environment

### VM creation

#### Unjoined

* [scenarios/base/master-role-template.cfg](scenarios/base/master-role-template.cfg): Setup Master
* [scenarios/base/ucs-master-backup.cfg](scenarios/base/ucs-master-backup.cfg): Setup Master and Backup
* [scenarios/base/ucs-ad-connector-w2k12.cfg](scenarios/base/ucs-ad-connector-w2k12.cfg): Master and Windows 2012 AD Connector setup
* [scenarios/base/school.cfg](scenarios/base/school.cfg): Master and Slave with UCS@School
* [scenarios/base/ucs-win2012.cfg](scenarios/base/ucs-win2012.cfg): Master and Windows 2012
* [scenarios/base/w2k19-ad.cfg](scenarios/base/w2k19-ad.cfg): Master and Windows 2019 AD with certtificate authority
* [scenarios/base/w2k19-ad-example-org.cfg](scenarios/base/w2k19-ad-example-org.cfg): Windows 2019 AD already provisioned

#### Joined

* [scenarios/base/ucs-samba-env1-primary-replica.cfg](scenarios/base/ucs-samba-env1-primary-replica.cfg): Master and Replica with samba
* [scenarios/base/ucs-ad-connector-w2k19.cfg](scenarios/base/ucs-ad-connector-w2k19.cfg): Master and Windows 2019 AD Connector setup
* [scenarios/base/master-windows-clients.cfg](scenarios/base/master-windows-clients.cfg): Setup Master + 2 Windows 10
* [scenarios/base/ucs-master-backup-joined.cfg](scenarios/base/ucs-master-backup-joined.cfg): Setup Master and Backup
* [scenarios/base/ucs-master-slave-joined.cfg](scenarios/base/ucs-master-slave-joined.cfg): Setup Master and Slave
* [scenarios/base/ucs-primary-with-200000-users.cfg](scenarios/base/ucs-primary-with-200000-users.cfg): Setup Master with 200k users
* [scenarios/base/ucs-school-multiserver-joined-primary-school1.cfg](scenarios/base/ucs-school-multiserver-joined-primary-school1.cfg) UCS@School primary with school replica
* [scenarios/base/ucs-school-performance-env1.cfg](scenarios/base/ucs-school-performance-env1.cfg): UCS@School primary from school performance template

-----

### ??? deprecated ???

* [scenarios/setup-testing/backup-no-samba.cfg](scenarios/setup-testing/backup-no-samba.cfg)
* [scenarios/setup-testing/backup-s4.cfg](scenarios/setup-testing/backup-s4.cfg)
* [scenarios/setup-testing/master-no-samba.cfg](scenarios/setup-testing/master-no-samba.cfg)
* [scenarios/setup-testing/master-s4.cfg](scenarios/setup-testing/master-s4.cfg)
* [scenarios/setup-testing/member-no-samba.cfg](scenarios/setup-testing/member-no-samba.cfg)
* [scenarios/setup-testing/member-s4.cfg](scenarios/setup-testing/member-s4.cfg)
* [scenarios/setup-testing/slave-no-samba.cfg](scenarios/setup-testing/slave-no-samba.cfg)
* [scenarios/setup-testing/slave-s4.cfg](scenarios/setup-testing/slave-s4.cfg)

## Apps

### [App testing](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/Apps/)

#### [App Autotest MultiEnv](ttps://jenkins2022.knut.univention.de/job/UCS-5.0/job/Apps/job/admin-dashboard/job/App%20Autotest%20MultiEnv/)

* [scenarios/app-testing/autotest-100-app-master-no-samba.cfg](scenarios/app-testing/autotest-100-app-master-no-samba.cfg)
* [scenarios/app-testing/autotest-101-app-master-s4.cfg](scenarios/app-testing/autotest-101-app-master-s4.cfg)
* [scenarios/app-testing/autotest-102-app-backup-no-samba.cfg](scenarios/app-testing/autotest-102-app-backup-no-samba.cfg)
* [scenarios/app-testing/autotest-103-app-backup-s4.cfg](scenarios/app-testing/autotest-103-app-backup-s4.cfg)
* [scenarios/app-testing/autotest-104-app-slave-no-samba.cfg](scenarios/app-testing/autotest-104-app-slave-no-samba.cfg)
* [scenarios/app-testing/autotest-105-app-slave-s4.cfg](scenarios/app-testing/autotest-105-app-slave-s4.cfg)
* [scenarios/app-testing/autotest-106-app-member-no-samba.cfg](scenarios/app-testing/autotest-106-app-member-no-samba.cfg)
* [scenarios/app-testing/autotest-107-app-member-s4.cfg](scenarios/app-testing/autotest-107-app-member-s4.cfg)

#### [App Autotest MultiEnv Release Update](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/Apps/job/admin-dashboard/job/App%20Autotest%20MultiEnv%20Release%20Update/)

* [scenarios/app-testing/autotest-110-release-appupdate-master-no-samba.cfg](scenarios/app-testing/autotest-110-release-appupdate-master-no-samba.cfg)
* [scenarios/app-testing/autotest-111-release-appupdate-master-s4.cfg](scenarios/app-testing/autotest-111-release-appupdate-master-s4.cfg)
* [scenarios/app-testing/autotest-112-release-appupdate-backup-no-samba.cfg](scenarios/app-testing/autotest-112-release-appupdate-backup-no-samba.cfg)
* [scenarios/app-testing/autotest-113-release-appupdate-backup-s4.cfg](scenarios/app-testing/autotest-113-release-appupdate-backup-s4.cfg)
* [scenarios/app-testing/autotest-114-release-appupdate-slave-no-samba.cfg](scenarios/app-testing/autotest-114-release-appupdate-slave-no-samba.cfg)
* [scenarios/app-testing/autotest-115-release-appupdate-slave-s4.cfg](scenarios/app-testing/autotest-115-release-appupdate-slave-s4.cfg)
* [scenarios/app-testing/autotest-116-release-appupdate-member-no-samba.cfg](scenarios/app-testing/autotest-116-release-appupdate-member-no-samba.cfg)
* [scenarios/app-testing/autotest-117-release-appupdate-member-s4.cfg](scenarios/app-testing/autotest-117-release-appupdate-member-s4.cfg)

#### [App Autotest Update MultiEnv](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/Apps/job/admin-dashboard/job/App%20Autotest%20Update%20MultiEnv/)

* [scenarios/app-testing/autotest-120-appupdate-master-no-samba.cfg](scenarios/app-testing/autotest-120-appupdate-master-no-samba.cfg)
* [scenarios/app-testing/autotest-121-appupdate-master-s4.cfg](scenarios/app-testing/autotest-121-appupdate-master-s4.cfg)
* [scenarios/app-testing/autotest-122-appupdate-backup-no-samba.cfg](scenarios/app-testing/autotest-122-appupdate-backup-no-samba.cfg)
* [scenarios/app-testing/autotest-123-appupdate-backup-s4.cfg](scenarios/app-testing/autotest-123-appupdate-backup-s4.cfg)
* [scenarios/app-testing/autotest-124-appupdate-slave-no-samba.cfg](scenarios/app-testing/autotest-124-appupdate-slave-no-samba.cfg)
* [scenarios/app-testing/autotest-125-appupdate-slave-s4.cfg](scenarios/app-testing/autotest-125-appupdate-slave-s4.cfg)
* [scenarios/app-testing/autotest-126-appupdate-member-no-samba.cfg](scenarios/app-testing/autotest-126-appupdate-member-no-samba.cfg)
* [scenarios/app-testing/autotest-127-appupdate-member-s4.cfg](scenarios/app-testing/autotest-127-appupdate-member-s4.cfg)

#### [App Appliances Tests](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/App%20Appliances%20Tests/)

* [scenarios/appliance-testing/ad-member.cfg](scenarios/appliance-testing/ad-member.cfg)
* [scenarios/appliance-testing/master.cfg](scenarios/appliance-testing/master.cfg)
* [scenarios/appliance-testing/master-no-internet.cfg](scenarios/appliance-testing/master-no-internet.cfg)
* [scenarios/appliance-testing/fast-demo.cfg](scenarios/appliance-testing/fast-demo.cfg)

-----

## [Product tests](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/view/Product%20Tests/)

1. Last minute tests before new release

* [product-tests/appcenter/first-run.cfg](product-tests/appcenter/first-run.cfg)
* [product-tests/base/fake-listener.cfg](product-tests/base/fake-listener.cfg): Test joining with FAKE init
* [product-tests/base/ldap-in-samba-domain.cfg](product-tests/base/ldap-in-samba-domain.cfg)
* [product-tests/base/ldap-non-samba-domain.cfg](product-tests/base/ldap-non-samba-domain.cfg)
* [product-tests/base/saml.cfg](product-tests/base/saml.cfg)
* [product-tests/base/saml-kvm.cfg](product-tests/base/saml-kvm.cfg)
* [product-tests/component/office365.cfg](product-tests/component/office365.cfg)
* [product-tests/component/openid-connect.cfg](product-tests/component/openid-connect.cfg)
* [product-tests/domain-join/linuxmint-20.cfg](product-tests/domain-join/linuxmint-20.cfg)
* [product-tests/domain-join/ubuntu-20.04.cfg](product-tests/domain-join/ubuntu-20.04.cfg)
* [product-tests/samba/ad-takeover-admembermode.cfg](product-tests/samba/ad-takeover-admembermode.cfg)
* [product-tests/samba/ad-takeover-all-tests.cfg](product-tests/samba/ad-takeover-all-tests.cfg)
* [product-tests/samba/ad-trust.cfg](product-tests/samba/ad-trust.cfg)
* [product-tests/samba/bigenv.cfg](product-tests/samba/bigenv.cfg)
* [product-tests/samba/multi-server.cfg](product-tests/samba/multi-server.cfg)
* [product-tests/samba/single-server.cfg](product-tests/samba/single-server.cfg)
* [product-tests/umc/multi-server.cfg](product-tests/umc/multi-server.cfg)
* [product-tests/samba/smbtorture.cfg](product-tests/samba/smbtorture.cfg)
* [product-tests/component/keycloak_2backups.cfg](product-tests/component/keycloak_2backups.cfg)
* [product-tests/component/dcd_all_roles.cfg](product-tests/component/dcd_all_roles.cfg)
* [product-tests/component/dcd_redis_primary_change.cfg](product-tests/component/dcd_redis_primary_change.cfg)
* [product-tests/component/office365_update.cfg](product-tests/component/office365_update.cfg)

-----

## [UCS@school](https://jenkins2022.knut.univention.de/job/UCSschool-5.0/)

* [product-tests/ucsschool/largeenv-installation.cfg](product-tests/ucsschool/largeenv-installation.cfg)
* [product-tests/ucsschool/migration.cfg](product-tests/ucsschool/migration.cfg)
* [product-tests/ucsschool/multiserver.cfg](product-tests/ucsschool/multiserver.cfg)
* [product-tests/ucsschool/performance-500.cfg](product-tests/ucsschool/performance-500.cfg)
* [product-tests/ucsschool/performance-30000.cfg](product-tests/ucsschool/performance-30000.cfg)
* [product-tests/ucsschool/performance-65000.cfg](product-tests/ucsschool/performance-65000.cfg)
* [product-tests/ucsschool/schooljoin-200000-users.cfg](product-tests/ucsschool/schooljoin-200000-users.cfg)
* [scenarios/veyon/veyon.cfg](scenarios/veyon/veyon.cfg)

### [U@S performance tests](https://jenkins.knut.univention.de:8181/job/UCSschool%205.0%20Performance/)

* [scenarios/ucsschool-performance-30000.cfg](scenarios/ucsschool-performance-30000.cfg) → [UCSschool 5.0 Performance 30000](https://jenkins.knut.univention.de:8181/job/UCSschool%205.0%20Performance/job/UCSschool%205.0%20Performance%2030000/)
* [scenarios/ucsschool-performance-500.cfg](scenarios/ucsschool-performance-500.cfg) → [UCSschool 5.0 Performance 500](https://jenkins.knut.univention.de:8181/job/UCSschool%205.0%20Performance/job/UCSschool%205.0%20Performance%20500/)
* [scenarios/ucsschool-performance-65000.cfg](scenarios/ucsschool-performance-65000.cfg) → [UCSschool 5.0 Performance 65000](https://jenkins.knut.univention.de:8181/job/UCSschool%205.0%20Performance/job/UCSschool%205.0%20Performance%2065000/)
* [scenarios/ucsschool-performance-new-import-10000.cfg](scenarios/ucsschool-performance-new-import-10000.cfg) → [UCSschool 5.0 Performance NewImport 10.000](https://jenkins.knut.univention.de:8181/job/UCSschool%205.0%20Performance/job/UCSschool%205.0%20Performance%20NewImport%2010.000/)

### Regular tests

* [scenarios/autotest-201-ucsschool-singleserver-s4.cfg](scenarios/autotest-201-ucsschool-singleserver-s4.cfg): Install U@S 5.0 Singleserver
* [scenarios/autotest-203-ucsschool-multiserver-s4.cfg](scenarios/autotest-203-ucsschool-multiserver-s4.cfg): Install U@S 5.0 Multiserver
* [scenarios/autotest-206-ucsschool-update-singleserver-s4.cfg](scenarios/autotest-206-ucsschool-update-singleserver-s4.cfg): Update U@S 4.3 to U@S 5.0 Singleserver
* [scenarios/autotest-208-ucsschool-update-multiserver-s4.cfg](scenarios/autotest-208-ucsschool-update-multiserver-s4.cfg): Update U@S 4.3 to U@S 5.0 Multiserver
* [scenarios/autotest-241-ucsschool-kelvin-API.cfg](scenarios/autotest-241-ucsschool-kelvin-API.cfg): UCS@School KELVIN tests
* [scenarios/autotest-242-ucsschool-DL-MV.cfg](scenarios/autotest-242-ucsschool-DL-MV.cfg): obsolete, remove?
* [scenarios/autotest-243-ucsschool-DL-SH.cfg](scenarios/autotest-243-ucsschool-DL-SH.cfg): obsolete, remove?
* [scenarios/autotest-244-ucsschool-id-sync.cfg](scenarios/autotest-244-ucsschool-id-sync.cfg): UCSschool ID Connector
* [scenarios/autotest-245-ucsschool-apple-school-manager.cfg](scenarios/autotest-245-ucsschool-apple-school-manager.cfg): UCS@School apple school manager tests
* [scenarios/autotest-247-ucsschool-id-broker.cfg](scenarios/autotest-247-ucsschool-id-broker.cfg) UCS@School ID Broker tests
* [scenarios/autotest-247-ucsschool-id-broker-additional-traeger-staging.cfg](scenarios/autotest-247-ucsschool-id-broker-additional-traeger-staging.cfg)
* [scenarios/autotest-247-ucsschool-id-broker-perf-ec2.cfg](scenarios/autotest-247-ucsschool-id-broker-perf-ec2.cfg): ID Broker Performance (EC2)
* [scenarios/autotest-247-ucsschool-id-broker-perf-kvm.cfg](scenarios/autotest-247-ucsschool-id-broker-perf-kvm.cfg): ID Broker Performance (KVM)
* [scenarios/autotest-248-ram-rankine.cfg](scenarios/autotest-248-ram-rankine.cfg): UCS@School RAM tests
* [scenarios/autotest-248-ram-rankine-performance.cfg](scenarios/autotest-248-ram-rankine-performance.cfg): UCS@School RAM performance tests
* [scenarios/autotest-300-ucsschool-large.cfg](scenarios/autotest-300-ucsschool-large.cfg): Install U@S 5.0 Multiserver Large Env
