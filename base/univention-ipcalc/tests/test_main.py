#!/usr/bin/env pytest-3
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-License-Identifier: AGPL-3.0
# Copyright 2021-2022 Univention GmbH

import pytest

pytest.importorskip("ipaddress")

from univention.ipcalc.__main__ import main, parse_options  # noqa: E402


@pytest.mark.parametrize("args", [
	"",
	"foo",
	"--ip",
	"--ip foo",
	"--ip 1.2.3.4.5",
	"--ip 1:2:3:4:5:6:7:8:9",
	"--netmask",
	"--output",
	"--output foo",
	"--output all",
	"--calcdns --output network --ip 1.2.3.4 --netmask",
	"--calcdns --output network --ip 1.2.3.4 --netmask foo",
	"--calcdns --output network --ip 1.2.3.4 --netmask 33",
	"--calcdns --output network --ip 1:2::4 --netmask",
	"--calcdns --output network --ip 1:2::4 --netmask 129",
	"--output network --ip 1.2.3.4 --netmask 16",
	"--calcdns --ip 1.2.3.4 --netmask 16",
	"--calcdns --output network --netmask 16",
	"--calcdns --output network --ip 1.2.3.4",
])
def test_invalid(args):
	with pytest.raises(SystemExit) as exc_info:
		parse_options(args.split())

	assert exc_info.value.code


def test_help(capsys):
	with pytest.raises(SystemExit) as exc_info:
		parse_options(["--help"])

	assert exc_info.value.code == 0

	out, err = capsys.readouterr()
	assert out
	assert err == ""


@pytest.mark.parametrize("ip,mask,net", [
	("1.2.3.4", "16", "1.2"),
	("1:2:3::4", "64", "0001:0002:0003:0000"),
])
def test_main(ip, mask, net, capsys):
	main(["--calcdns", "--ip", ip, "--netmask", mask, "--output", "network"])
	out, err = capsys.readouterr()
	assert out == net + "\n"
	assert err == ""
