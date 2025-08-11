#!/usr/bin/python3
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from argparse import Namespace

import pytest


def test_HTTError(umc):
    _resp = Namespace(**{'getheader': lambda a, b: b})  # noqa: PIE804
    req = umc.Request('GET', '/')
    for code, Error in umc.HTTPError.codes.items():
        resp = umc.Response(code, 'reason', 'no body', {}, _resp)
        with pytest.raises(Error):
            raise umc.HTTPError(req, resp, 'theHostname')
