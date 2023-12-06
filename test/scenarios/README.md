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


UCS Branch Tests
================

In order to test change from feature branches we need a way to add repositories to our test instances (via our scenario files), for that we have:

**packages from gitlab pipeline:**

* use `utils.sh::add_extra_branch_repository()`
* uses env var `UCS_ENV_UCS_BRANCH` (an ucs branch name)
* adds `http://omar.knut.univention.de/build2/git` sources list for corresonding repository
* adds apt.conf for that repo with priority 1001 (install, downgrade from this repo)

**packages from different scope repository**

* use `utils.sh::add_extra_apt_scope()`
* uses env var `SCOPE` (an ucs build scope)
* **TODO** merge with univention/dist/jenkins#2 - `UCS_ENV_APT_REPO` and `UCS_ENV_APT_PREFS`

Jenkins
-------

The idea is that we have dedicated jenkins jobs for different scenarios which can be used to test the "pipeline" packages from ucs feature branches (or packags from a custome scope).

* because we don't want to spoil the history of the daily jobs
* make it as easy as possible for dev's to start branch tests

These jenkins jobs

* a required parameter `UCS_ENV_UCS_BRANCH`
* checks out this ucs branch and starts the scenario
* adds the gitlab branch repo and from that on just the usual setup and test runs

See https://jenkins2022.knut.univention.de/job/UCS-5.0/job/UCS-5.0-6/view/Branch%20test%20(WIP)/ for what we have so far.

New jobs can be added in the jenkins seed file in the univention/dist/jenkins repository.

