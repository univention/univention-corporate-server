#!/usr/share/ucs-test/runner pytest-3 -l -vv
## desc: "Basic udn tests"
## packages:
##  - univention-directory-notifier
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: safe
## bugs: [53355]

import subprocess

import pytest


TRANSLOG_CMD = '/usr/share/univention-directory-notifier/univention-translog'


@pytest.mark.parametrize("cmd", [
	"--verbose",
])
def test_translog_check_fail(cmd, capfd):
	with pytest.raises(subprocess.CalledProcessError) as exc_info:
		subprocess.check_call([TRANSLOG_CMD] + cmd.split())

	assert exc_info.value.returncode


@pytest.mark.parametrize("cmd", [
	"--help",
	"index",
	"lookup 1",
	"stat",
	"ldap 1",
])
def test_translog_check(cmd, capfd):
	subprocess.check_call([TRANSLOG_CMD] + cmd.split())
	stdout, stderr = capfd.readouterr()
	assert stdout > ""
	assert stderr == ""


@pytest.mark.parametrize("cmd", [
	"check",
	"prune 1",
	"-n -l load 1",
	"-n -l import -m 1 -M 1",
])
def test_translog_check_silent(cmd, capfd):
	subprocess.check_call([TRANSLOG_CMD] + cmd.split())
	stdout, stderr = capfd.readouterr()
	assert stdout == ""
	assert stderr == ""
