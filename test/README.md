# Tests

## UCS

### [Default](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/)

#### [MultiEnv: AMI<5.0, join, upgrade=5.0, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/AutotestUpgrade/)

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

#### [MultiEnv: AMI=5.0, errata, join, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/AutotestJoin/)
#### [MultiEnv: AMI=5.0, only released errata, join, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/AutotestJoinReleased/)

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

#### [Tests - AD Connector (ec2)](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/ADConnectorMultiEnv/)

1. AD connector setups with different windows versions

* [scenarios/ad-connector/autotest-231-adsync-w2k12-german.cfg](scenarios/ad-connector/autotest-231-adsync-w2k12-german.cfg)
* [scenarios/ad-connector/autotest-232-adsync-w2k8r2-english.cfg](scenarios/ad-connector/autotest-232-adsync-w2k8r2-english.cfg)
* [scenarios/ad-connector/autotest-232-adsync-w2k8r2-english-same-domain.cfg](scenarios/ad-connector/autotest-232-adsync-w2k8r2-english-same-domain.cfg)
* [scenarios/ad-connector/autotest-233-adsync-w2k12r2-france.cfg](scenarios/ad-connector/autotest-233-adsync-w2k12r2-france.cfg)
* [scenarios/ad-connector/autotest-234-adsync-w2k16-german.cfg](scenarios/ad-connector/autotest-234-adsync-w2k16-german.cfg)
* [scenarios/ad-connector/autotest-235-adsync-w2k19-english.cfg](scenarios/ad-connector/autotest-235-adsync-w2k19-english.cfg)
* [scenarios/ad-connector/autotest-236-adsync-w2k8r2-german.cfg](scenarios/ad-connector/autotest-236-adsync-w2k8r2-german.cfg)
* [scenarios/ad-connector/autotest-237-adsync-s4connector-w2k8r2-german.cfg](scenarios/ad-connector/autotest-237-adsync-s4connector-w2k8r2-german.cfg)
* [scenarios/ad-connector/autotest-adsync-w2012-german.cfg](scenarios/ad-connector/autotest-adsync-w2012-german.cfg)

#### [Tests - AD Member Mode (ec2)](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-r/job/ADMemberMultiEnv/)

1. AD member setups for installation/module with different windows versions

* [scenarios/ad-membermode/autotest-221-admember-w2019-english.cfg](scenarios/ad-membermode/autotest-221-admember-w2019-english.cfg)
* [scenarios/ad-membermode/autotest-222-admember-w2k8r2-german.cfg](scenarios/ad-membermode/autotest-222-admember-w2k8r2-german.cfg)
* [scenarios/ad-membermode/autotest-223-admember-w2k12-german-slave.cfg](scenarios/ad-membermode/autotest-223-admember-w2k12-german-slave.cfg)
* [scenarios/ad-membermode/autotest-224-admember-w2k12-german-other-join-user.cfg](scenarios/ad-membermode/autotest-224-admember-w2k12-german-other-join-user.cfg)
* [scenarios/ad-membermode/autotest-225-admember-w2k12r2-france.cfg](scenarios/ad-membermode/autotest-225-admember-w2k12r2-france.cfg)

#### [Tests - App Appliance](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/App%20Appliance%20Tests/)

UCS with pre-installed App, to check if changes in UCS break the appliance setup

* [scenarios/appliance-testing/app-appliance-errata-test.cfg](scenarios/appliance-testing/app-appliance-errata-test.cfg)
* [scenarios/appliance-testing/app-appliance-only-released.cfg](scenarios/appliance-testing/app-appliance-only-released.cfg)

#### [Tests - DVD Installation](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/Installation%20Tests/)

1. Various UCS installation tests (fail immediately if one setup step fails, only basic tests)

* [scenarios/install-testing/ad-member.cfg](scenarios/install-testing/ad-member.cfg)
* [scenarios/install-testing/base.cfg](scenarios/install-testing/base.cfg)
* [scenarios/install-testing/master-all-components.cfg](scenarios/install-testing/master-all-components.cfg)
* [scenarios/install-testing/master-english-static-ip.cfg](scenarios/install-testing/master-english-static-ip.cfg)
* [scenarios/install-testing/master-french-static-ip.cfg](scenarios/install-testing/master-french-static-ip.cfg)
* [scenarios/install-testing/net-installer.cfg](scenarios/install-testing/net-installer.cfg)
* [scenarios/install-testing/samba-env.cfg](scenarios/install-testing/samba-env.cfg)
* [scenarios/install-testing/school.cfg](scenarios/install-testing/school.cfg)
* [scenarios/install-testing/school-dev.cfg](scenarios/install-testing/school-dev.cfg)
* [scenarios/install-testing/school-scope.cfg](scenarios/install-testing/school-scope.cfg)

