`ucs-test` is used to check UCS installations for correct working and configuration.

# Structure
Tests are structured in [sections](#sections) and [tests](#single-tests).

## Sections
The tests are categorized in sections, which are represented as sub-directories like `/usr/share/ucs-test/00_section/`.
Every directory must begin with a two digit number followed by a name, separated by an underscore character.
Every section should be packaged in a separate (binary) Debian package to allow picking only relevant tests.

## Single tests
For every test a single executable file exists, which implements the test.
* The name of the file must begin with a two or three digit number, followed by a short description.
* No file extension (`.py`, `.sh`, …) must be used (as this gets interpreted as a separator by Jenkins).
* The file should be marked as executable.
* In the hash-bang-line `#!/usr/share/ucs-test/runner` should be used instead of using `/bin/bash` or `/usr/bin/python` directly.
  Is interpreter asserts several things:
  * The current working directory is changed to the directory containing the script.
  * Meta data information from the test case file are used to check the required system role, check for required packages and versions.
    The test is only run if those pre-conditions are met.
  * The (integer) return value of the test script is converted to a human readable message.

## Framework
Next to the test files some shell and Python libraries are provided below [/usr/share/ucs-test/lib/](lib/), which can be re-used by several tests.

[/usr/sbin/ucs-test](bin/ucs-test) is a program to run several tests at once.
It collects their output and creates some summary information.

# Packages
* `ucs-test-framework`: This package contains the minimum required files like [runner](bin/runner) and [ucs-test](bin/ucs-test).
* `ucs-test-libs`: This package contains the optional shared libraries used by several other packages.
* `ucs-test-*`: Each package contains the tests of the different sections.

## Libraries
The `ucs-test-libs` package provides several libraries for common tasks, such as creating and modifying UDM objects, handling UCR variables, or common functions to simplify writing robust tests.
Shell libraries should be included like this:
```sh
. "$TESTLIBPATH/name.sh" || exit 137
```
while Python libraries should be imported as regular modules like
```python
import univention.testing.name
```

Currently the following libraries are shipped:
- [base.sh](lib/base.sh): Output helpers, software checks, version checks, test helpers
- [computer.sh](lib/computer.sh): Simplify handling UDM computers
- [container.sh](lib/container.sh): Simplify handling UDM container
- [group.sh](lib/group.sh): Simplify handling UDM groups
- [ldap.sh](lib/ldap.sh): Directly interact with LDAP (uses [ldap_glue.py](lib/ldap_glue.py) internally)
- [maildomain.sh](lib/maildomain.sh): Simplify handling mail tests
- [master.sh](lib/master.sh): Execute commands remotely on Primary / Master
- [printer.sh](lib/printer.sh): Simplify handling printer tests
- [random.sh](lib/random.sh): Provide function to generate random names for different requirements
- [shares.sh](lib/shares.sh): Simplify handling UDM shares
- [ucr.sh](lib/ucr.sh): Wrapper around UCR to restore values on exit ;user.sh: Simplify handling UDM users
- [undo.sh](lib/undo.sh): Helper function for unding things in shell
- [user.sh](lib/user.sh): Simplify handling UDM users

Sections can also include their own helper files, which should have the suffix `.py` or `.sh` to distinguish them from regular tests.

## Working with LDAP objects
To allow the creation of LDAP objects on different system roles other than Primary and Backup, `ucs-test` set the following UCR variables during installation:
- `tests/domainadmin/account`: Domain administrator LDAP bind DN to be used in test cases
- `tests/domainadmin/pwd`: Domain administrator password to be used in test cases
- `tests/domainadmin/pwdfile`: File to read the domain administrator password

By default these variables are set to the the DN of `Administrator` and to the password `univention`.

To use these variables in a UDM call, `udm-test` can be used, for example:
```sh
#!/usr/share/ucs-test/runner bash
# shellcheck shell=bash
## desc: Create a container
## roles: domaincontroller_slave

. "$TESTLIBPATH/base.sh" || exit 137
. "$TESTLIBPATH/random.sh" || exit 137

container_name="$(random_chars 20)"
udm-test container/cn create --set name="$container_name"
wait_for_replication

univention-ldapsearch "cn=$container_name"
```

The function `wait_for_replication` checks if the replication is finished.
To wait also for the service restart, for example if a new printer was added, the function `wait_for_replication_and_postrun` can be used.

# Usage
Tests can be run in two ways.
Either directly using their fully qualified name (`/usr/share/ucs-test/00_section/00_test`), or using `ucs-test` to run several tests together.
`ucs-test` supports several options to select a subset of all installed tests, which are described in its manual page (<man:ucs-test>).

# Creating new tests
There is a [minimal](doc/template.min) and a [maximal](doc/template.max) template for new tests.
Make sure to run [lint](lint) before committing new tests.

## Minimal test
In its simplest form a test contains only some commands, which return `0` on success.
Any other return value is interpreted as a failure.

```sh
#!/usr/share/ucs-test/runner bash
# shellcheck shell=bash
## desc: Test if /etc/shadow exists
## exposure: safe
[ -f '/etc/shadow' ]
# vim: set filetype=sh tabstop=4 :
```

* line 1 uses `/usr/share/ucs-test/runner` instead of `/bin/bash`.
  This wrapper prints some more information in addition to the return value of the tests.
  The language used for the implementation of the test is passed as the sole parameter to this wrapper.
  Next to `bash`, `python`, `python2.7`, `python3`, `pytest`, `pytest-3` any other interpreter might be used as well as long as the fully qualified path to the interpreter is given.
* line 2 just tells `shellcheck` to use `bash` style.
* line 3 gives a description using the meta data syntax.
  This description is included in the output next to the return value.
  The meta data block must be located at the beginning of the file right after the hash-bang line with only comment lines in between.
  All lines must pre prefix by `## `.
* line 4 declares that the test is safe to be run on any system, even systems already in production.
* line 5 implements the tests.
* line 6 contains the configuration for the editor `vim`.

## Meta data
The meta data information consists of consecutively lines, which directly follow the hash-bang and comment lines.
The block ends at the first line not prefixed by `## `.
Without that prefix the format follows [YAML](http://yaml.org/).
This allows other programs to parse that information as well and also allows custom data (severity, author, ...) to be added.
`ucs-test` uses the following entries:

### desc
A text used as a description for this test, which is displayed together
with the test result when the test is run. The text can span multiple
lines, which allows adding detailed information. How much of the
description is displayed depends on the chosen output format.
```
## desc: A short text
## desc: |
##  A short text for displaying.
##  A longer text, which describes the test in more detail.
```

### bugs
A list of bug numbers from [Univention Bugzilla](https://forge.univention.de/bugzilla/).
Depending on the chosen output format (for example `html`), reports will include links to the referenced bugs.
```
## bugs: [23527]
## bugs:
##  - 23527
```

### otrs
A list of ticket numbers from [Univention OTRS](https://gorm.knut.univention.de/otrs/).
Depending on the chosen output format (for example `'html`'), reports will include links to the referenced tickets.
```
## otrs: [2012031912061xxx]
## otrs:
##  - 2012031912061xxx
```

### versions
A mapping from UCS versions number (`major.minor-patchlevel`) to the strings `found`, `fixed` and `skip`.
This allows to differentiate the return values and to distinguish between tests, which are for known not-yet-fixed bugs, and tests, which should be fixed but fail again.
- `found`: the bug is relevant starting from that version.
- `fixed`: the bug was fixed in this version and should not trigger.
- `skip`: the test should be skipped since that version.
```
## versions:
## 2.0-0: found
## 2.1-0: fixed
## 3.0-0: skip
```

### tags
A list of tags, which can be used to group tests.
This can be used to either run only a specific subset of all installed tests or prevent some tagged tests from running.
The name for tags can be chosen freely, but the following words have special meaning:
- `SKIP`, `WIP`: The test will be skipped by default, because — for example — the implementation is still work in progress.
- `basic`: Marks the tests as a basic test, which should be run on all systems to assert a sound installation.

In addition to them the following tags are used commonly:
- `apptest`: execute them only for testing new Apps, but otherwise skip them due to their long run time.
- `basic`: check that basic functions work on all system roles.
- `univention`: tests which require special pre-requisites, for exmaple *well known password* `univention` for admin user.
- `import500`, `import30000`, `import65000`, `performance`: performance tests for importing ½/30/65k users.
- `rename_default_account`: modifies standard accounts.
- `replication`: sub-set of tests for replication.
- `ldapextensions`: sub-set of tests for LDAP extensions.
- `producttest`: only relevant for UCS product tests, which tests one-time issues like for example re-joining an already joined system.
- `IPv4required`: tests require IPv4 or dual-stack.
- `IPv6required`: tests require IPv6 or dual-stack.
- `skip_admember`: tests to skip in *AD member modus*.
- `SKIP-UCSSCHOOL`:
- `udm-ldapextensions`:
- `udm`:
- `udm-computers`:
- `udm-net`:
- `udm-extensions`:
- `docker`:
- `saml`:
- `translation-template`:

```
## tags: [WIP]
## tags:
##  - my-tag
```

### roles
A list of UCS role names.
The test is only run on systems, which match the role name explicitly listed here.
The default is to allow the test to run on all roles.
```
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
##  - domaincontroller_slave
##  - memberserver
##  - basesystem
```

### roles-not
Inverse list for UCS role names.
The test is skipped on systems, which match the role name listed here.
Overlaps with [roles](#roles) will abort the test.
```
## roles-not: [basesystem]
```

### join
Requires or prohibits the system to be joined.
Otherwise the test is not run.
By default the join status is irrelevant and the test is run on all systems.
```
## join: true
```

### components
A mapping of component names to a boolean value, which requires the named component to be either installed or to be deactivated.
By default no components are required and the test is run on all systems.
```
## components:
##  tcs: true
##  dvs: false
```

### packages
A list of Debian package dependencies, which must be fulfilled.
Otherwise the test is not run on such a system.
Each entry follows the syntax used by [Debian dependencies](http://www.debian.org/doc/debian-policy/ch-relationships.html).
```
## packages:
##  - dpkg-dev (>= 1.15)
##  - apache2 | apache2-mpm-prefork
```
Normally dependencies should be specified using the Debian `debian/control` file.
But in some cases tests need special software, which is not wanted on normal systems.
This mechanism allows the user to still install the full `ucs-test-*` section package without forcing him to install several other packages only relevant for corner case tests.
By using this mechanism of `ucs-test`, tests still missing some dependent packages are skipped.

### exposure
A string consisting of one of the words `safe`, `careful` or `dangerous`.
This is used to classify tests in different categories:
- `safe`: tests of read data and never modify anything on the system.
  These tests can be run on production systems without danger of modifying that system or losing services.
- `careful`: test do modify the system (create files, restart services, change configurations), but revert all changes back to the original state at the end of the test, regardless of if the test succeeds or fails.
- `dangerous`: the test has side effects, which might change this and other systems in a way unfit for production systems.
  This includes — for example — creating users and groups in LDAP, re-configuring essential services like LDAP.
The default is `dangerous`.

### external-junit

Filename of a junit result file that is provided by the test itself.
This can be used — for example — if the test starts pytest in a container.
```
...
## external_junit: /tmp/my_test_results.xml
...
docker exec pytest --junit-xml=/tmp/junit.xml ...
docker cp container:/tmp/junit.xml /tmp/my_test_results.xml
```

## Return value
In its simplest case a test should return `0` for success and `1` on failure.
For backward compatibility to previous versions of `ucs-test` several other special values can be returned as well to provide more detailed information.
For exmaple `REASON_SKIP` and several others can be used to skip tests if the pre-conditions for running the test are not met, for example missing credentials or missing help software.
More information is available in the [source code](univention/testing/codes.py).

# Quality
`ucs-test` should be runnable on all systems, ranging from development machines to systems in production.
Because of this requirement test developers should be extremely careful before modifying system configuration or data.
To protect production systems from accidental destruction by running tests, `ucs-test` requires tests to follow the following criteria:
- a test should just test one thing, so a failed tests has a clear conclusion.
- a test should return stable results, so running the same test multiple times returns the same result each time.
- a test should not modify the system.
  If anything is changed, it **must** be changed back regardless if the test succeeds or fails.

To enforce this `ucs-test` by default refrains from running tests with an [#exposure](#exposure) level other then `safe`.

# Appendix

## Using pytest
Since UCS 4.4-8 tests can directly use [pytest](http://pytest.org/).
1. The file implementing the test must be executable and its name must have the suffix `.py`.
2. The hash-bang-line should be `#!/usr/share/ucs-test/runner [/usr/bin/]py[.]test[-3]` followed by additional options for `pytest`.

The following [markers](univention/testing/conftest.py) are supported:
* use `@pytest.mark.tags('apptest')` to add single tags for tests
* use `@pytest.mark.exposure('dangerous')` to mark single tests as safe/careful/dangerous
* use `@pytest.mark.roles('domaincontroller_master','domaincontroller_backup')` and/or `@pytest.mark.roles_not('memberserver')` to exclude certain roles for some tests

Several [fixtures](tests/conftest.py) are available:
* `ucr` for a `function` and `ucs_session` for a `session` scoped instance UCR instance.
* `server_role`, `ldap_base`, `ldap_master` to query those values from UCR.
* `udm`, `selenium`, `lo` to get instances for testing UDM, UMC via Selenium, LDAP connection.
* …

## Using Selenium
Since UCS 4.2-3 tests can use [Selenium](https://www.selenium.dev/) for browser based UMC testing.
1. The test must be implemented in Python.
2. The hash-bang-line shoule be `#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest` when using `pytest`.
3. The hash-bang-line should be `#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium`.

[univention.testing.selenium](univention/testing/selenium/base.py) provides several helper functions.
See [86 selenium](tests/86_selenium/) for examples.

```python
#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest -s -l -v
## desc: Test basic UMC login
## exposure: safe
def test_login(selenium):
    selenium.do_login()
    assert True
```
