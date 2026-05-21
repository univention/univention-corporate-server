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
They are stored in [dists/ucs500/](http://updates.software-univention.de/dists/ucs500/) respective [download/univention-update-checks/](http://updates.software-univention.de/download/univention-update-checks/).

Sometimes the scripts need to be modified **after** a release, for example to block the update because of some late issues.
1. In that case the code for the modified script should be committed in git first, so the change is documented.
2. It is then recommended to import and build the package using `repo-ng`, after which the scripts can be extract from the binary package by using `dpkg -x univention-updaeter_${version}_all.deb /some/temporary/directory/`.
3. The scripts **must** be signed **manually** using `repo-ng-sign-release-file` from `repo-ng` with the PGP key **corresponding** to the UCS release.
    ```sh
    repo-ng-sign-release-file -i pre-update-checks-5.2-0 -o pre-update-checks-5.2-0.gpg -k 92E57AE68A7988BD9651C222C882B6F1F7229D9A -p /etc/archive-keys/ucs5.3.txt
    ```
4. Afterwards the script and signature files must be copied **manually** to the locations mentioned above.
5.  In case prior changes have been made, the script files under `test_mirror/ftp` may be write protected with `chattr +i` (not the signature files).
    If so, that needs to adjusted temporarily.
    After the changes have been mae, it is recommended to protect the script files under `test_mirror/ftp` (not the signature files) against getting overwritten
    during the nightly run of `jenkins:PublishUCS5Testing`. This can be done by running `chattr +i` on the modified files.
    Also make sure that the signature files are writeable for the `buildgroup` (otherwise the nightly `repo-ng-sign-release-file` will fail).
6. Test it thoroughly before updating our **external** mirror:
    ```sh
    curl -OOf https://updates.knut.univention.de/download/univention-update-checks/pre-update-checks-5.2-0{.gpg,}
    apt-key verify pre-update-checks-5.2-0{.gpg,}
    bash pre-update-checks-5.2-0
    ```
7. Update the external mirror:
    ```sh
    sudo update_mirror.sh ftp/download/univention-update-checks
    ```
