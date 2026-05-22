Purpose
=======
* explicit release updates
* App Center integration
* higher level tool than `apt`
* possibility to create a *local* mirror

Code layout
===========

* [overview](doc/code.md)
* [status file](doc/status.md)
* [UMC hooks](doc/hooks.md)

Repository layout
=================
* [IPvX](https://updates.software-univention.de/)
* [Local](http://univention-repository.$FQDN/univention-repository/)

* [UCS 2-4](doc/layout4.md)
* [UCS 5](doc/layout5.md)

Check scripts
=============

[script/preup.sh](script/preup.sh) and [script/postup.sh](script/postup.sh) are extracted during announce to the server and signed.
They are downloaded by the previuos updater and executed before / after the release upgrade.
A failure in `preup.sh` will abort the upgrade.

Since UCS-5 the tests should go to [script/check.sh](script/check.sh) instead, which previously lived in `checks/` and duplicated much of the code.
The checks are now only maintained there and `preup.sh` includes that file during package build.

The final `preup.sh` script is created by this command in [debian/rules](debian/rules):

	sed '/^###CHECKS###/r script/check.sh' script/preup.sh >debian/univention-updater/usr/share/univention-updater/preup.sh

* Each check should be in a separate function, whos name starts with `update_check_`.
* Each check should be self-contained.
* The order of execution is not deterministic.

Publishing
----------
The `preup.sh`, `postup.sh` and `check.sh` scripts are **automatically** extracted from the package `univention-updater` by `announce_ucs5_release` from `repo-ng` **only** for the **initial** release.
On the server they are published as:

| File in the repository | Published as |
| ---------------------- | ------------ |
| `script/preup.sh` with `script/check.sh` inserted | `dists/ucs527/preup.sh` |
| `script/postup.sh` | `dists/ucs527/postup.sh` |
| `script/check.sh` | `download/univention-update-checks/pre-update-checks-5.3-0` |

Each file has a detached PGP signature next to it (`*.gpg`), made with the key of the UCS release.
The updater refuses to run a script whose signature does not match.

Sometimes the scripts need to be modified **after** a release, for example to block the update because of some late issues.
For releases which are no longer maintained (status `end-of-life` in `/etc/repo-ng/releases.yaml`) this is done with `announce_update_checks` from `repo-ng` on `omar`.
It generates the files from a UCS clone, signs them, shows a diff, and publishes only the files which changed.
For maintained releases it refuses to run unless `--force` is given.

### Mirrors

The scripts go through three mirrors, always in this order:

| Step | Mirror on `omar` | Internal URL | Public URL |
| ---- | ---------------- | ------------ | ---------- |
| 1. Test | `test_mirror/ftp/` | http://apt.knut.univention.de/ | – |
| 2. Testing | `mirror/testing/` | http://updates-test.knut.univention.de/ | https://updates-test.software-univention.de/ |
| 3. Production | `mirror/ftp/` | http://updates.knut.univention.de/ | https://updates.software-univention.de/ |

There are two ways to fill each mirror:

* `--test-mirror`, `--testing` and `--ftp` generate the files from the UCS clone and sign them.
* `--copy-from-test-mirror-to-testing` and `--copy-from-test-mirror-to-ftp` copy the files already signed in the test mirror.

The recommended way is to generate only the test mirror and copy from there, so testing and production receive **exactly** the files tested before.
This is what the following steps do.

### 1. Commit the change

Commit and push the modified scripts to the release branch, e.g. `5.3-0`, so the change is documented and reviewed.

### 2. Prepare a UCS clone on omar

Log in to `omar` and start a `tmux` or `screen` session; the tool refuses to run without one.
Only the updater scripts are needed, so a sparse checkout is enough:

```sh
git clone --no-checkout --depth 1 --branch 5.3-0 git@git.knut.univention.de:univention/dev/ucs.git ucs-updater-5.3-0
cd ucs-updater-5.3-0
git config core.sparseCheckout true
echo base/univention-updater/script/ >.git/info/sparse-checkout
git checkout 5.3-0
cd ..
```

For a later change just run `git -C ucs-updater-5.3-0 pull`.
The tool checks that the clone is on the release branch, clean and up to date.

### 3. Publish to the test mirror

```sh
announce_update_checks -r 5.3-0 --ucs-dir ./ucs-updater-5.3-0 --test-mirror
```

The tool shows the diff of every changed script and asks before signing and installing it.
The PGP key and its passphrase file are taken from `releases.yaml`.
Unchanged scripts are skipped, unless their signature is missing or invalid; then they are signed again.

Test the new scripts on a UCS system of that release:

```sh
curl -OOf http://apt.knut.univention.de/download/univention-update-checks/pre-update-checks-5.3-0{.gpg,}
gpgv --verbose --keyring /etc/apt/trusted.gpg.d/univention-archive-key-ucs-53x.gpg pre-update-checks-5.3-0{.gpg,}
bash pre-update-checks-5.3-0
```

### 4. Publish to testing

```sh
announce_update_checks -r 5.3-0 --copy-from-test-mirror-to-testing
```

This verifies the signatures in the test mirror and copies the files to `mirror/testing/`.
While doing so the mirror is locked with `ucr set update/mirror/disabled=…`, so no other job synchronizes it in between.
Test again from http://updates-test.knut.univention.de/ when the tool asks for it.
Afterwards the tool runs `update_mirror.sh` for the changed files, first as dry run with `--debug --verbose`, then for real after confirmation.
Finally it checks that https://updates-test.software-univention.de/ serves the new files.

### 5. Publish to production

```sh
announce_update_checks -r 5.3-0 --copy-from-test-mirror-to-ftp
```

The same as step 4, but for `mirror/ftp/` and https://updates.software-univention.de/.

### Tips

* `-n` (`--dry-run`) shows what would be done without changing anything.
* `--testing` and `--ftp` work like `--test-mirror`, but generate and sign the files directly for that mirror.
  Use them only if the test mirror can not be used, as the files then skip the tests of step 3.
* If a step fails, fix the cause and continue from that step with `-s STEP`, e.g. `-s update_mirror`. `--help` lists the steps.
* The nightly Jenkins job `PublishUCS5Testing` overwrites the scripts in `test_mirror/ftp/` and signs them again.
  A script modified after the release is protected against this with `chattr +i` on the script file only, not on its `.gpg` file.
  The `.gpg` files must stay writable for the group `buildgroup`, otherwise the nightly `repo-ng-sign-release-file` fails.
  The tool detects protected files and shows which ones must be unlocked.
  On `omar` `chattr` can not be run as `sudo chattr …`, so become root first with `sudo bash`:
  ```sh
  sudo bash
  chattr -i /var/univention/buildsystem2/test_mirror/ftp/dists/ucs527/postup.sh  # unlock before publishing
  chattr +i /var/univention/buildsystem2/test_mirror/ftp/dists/ucs527/postup.sh  # protect again afterwards
  ```
* A directory which does not yet exist on the download server, e.g. `download/univention-update-checks/` on testing, is synchronized as a whole, as `rsync` can not create it for a single file.
* Before overwriting anything the tool saves the old files to `~/backup-update-checks/`.
