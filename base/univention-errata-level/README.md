Versioning
==========
This is the dummy package to be shipped with a UCS minor release.

For errata it will be created on-the-fly by `repo-ng/errata.py`.
As such the version number in [debian/changelog](debian/changelog) must be below "$MAJOR.$MINOR.$PATCH-1"!

Do **not** bump the first number of the package version number on each minor
release, as this will break the above schema!

Instead, do **not** change `debian/changelog` but force import the package into repo-ng for the new releases:

```
repo_admin.py -G git@git.knut.univention.de:univention/ucs.git -p univention-errata-level -b $BRANCH -P base/univention-errata-level -r $UCS_VERSION --force
```

Maintained
==========
Until UCS-4 maintained packages were in a separate repository.
From UCS-5 on the maintained packages are listed in [maintained-packages.txt](maintained-packages.txt).
This is a cleaned-up copy from <file://omar/var/univention/buildsystem2/cd-contents/ucs_${VERSION}_amd64.maintained> with the following removed:
- `*-dbg` old style debug symbols
- `*-dbgsym` new style debug symbols
- `*-di` Debian Installer packages
- `*-udeb` micro Debian package for Installer

The file is shipped in `/usr/share/univention-errata-level/`.
It is evaluated by [univention-list-installed-unmaintained-packages](../base/univention-updater/) from `univention-updater`.
