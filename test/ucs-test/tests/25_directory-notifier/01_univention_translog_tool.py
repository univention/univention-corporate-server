#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: "Basic udn tests"
## packages:
##  - univention-directory-notifier
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: safe

import subprocess

import pytest


TRANSLOG_CMD = '/usr/share/univention-directory-notifier/univention-translog'


def test_translog_check():
	subprocess.check_call([TRANSLOG_CMD, 'check'], stderr=subprocess.STDOUT)


def test_translog_index():
	subprocess.check_call([TRANSLOG_CMD, 'index'], stderr=subprocess.STDOUT)


def test_translog_lookup():
	subprocess.check_call([TRANSLOG_CMD, 'lookup', '1'], stderr=subprocess.STDOUT)


def test_translog_stat():
	subprocess.check_call([TRANSLOG_CMD, 'stat'], stderr=subprocess.STDOUT)


def test_translog_prune():
	subprocess.check_call([TRANSLOG_CMD, 'prune', '1'], stderr=subprocess.STDOUT)


def test_translog_ldap():
	subprocess.check_call([TRANSLOG_CMD, 'ldap', '1'], stderr=subprocess.STDOUT)
