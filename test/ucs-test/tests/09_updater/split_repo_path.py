#!/usr/bin/python
"""
Split repository path `$mm/$part/($mmp|component/$comp)/$arch` into atoms `($mmp|$mm--$comp,$part,$arch)`
"""
from __future__ import print_function
from os.path import relpath
from sys import argv, exit

repodir, path = argv[1:]
args = relpath(path, repodir).split("/")
if args[0] == "dists":  # dists/$suite/$section
    exit(0)
if args[2] == "component":  # $mm/$part/component/$comp/$arch
    version, part, arch = ("%s--%s/%s" % (args[0], args[2], args[3]), args[1], args[4])
else:  # $mm/$part/$mmp/$arch
    version, part, arch = args[2:5]
print(" ".join((version, part, arch)))
