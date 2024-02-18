# -*- coding: utf-8 -*-
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Example for |UDM| syntax."""

from univention.admin.syntax import select


class ExampleSyntax(select):
    """This is an example for a syntax having 3 values."""

    choices = [
        ('value1', 'This item selects value 1'),
        ('value2', 'This item selects value 2'),
        ('value3', 'This item selects value 3'),
    ]
