= Usage =

== Docker image ==

A docker image is build by GitLab-CI for every UCS release branch:

```
docker run -v $PWD:/work -w /work registry.knut.univention.de/ucslint:444
```

== Locally ==

You can run `ucslint` locally if the required Debian packages `python3-apt`, `python3-debian`, `python3-flake8` and `python-flake8` are installed:

```
packaging/ucslint/ucslint $PWD
```

== Virtualenv ==

If not you can setup a `virtualenv` environemtn to install the required Python packages:

```
virtualenv -p /usr/bin/python3 usr
. usr/bin/activate
apt download python3-apt
dpkg -x python3-apt_*.deb .
python3 setup.py install
```