#### [Tests - S4Connector](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/S4Connector/)

1. Install/Update/OnlyReleasedErrata scenario for S4Connector tests.

* [scenarios/s4-connector/master-only-released-errata-s4connector.cfg](scenarios/s4-connector/master-only-released-errata-s4connector.cfg)
* [scenarios/s4-connector/master-s4connector.cfg](scenarios/s4-connector/master-s4connector.cfg)
* [scenarios/s4-connector/update-master-s4connector.cfg](scenarios/s4-connector/update-master-s4connector.cfg)

### [Tests - UCS update](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/job/Update%20Tests/)

1. Various UCS update tests (fail immediately if one setup step fails, only basic tests)

* [scenarios/update-testing/smbtorture.cfg](scenarios/update-testing/smbtorture.cfg): Master to latest and smbtorture tests
* [scenarios/update-testing/update-from-1.2.cfg](scenarios/update-testing/update-from-1.2.cfg)
* [scenarios/update-testing/update-from-1.2-start-4.3-4.cfg](scenarios/update-testing/update-from-1.2-start-4.3-4.cfg): Update from old UCS-1.2 system
* [scenarios/update-testing/update-from-4.2-4.cfg](scenarios/update-testing/update-from-4.2-4.cfg): Update system with all UCS components

### [MultiEnv: IPv6 AMI\<5.0, upgrade=5.0, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/All/job/AutotestIPv6Update/)
### [MultiEnv: IPv6 AMI=5.0, Autotest](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/All/job/AutotestIPv6/)

1. (Master / Backup / Slave / Member) × (IPv4 + IPv& / IPv6 only)
2. previous AMI
3. upgrade
4. join

* [scenarios/ipv6/generic/autotest-300-master46-slave46.cfg](scenarios/ipv6/generic/autotest-300-master46-slave46.cfg)
* [scenarios/ipv6/generic/autotest-301-master46-backup46.cfg](scenarios/ipv6/generic/autotest-301-master46-backup46.cfg)
* [scenarios/ipv6/generic/autotest-302-master46-member46.cfg](scenarios/ipv6/generic/autotest-302-master46-member46.cfg)
* [scenarios/ipv6/generic/autotest-303-master46-slave6.cfg](scenarios/ipv6/generic/autotest-303-master46-slave6.cfg)
* [scenarios/ipv6/generic/autotest-304-master46-backup6.cfg](scenarios/ipv6/generic/autotest-304-master46-backup6.cfg)
* [scenarios/ipv6/generic/autotest-305-master46-member6.cfg](scenarios/ipv6/generic/autotest-305-master46-member6.cfg)
* [scenarios/ipv6/generic/autotest-306-master6-slave46.cfg](scenarios/ipv6/generic/autotest-306-master6-slave46.cfg)
* [scenarios/ipv6/generic/autotest-307-master6-backup46.cfg](scenarios/ipv6/generic/autotest-307-master6-backup46.cfg)
* [scenarios/ipv6/generic/autotest-308-master6-member46.cfg](scenarios/ipv6/generic/autotest-308-master6-member46.cfg)
* [scenarios/ipv6/generic/autotest-309-master6-slave6.cfg](scenarios/ipv6/generic/autotest-309-master6-slave6.cfg)
* [scenarios/ipv6/generic/autotest-310-master6-backup6.cfg](scenarios/ipv6/generic/autotest-310-master6-backup6.cfg)
* [scenarios/ipv6/generic/autotest-311-master6-member6.cfg](scenarios/ipv6/generic/autotest-311-master6-member6.cfg)
* [scenarios/ipv6/generic/autotest-312-master46-masteronly.cfg](scenarios/ipv6/generic/autotest-312-master46-masteronly.cfg)
* [scenarios/ipv6/generic/autotest-313-master6-masteronly.cfg](scenarios/ipv6/generic/autotest-313-master6-masteronly.cfg)

-----

