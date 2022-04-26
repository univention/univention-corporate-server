# python-keycloak

## Introduction

The `python-keycloak` package is a debian wrapped of the [PyPi package of the same name](https://pypi.org/project/python-keycloak/).

See `docs/source/index.rst` for more details.

## Building

* This package was created using [stdeb](https://pypi.org/project/stdeb/):
  ```
  pip3 install stdeb
  wget https://github.com/marcospereirampj/python-keycloak/archive/refs/tags/0.24.0.tar.gz
  mv 0.24.0.tar.gz python-keycloak-0.24.0.tar.gz
  py2dsc --compat 11 python-keycloak-0.24.0.tar.gz
  [...]
  rm -r bin Pipfile* requirements.txt LICENSE MANIFEST.in
  wrap-and-sort -astf debian/control
  ```
* Checking for available updates: `uscan --no-download --verbose`
* Updating with: `uscan && uupdate ../python-keycloak-*.tar.gz`
