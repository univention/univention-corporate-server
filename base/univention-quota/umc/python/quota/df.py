#!/usr/bin/python3
#
# Univention Management Console
#  quota module: provides size information about a hard drive partition
#
# SPDX-FileCopyrightText: 2006-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""This module provides a similar functionality as the UNIX tool df"""

import os


class DeviceInfo:

    def __init__(self, path):
        self.path = path
        self._statvfs = os.statvfs(self.path)

    def free(self):
        return (self._statvfs.f_bfree * self._statvfs.f_bsize)

    def available(self):
        return (self._statvfs.f_bavail * self._statvfs.f_bsize)

    def size(self):
        return (self._statvfs.f_blocks * self._statvfs.f_bsize)

    def block_size(self):
        return self._statvfs.f_bsize