### [Appliances](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/Appliances/)

* [scenarios/app-appliance.cfg](scenarios/app-appliance.cfg): Create App Appliance (Stable.ISO → $mm-99 → +App → `$BS2/mirror/appcenter.test/univention-apps/current/`KVM,VMware,ESX,VirtualBox)
* [scenarios/ucs-appliance.cfg](scenarios/ucs-appliance.cfg): Create UCS Appliance (Stable.ISO → $mm-99 → `$BS2/temp/build/appliance/`KVM,VMware,ESX,VirtualBox,HyperV)
* [scenarios/appliances/ec2-appliance.cfg](scenarios/appliances/ec2-appliance.cfg): Create UCS ec2 image (Stable.ISO → `$VIRT/images/`KVM → EC2)
* [scenarios/cloud-init-image.cfg](scenarios/cloud-init-image.cfg)

#### [Test UCS Appliance](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/Appliances/job/TestUCSAppliance/)

* [scenarios/ucs-appliance-testing/ad-member.cfg](scenarios/ucs-appliance-testing/ad-member.cfg)
* [scenarios/ucs-appliance-testing/master.cfg](scenarios/ucs-appliance-testing/master.cfg)
* [scenarios/ucs-appliance-testing/master-slave.cfg](scenarios/ucs-appliance-testing/master-slave.cfg)

#### [Test EC2 UCS Appliance](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/Appliances/job/TestEC2UCSAppliance/)

* [scenarios/ucs-appliance-testing/ad-member-ec2.cfg](scenarios/ucs-appliance-testing/ad-member-ec2.cfg)
* [scenarios/ucs-appliance-testing/master-ec2.cfg](scenarios/ucs-appliance-testing/master-ec2.cfg)
* [scenarios/ucs-appliance-testing/master-slave-ec2.cfg](scenarios/ucs-appliance-testing/master-slave-ec2.cfg)

-----

### [KVM Templates](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/KVM%20Templates/)

* [scenarios/appliances/generic-kvm-template.cfg](scenarios/appliances/generic-kvm-template.cfg): Create generic `ucs-kt-get` template
* [scenarios/appliances/joined-kvm-templates.cfg](scenarios/appliances/joined-kvm-templates.cfg): Create `ucs-kt-get` templates for joined UCS roles
* [scenarios/appliances/role-kvm-templates.cfg](scenarios/appliances/role-kvm-templates.cfg): Create `ucs-kt-get` templates for UCS roles

-----

### VM creation

* [scenarios/base/ucs-master-backup.cfg](scenarios/base/ucs-master-backup.cfg): Setup Master and Backup unjoined
* [scenarios/base/ucs-master-backup-joined.cfg](scenarios/base/ucs-master-backup-joined.cfg): Setup Master and Backup joined

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

* [scenarios/ipv6/update/autotest-300-master46-slave46.cfg](scenarios/ipv6/update/autotest-300-master46-slave46.cfg)
* [scenarios/ipv6/update/autotest-301-master46-backup46.cfg](scenarios/ipv6/update/autotest-301-master46-backup46.cfg)
* [scenarios/ipv6/update/autotest-302-master46-member46.cfg](scenarios/ipv6/update/autotest-302-master46-member46.cfg)
* [scenarios/ipv6/update/autotest-303-master46-slave6.cfg](scenarios/ipv6/update/autotest-303-master46-slave6.cfg)
* [scenarios/ipv6/update/autotest-304-master46-backup6.cfg](scenarios/ipv6/update/autotest-304-master46-backup6.cfg)
* [scenarios/ipv6/update/autotest-305-master46-member6.cfg](scenarios/ipv6/update/autotest-305-master46-member6.cfg)
* [scenarios/ipv6/update/autotest-306-master6-slave46.cfg](scenarios/ipv6/update/autotest-306-master6-slave46.cfg)
* [scenarios/ipv6/update/autotest-307-master6-backup46.cfg](scenarios/ipv6/update/autotest-307-master6-backup46.cfg)
* [scenarios/ipv6/update/autotest-308-master6-member46.cfg](scenarios/ipv6/update/autotest-308-master6-member46.cfg)
* [scenarios/ipv6/update/autotest-309-master6-slave6.cfg](scenarios/ipv6/update/autotest-309-master6-slave6.cfg)
* [scenarios/ipv6/update/autotest-310-master6-backup6.cfg](scenarios/ipv6/update/autotest-310-master6-backup6.cfg)
* [scenarios/ipv6/update/autotest-311-master6-member6.cfg](scenarios/ipv6/update/autotest-311-master6-member6.cfg)
* [scenarios/ipv6/update/autotest-312-master46-masteronly.cfg](scenarios/ipv6/update/autotest-312-master46-masteronly.cfg)
* [scenarios/ipv6/update/autotest-313-master6-masteronly.cfg](scenarios/ipv6/update/autotest-313-master6-masteronly.cfg)

