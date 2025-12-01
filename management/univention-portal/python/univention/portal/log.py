#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import sys
import time


# from univention.logging import StructuredFormatter


class ShortNameFormatter(logging.Formatter):
    shorten = "univention.portal"
    converter = time.gmtime

    def format(self, record):
        record.short_name = record.name
        if record.short_name.startswith("%s." % self.shorten):
            record.short_name = record.short_name[len(self.shorten) + 1:]
        return super().format(record)


def setup_logger(logfile="/var/log/univention/portal.log", stream=True):
    logger = logging.getLogger("univention.portal")

    if logfile is None and not stream:
        logger.addHandler(logging.NullHandler())

        return

    # log_format = '{asctime} {levelname:>8.8} [{request_id:>10.10}] {message}\t| {logfmt}'
    log_format = '{asctime} {levelname:>8.8} [         -] {message}'
    log_format_time = "%Y-%m-%dT%H:%M:%S.000000%z"
    formatter = ShortNameFormatter(log_format, log_format_time, style='{')
    # formatter = StructuredFormatter(with_date_prefix=True)

    logger.setLevel(logging.DEBUG)

    if logfile is not None:
        handler = logging.FileHandler(logfile)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if stream:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def get_logger(name):
    logger = logging.getLogger("univention.portal")
    logger = logger.getChild(name)
    return logger
