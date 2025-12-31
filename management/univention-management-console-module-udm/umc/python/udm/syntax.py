#!/usr/bin/python3
#
# Univention Management Console
"""module: manages UDM modules"""
#
# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


def widget(syntax, udm_property):
    """
    Returns a widget description as a dictionary

    .. deprecated:: 5.0-1
        remove in 5.0-2
    """
    return syntax.get_widget_options(udm_property)