* [scenarios/ipv6/autotest-300-master46-slave46.cfg](scenarios/ipv6/autotest-300-master46-slave46.cfg)
* [scenarios/ipv6/autotest-301-master46-backup46.cfg](scenarios/ipv6/autotest-301-master46-backup46.cfg)
* [scenarios/ipv6/autotest-302-master46-member46.cfg](scenarios/ipv6/autotest-302-master46-member46.cfg)
* [scenarios/ipv6/autotest-303-master46-slave6.cfg](scenarios/ipv6/autotest-303-master46-slave6.cfg)
* [scenarios/ipv6/autotest-304-master46-backup6.cfg](scenarios/ipv6/autotest-304-master46-backup6.cfg)
* [scenarios/ipv6/autotest-305-master46-member6.cfg](scenarios/ipv6/autotest-305-master46-member6.cfg)
* [scenarios/ipv6/autotest-306-master6-slave46.cfg](scenarios/ipv6/autotest-306-master6-slave46.cfg)
* [scenarios/ipv6/autotest-307-master6-backup46.cfg](scenarios/ipv6/autotest-307-master6-backup46.cfg)
* [scenarios/ipv6/autotest-308-master6-member46.cfg](scenarios/ipv6/autotest-308-master6-member46.cfg)
* [scenarios/ipv6/autotest-309-master6-slave6.cfg](scenarios/ipv6/autotest-309-master6-slave6.cfg)
* [scenarios/ipv6/autotest-310-master6-backup6.cfg](scenarios/ipv6/autotest-310-master6-backup6.cfg)
* [scenarios/ipv6/autotest-311-master6-member6.cfg](scenarios/ipv6/autotest-311-master6-member6.cfg)
* [scenarios/ipv6/autotest-312-master46-masteronly.cfg](scenarios/ipv6/autotest-312-master46-masteronly.cfg)
* [scenarios/ipv6/autotest-313-master6-masteronly.cfg](scenarios/ipv6/autotest-313-master6-masteronly.cfg)

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

## [UCS Branch Test](https://jenkins.knut.univention.de:8181/job/UCS%20Branch%20Test/)

1. Used by developers to test specific areas of UCS

* [branch-tests/appcenter/singlemaster.cfg](branch-tests/appcenter/singlemaster.cfg)
* [branch-tests/base/bug48427-backup-rejoin.cfg](branch-tests/base/bug48427-backup-rejoin.cfg)
* [branch-tests/base/bug48427-master-after-backup.cfg](branch-tests/base/bug48427-master-after-backup.cfg)
* [branch-tests/base/bug48427-master-before-backup.cfg](branch-tests/base/bug48427-master-before-backup.cfg)
* [branch-tests/base/bug48427-setup.cfg](branch-tests/base/bug48427-setup.cfg)
* [branch-tests/base/bug48427-single-master.cfg](branch-tests/base/bug48427-single-master.cfg)
* [branch-tests/base/master-slave.cfg](branch-tests/base/master-slave.cfg)
* [branch-tests/base/singlemaster-all-components.cfg](branch-tests/base/singlemaster-all-components.cfg)
* [branch-tests/base/singlemaster.cfg](branch-tests/base/singlemaster.cfg)
* [branch-tests/base/singlemaster-joined.cfg](branch-tests/base/singlemaster-joined.cfg)
* [branch-tests/create_templates/singlemaster-joined.cfg](branch-tests/create_templates/singlemaster-joined.cfg)
* [branch-tests/mail/joined-master.cfg](branch-tests/mail/joined-master.cfg)
* [branch-tests/samba/s4-connector.cfg](branch-tests/samba/s4-connector.cfg)
* [branch-tests/school/multiserver.cfg](branch-tests/school/multiserver.cfg)
* [branch-tests/singlemaster.cfg](branch-tests/singlemaster.cfg)
* [branch-tests/umc/singlemaster.cfg](branch-tests/umc/singlemaster.cfg)

