#!/usr/bin/python3
#
# Univention Portal
#
# Copyright 2020-2022 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
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
