#!/usr/share/ucs-test/runner python3
## desc: check the /etc/rsyslog.conf validity
## tags: [basic, skip_admember]
## roles: [domaincontroller_primary]
## exposure: dangerous
## packages: [rsyslog]
## bugs: [56055]

import subprocess


def test_rsyslog_conf_validity(ucr):
    valid_variable_values = {
        "syslog/cron": None,
        "syslog/daemon": None,
        "syslog/input/relp": "2514",
        "syslog/input/tcp": "10514",
        "syslog/input/udp": "514",
        "syslog/kern": None,
        "syslog/limit/burst": "200",
        "syslog/limit/interval": "5",
        "syslog/lpr": None,
        "syslog/mail": None,
        "syslog/mail/mirrorto/syslog": "no",
        "syslog/maxmessagesize": None,
        "syslog/remote": None,
        "syslog/remote/fallback": None,
        "syslog/syslog": None,
        "syslog/syslog/avoid_duplicate_messages": None,
        "syslog/syslog/selector": None,
        "syslog/template/default": None,
    }
    ucr.handler_set([f"{k}={v}" for k, v in valid_variable_values.items() if v is not None])
    ucr.handler_unset([k for k, v in valid_variable_values.items() if v is None])

    subprocess.run(["ucr", "commit"], check=True)
    subprocess.run(["rsyslogd", "-N", "1", "-f", "/etc/rsyslog.conf"], check=True)
