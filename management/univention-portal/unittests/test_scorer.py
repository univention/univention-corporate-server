#!/usr/bin/python3
#
# Univention Portal
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#


def test_import(dynamic_class):
    assert dynamic_class("Scorer")
    assert dynamic_class("DomainScorer")
    assert dynamic_class("PathScorer")


def test_scorer(dynamic_class, mocker):
    request = mocker.Mock()
    scorer = dynamic_class("Scorer")()
    assert scorer.score(request) == 1


def test_domain_scorer_hit(dynamic_class, mocker):
    request = mocker.Mock()
    request.host = "portal.domain.tld"
    scorer = dynamic_class("DomainScorer")("portal.domain.tld")
    assert scorer.score(request) == 10


def test_domain_scorer_miss(dynamic_class, mocker):
    request = mocker.Mock()
    request.host = "portal2.domain.tld"
    scorer = dynamic_class("DomainScorer")("portal.domain.tld")
    assert scorer.score(request) == 0


def test_path_scorer_hit(dynamic_class, mocker):
    request = mocker.Mock()
    request.path = "/portal2"
    scorer = dynamic_class("PathScorer")("/portal2")
    assert scorer.score(request) == 10


def test_path_scorer_miss(dynamic_class, mocker):
    request = mocker.Mock()
    request.path = "/portal"
    scorer = dynamic_class("PathScorer")("/portal2")
    assert scorer.score(request) == 0
