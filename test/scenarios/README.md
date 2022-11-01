_[TOC]_

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

Personal environments via Jenkins Job
=====================================

Altough every scenario can be started on the local computer via the docker tool ucs-ec2/kvm-create, sometimes it is easier to have a dedicated Jenkins Job for certain environments
* Because jenkins-data does not have to be in sync (at least in the personal computer)
* It is even easier to just press on a button
* We can provide meaningful defaults

Personal environments just means, that the name of the instance starts with the uid of the user that started the job.

To create a such a job, add the job to the appropriate seed script in univention/dist/jenkins>, e.g.
```
def ram_kvm = job("${cuas.jenkins_folder_name}/RAM-environment") {
    displayName('Create RAM Environment in KVM')
    description('Create an school env with a primary and a backup with the rankine APIs.')
    logRotator(28, 3, -1, -1)
    label(label_agents)
    wrappers {
        preBuildCleanup()
        timestamps()
    }
    parameters {
        configure EC2Tools.extensibleChoice('KVM_BUILD_SERVER', 'KVM_BUILD_SERVER', 'ranarp.knut.univention.de')
    }
    steps {
        shell('cd test && exec ./utils/ram/start-kvm.sh')
    }
}
EC2Tools.addUpdateParameters(ram_kvm, false, false)
EC2Tools.addUcsGit(ram_kvm, cucs.mmm, '/test/scenarios', '/test/utils')
```

and a start wrapper somewhere in univention/ucs>test/utils

```
#!/bin/bash

set -x
set -e

export KVM_BUILD_SERVER="${KVM_BUILD_SERVER:=tross.knut.univention.de}"
export HALT=false          # do not destroy instances after setup
export DOCKER=true         # use docker
export REPLACE=true        # replace existing instances
export UCS_TEST_RUN=false  # don't execte use-test

# user specific instances "username_..."
export KVM_OWNER="${BUILD_USER_ID:=$USER}"
export JOB_BASE_NAME="${JOB_BASE_NAME:=ram-env}"

exec ./utils/start-test.sh scenarios/autotest-248-ram-rankine.cfg
```

`BUILD_USER_ID` is set by jenkins to the uid of current logged in user and `KVM_OWNER` instructs ec2-kvm-create to create an instance with this "name" (pmueller_master-ucsschool-env) -> So this creates instances with YOUR uid in the name.

Best practice
-------------

* Whenever possible it is best to re-use an existing scenario file from a test job, so that we don't have to maintain multiple version of a scenario
* `export UCS_TEST_RUN=false` to disable ucs-test (so only setup, not tests), keep in mind to also add this to the environment section of the scenario file, so that the instnaces can see this varibale
