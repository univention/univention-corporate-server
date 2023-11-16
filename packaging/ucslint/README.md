# Usage

## Docker image
A docker image is build by GitLab-CI for every UCS release branch:

```
docker run --rm -ti -u "$UID" -v "$PWD:/work" -w /work gitregistry.knut.univention.de/univention/ucs
```

## Locally
You can run `ucslint` locally if the required Debian packages `python3-apt`, `python3-debian`, `python3-flake8` and `python-flake8` are installed:

```
packaging/ucslint/ucslint "$PWD"
```

## Virtualenv
If not you can setup a `virtualenv` environment to install the required Python packages:

```
virtualenv -p /usr/bin/python3 usr
. usr/bin/activate
apt download python3-apt
dpkg -x python3-apt_*.deb .
python3 setup.py install
```

# Override
You can create a per-package `debian/ucslint.overrides` file to disable certain messages:

	# Disable module for all files:
	0000-0
	# Disable module for specific file:
	0000-0: filename
	# Disable module for specific line in file:
	0000-0: filename: 1

The blanks are optional.

Some messages can also be ignored on a line-by-line basis if the test allows that:

	echo "ignore all issues" # ucslint
	echo "ignore specific issue" # ucslint: 0000-0
	echo "ignore specific issues" # ucslint: 0000-0, 0000-1

There must be at least one blank before `ucslint`. It can be followed by a `:`, some blanks, a blank/comma separated list if IDs, and some more blanks before the end of the line:

	\s ucslint [:] \s* <msg-id>([, ]...) \s*

# Advanced
You can run `ucslint` over multiple packages and generate a statistic:

	find -maxdepth 3 -name doc -prune -o -name debian -printf '%h\0' |
		xargs -0 ./packaging/ucslint/ucslint -i 0007-5,0007-6 |
		./packaging/ucslint/ucslint-sort-output.py -g -s |
		tee ucslint.txt
