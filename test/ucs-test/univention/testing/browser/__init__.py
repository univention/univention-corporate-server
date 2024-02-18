# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging


__all__ = ['logger']

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addFilter(logging.Filter('univention.testing.browser'))
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(filename)s:%(lineno)d (%(funcName)s)- %(message)s'))

root_logger.addHandler(ch)

logger = logging.getLogger('univention.testing.browser.tests')
