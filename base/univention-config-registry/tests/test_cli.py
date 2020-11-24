#!/usr/bin/python3
"""
Run (uninstalled) univention.config_registry to make sure all commands work
"""
import pytest

from univention.config_registry import main  # noqa E402


@pytest.mark.parametrize(
    "args",
    [
        ("-?",),
        ("-h",),
        ("--help",),
        ("-v",),
        ("--version",),
        ("set", "key?value"),
        ("set", "key=value"),
        ("set", "--force", "key?value"),
        ("set", "--force", "key=value"),
        ("set", "--schedule", "key?value"),
        ("set", "--schedule", "key=value"),
        ("set", "--ldap-policy", "key?value"),
        ("set", "--ldap-policy", "key=value"),
        ("get", "key"),
        ("unset", "key"),
        ("unset", "--force", "key"),
        ("unset", "--schedule", "key"),
        ("unset", "--ldap-policy", "key"),
        ("dump",),
        ("--shell", "dump"),
        ("--keys-only", "dump"),
        ("search",),
        ("search", "hostname"),
        ("search", "--key", "hostname"),
        ("search", "--value", "hostname"),
        ("search", "--all", "hostname"),
        ("search", "--category", "system-network", "hostname"),
        ("search", "--brief", "hostname"),
        ("search", "--non-empty", "hostname"),
        ("--shell", "search"),
        ("--shell", "search", "hostname"),
        ("--shell", "search", "--key", "hostname"),
        ("--shell", "search", "--value", "hostname"),
        ("--shell", "search", "--all", "hostname"),
        ("--shell", "search", "--category", "system-network", "hostname"),
        ("--shell", "search", "--brief", "hostname"),
        ("--shell", "search", "--non-empty", "hostname"),
        ("--shell", "search"),
        ("--shell", "search", "hostname"),
        ("--keys-only", "search"),
        ("--keys-only", "search", "hostname"),
        ("--keys-only", "search", "--key", "hostname"),
        ("--keys-only", "search", "--value", "hostname"),
        ("--keys-only", "search", "--all", "hostname"),
        ("--keys-only", "search", "--category", "system-network", "hostname"),
        ("--keys-only", "search", "--brief", "hostname"),
        ("--keys-only", "search", "--non-empty", "hostname"),
        ("info", "hostname"),
        ("shell",),
        ("shell", "hostname"),
        # ("commit",),
        ("commit", "/etc/hostname"),
        ("filter",),  # </dev/null
        # ("register", "..."),
        # ("unregister", "..."),
        ("update",),
    ],
)
def test_cmd(args):
    with pytest.raises(SystemExit) as exc_info:
        main(list(args))

    assert exc_info.value.code == 0
