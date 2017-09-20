Main
====
AutotestJoin
------------
Description:
	Latest UCS can be used:

	1. current AMI
	2. errata
	3. join
	4. tests
Schedule:
	Runs every night.
Files:
	`autotest-09?-${Role}-${Samba}.cfg`

AutotestErrrata
---------------
Description:
	Installing errata does not break existing setups:

	1. current AMI
	2. join
	3. errata
	4. tests
Schedule:
	Should run once before errata are announced on Wednesday.
Files:
	`setup-testing/${Role}-${Samba}.cfg`
	`autotest-09?-${Role}-${Samba}-update.cfg`

AutotestUpgrade
---------------
Description:
	Old UCS can be upgrades to latest:

	1. previous UCS + latest published errata
	2. join
	3. upgrade to current release + errata
	4. tests
Schedule:
	On demand before release
Files:
	`autotest-07?-update-?.?-to-?.?-*-*.cfg`

Update Tests
------------
Description:
	Upgrade from (very) old UCS and/or with Apps installed
Schedule:
	On demand
Files:
	`update-testing/update-from-${Scenario}.cfg`

AD-Connector
============
ADConnectorMultiEnv
-------------------
Description:
Schedule:
	On demand
Files:
	`autotest-23?-adsync-${Version}.cfg`

ADMemberMultiEnv
-------------------
Description:
Schedule:
	On demand
Files:
	`autotest-22?-admember-${Mode}-${Version}.cfg`

IPv6
====
AutotestIPv6Update
------------------
Description:
Schedule:
	Disabled
Files:
	`ipv6/autotest-3??-${RoleMaster}-${RoleOther}.cfg`

AutotestIPv6Update
------------------
Description:
Schedule:
	Disabled
Files:
	`ipv6/autotest-3??-${RoleMaster}-${RoleOther}.cfg`
