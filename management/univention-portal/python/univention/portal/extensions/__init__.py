#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
"""
This directory is for any extension the portal may need (e.g. cache classes that are then referenced in the portals.json).
Just put your files into this directory and they will be imported.
But in order to make the portal aware of it, you need to use the metaclass
univention.portal.Plugin
As we use this directory, too, you may want to prefix your filename with your project name.
Class names should be globally unique. Otherwise it is undefined which one the portal will pick.
"""
