#!/usr/bin/python3
#
# Univention S4 Connector
#  reads the internal configuration
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import base64
import configparser
import os


def fixup(s):
    # add proper padding to a base64 string
    n = len(s) & 3
    if n:
        s = s + "=" * (4 - n)
    return s


configfile = '/etc/univention/s4connector/s4internal.cfg'
if not os.path.exists(configfile):
    print("ERROR: Config-File not found, maybe connector was never started")
config = configparser.ConfigParser()
config.read_file(open(configfile))

for section in config.sections():
    print(f"SECTION: {section}")
    for name, value in config.items(section):
        if section == "S4 GUID":
            print(f" --{name}: {value}")
            print(" --{}: {}".format(base64.b64decode(fixup(name).encode('ASCII')).decode('ASCII'), base64.b64decode(fixup(value).encode('ASCII')).decode('ASCII')))
        else:
            print(" -- %50s : %s" % (name, value))
