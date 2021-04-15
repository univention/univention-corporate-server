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
