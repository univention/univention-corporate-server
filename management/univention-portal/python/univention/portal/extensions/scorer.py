#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from univention.portal import Plugin


class Scorer(metaclass=Plugin):
    """
    Base class for portal scoring

    The idea is that when multiple portals are configured, their scorers
    decide which portal is to be used for a request.

    `score`: Gets a Tornado request and returns a number. The highest score wins.
    """

    def __init__(self, score=1):
        self._score = score

    def score(self, request):
        return self._score


class DomainScorer(Scorer):
    """
    Specialized Scorer that reponds if the request went against the configured domain.
    For this to work you have to make your portal system available under different domains.

    domain:
            Name of the domain, e.g. "myportal2.fqdn.com"
    """

    def __init__(self, domain, score=10, fallback_score=0):
        self._score = score
        self._fallback_score = fallback_score
        self.domain = domain

    def score(self, request):
        if request.host == self.domain:
            return self._score
        return self._fallback_score


class PathScorer(Scorer):
    """
    Specialized Scorer that reponds if the request went against the configured path.
    For this to work you have to make your portal available under different paths, e.g.
    "/univention/portal" and "/univention/portal2".

    path:
            The path. Does not have to match exactly, but the request's path needs to start
            with this value, e.g. "/portal2".
    """

    def __init__(self, path, score=10, fallback_score=0):
        self._score = score
        self._fallback_score = fallback_score
        self.path = path

    def score(self, request):
        request_path = "/{}".format(request.path.lstrip("/"))
        if request_path.startswith(self.path):
            return self._score
        return self._fallback_score
