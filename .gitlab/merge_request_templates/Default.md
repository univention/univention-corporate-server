## :page_with_curl: Summary

(Summarize the bug encountered concisely)

## :bug: Source

(Provide the source URL of the [bugzilla bug](https://forge.univention.org/bugzilla/) and GitLab Issue)

## :recycle: Steps to reproduce

(How one can reproduce the issue - this is very important)

## :warning: What is the current bug behavior?

(What actually happens)

## :gem: What is the expected correct behavior?

(What you should see instead)

## :exclamation: QA requirements

### Server Roles

* [ ] UCS Primary Directory Node
* [ ] UCS Backup Directory Node
* [ ] UCS Replica Directory Node
* [ ] UCS Managed Node

### UCS Releases

* [ ] UCS 5.0
* [ ] UCS 4.4
* [ ] Mixed - UCS 4.4 server in UCS 5.0 domain

### Apps / Scenarios

* [ ] UCS@school
* [ ] Samba/AD
* [ ] non-Samba
* [ ] AD-Connector (including AD-Member)
* [ ] AD-Takeover

### Installation paths

* [ ] Errata update
* [ ] Minor Release update
* [ ] Major Release update

### Provisioning paths

* [ ] Fresh installation (of UCS or App/component)
* [ ] Initial Join
* [ ] Re-Join

## :zap: QA steps

* (Describe the steps to test the bug)
* See [QA Guide in Wiki](https://hutten.knut.univention.de/mediawiki/index.php/QA_-_Quality_Assurance#QA_Guide)

## :question: Checklist

* See [Checklist for fixing Bugs](https://hutten.knut.univention.de/mediawiki/index.php/Development_enivironment#Checklist_for_fixing_Bugs)
* See [QA Guide in Wiki](https://hutten.knut.univention.de/mediawiki/index.php/QA_-_Quality_Assurance#QA_Guide)
* Check YAML for correctness, spelling and readability.
* [ ] The documentation is updated. Check if there is a README.md in the package source, check if one should be created or updated.
* [ ] Check Jenkins job (`scenario`) for the bug.
* [ ] Check coding style.
* [ ] Is there a ucs-test case (needed)?
