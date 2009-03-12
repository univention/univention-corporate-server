#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  reads the internal configuration
#
# Copyright (C) 2004-2009 Univention GmbH
#
# http://www.univention.de/
# 
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import sys, codecs, string, os, ConfigParser, cPickle, types, random, traceback


def fixup(s):
    # add proper padding to a base64 string
    n = len(s) & 3
    if n:
        s = s + "="*(4-n)
    return s

configfile='/etc/univention/connector/internal.cfg'
if not os.path.exists(configfile):
    print "ERROR: Config-File not found, maybe connector was never started"
config = ConfigParser.ConfigParser()
config.readfp(open(configfile))

for section in config.sections():
    print "SECTION: %s" % section
    for name, value in config.items(section):
        if section == "AD GUID":
            print " --%s: %s" % (name,value)
            print " --%s: %s" % (fixup(name).decode('base64'),fixup(value).decode('base64'))
        else:
            print " -- %50s : %s" % (name,value)