-----

## [Product tests](https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-2/view/Product%20Tests/)

1. Last minute tests before new release

* [product-tests/appcenter/first-run.cfg](product-tests/appcenter/first-run.cfg)
* [product-tests/appcenter/ucs-tests.cfg](product-tests/appcenter/ucs-tests.cfg)
* [product-tests/base/fake-listener.cfg](product-tests/base/fake-listener.cfg): Test joining with FAKE init
* [product-tests/base/ldap-in-samba-domain.cfg](product-tests/base/ldap-in-samba-domain.cfg)
* [product-tests/base/ldap-non-samba-domain.cfg](product-tests/base/ldap-non-samba-domain.cfg)
* [product-tests/base/saml.cfg](product-tests/base/saml.cfg)
* [product-tests/base/saml-kvm.cfg](product-tests/base/saml-kvm.cfg)
* [product-tests/component/office365.cfg](product-tests/component/office365.cfg)
* [product-tests/component/openid-connect.cfg](product-tests/component/openid-connect.cfg)
* [product-tests/domain-join/linuxmint-20.cfg](product-tests/domain-join/linuxmint-20.cfg)
* [product-tests/domain-join/ubuntu-20.04.cfg](product-tests/domain-join/ubuntu-20.04.cfg)
* [product-tests/extsec4.3/00026.cfg](product-tests/extsec4.3/00026.cfg)
* [product-tests/python3/ucs-tests.cfg](product-tests/python3/ucs-tests.cfg)
* [product-tests/samba/ad-takeover-admembermode.cfg](product-tests/samba/ad-takeover-admembermode.cfg)
* [product-tests/samba/ad-takeover-all-tests.cfg](product-tests/samba/ad-takeover-all-tests.cfg)
* [product-tests/samba/ad-trust.cfg](product-tests/samba/ad-trust.cfg)
* [product-tests/samba/bigenv.cfg](product-tests/samba/bigenv.cfg)
* [product-tests/samba/multi-server.cfg](product-tests/samba/multi-server.cfg)
* [product-tests/samba/s4-connector.cfg](product-tests/samba/s4-connector.cfg)
* [product-tests/samba/scaling-test.cfg](product-tests/samba/scaling-test.cfg)
* [product-tests/samba/single-server.cfg](product-tests/samba/single-server.cfg)
* [product-tests/samba/update-tests.cfg](product-tests/samba/update-tests.cfg)
* [product-tests/ucsschool/largeenv-installation.cfg](product-tests/ucsschool/largeenv-installation.cfg)
* [product-tests/ucsschool/migration.cfg](product-tests/ucsschool/migration.cfg)
* [product-tests/ucsschool/multiserver.cfg](product-tests/ucsschool/multiserver.cfg)
* [product-tests/ucsschool/performance-30000.cfg](product-tests/ucsschool/performance-30000.cfg)
* [product-tests/ucsschool/performance-500.cfg](product-tests/ucsschool/performance-500.cfg)
* [product-tests/ucsschool/performance-65000.cfg](product-tests/ucsschool/performance-65000.cfg)
* [product-tests/umc/multi-server.cfg](product-tests/umc/multi-server.cfg)
* [product-tests/umc/singlemaster.cfg](product-tests/umc/singlemaster.cfg)

-----

## [UCS@school](https://jenkins2022.knut.univention.de/job/UCSschool-5.0/)

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
* [scenarios/autotest-241-ucsschool-HTTP-API.cfg](scenarios/autotest-241-ucsschool-HTTP-API.cfg): HTTP-APIs tests
* [scenarios/autotest-242-ucsschool-DL-MV.cfg](scenarios/autotest-242-ucsschool-DL-MV.cfg): DL MV
* [scenarios/autotest-243-ucsschool-DL-SH.cfg](scenarios/autotest-243-ucsschool-DL-SH.cfg): DL SH
* [scenarios/autotest-244-ucsschool-id-sync.cfg](scenarios/autotest-244-ucsschool-id-sync.cfg): UCSschool ID Connector
* [scenarios/autotest-300-ucsschool-large.cfg](scenarios/autotest-300-ucsschool-large.cfg): Install U@S 5.0 Multiserver Large Env
