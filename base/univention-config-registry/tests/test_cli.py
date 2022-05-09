#!/usr/bin/python3
"""
Run (uninstalled) univention.config_registry to make sure all commands work
"""
from copy import deepcopy

import pytest

from univention.config_registry import main  # noqa: E402
import univention.config_registry.frontend as ucrfe


@pytest.fixture(autouse=True)
def global_state():
    """Save and restore global state for each test."""
    opt_actions = deepcopy(ucrfe.OPT_ACTIONS)
    opt_filters = deepcopy(ucrfe.OPT_FILTERS)
    opt_commands = deepcopy(ucrfe.OPT_COMMANDS)
    yield
    ucrfe.OPT_ACTIONS = opt_actions
    ucrfe.OPT_FILTERS = opt_filters
    ucrfe.OPT_COMMANDS = opt_commands


@pytest.mark.parametrize(
    "args",
    [
        "",
        "-?",
        "-h",
        "--help",
        "-v",
        "--version",
    ])
def test_exit(args, tmpucr):
    with pytest.raises(SystemExit) as exc_info:
        main(args.split() if args else [])

    assert exc_info.value.code == 0


@pytest.mark.parametrize(
    "args",
    [
        "set key?value",
        "set key=value",
        "set --force key?value",
        "set --force key=value",
        "set --forced key=value",
        "set --schedule key?value",
        "set --schedule key=value",
        "set --ldap-policy key?value",
        "set --ldap-policy key=value",
        "get key",
        "--shell get key",
        "unset key",
        "unset --force key",
        "unset --forced key",
        "unset --schedule key",
        "unset --ldap-policy key",
        "dump",
        pytest.param("--shell dump", marks=pytest.mark.xfail(reason="Fails on empty output")),
        "--sort dump",
        "--keys-only dump",
        "search",
        "search hostname",
        "search --key hostname",
        "search --value hostname",
        "search --all hostname",
        pytest.param("search --category system-network hostname", marks=pytest.mark.xfail(reason="Category not defined")),
        "search --brief hostname",
        "search --non-empty hostname",
        "search --verbose hostname",
        "--shell search",
        "--sort search",
        "--keys-only search",
        "info hostname",
        "--sort info hostname",
        "shell",
        "shell hostname",
        # "commit",
        "commit /etc/hostname",
        pytest.param("filter", marks=pytest.mark.skip(reason="Requires input")),
        pytest.param("filter --encode-utf8", marks=pytest.mark.skip(reason="Requires input")),
        pytest.param("filter disallow-execution", marks=pytest.mark.skip(reason="Requires input")),
        pytest.param("register ...", marks=pytest.mark.skip("Requires file")),
        pytest.param("unregister ...", marks=pytest.mark.skip("Requires file")),
        "update",
    ])
def test_cmd(args, tmpucr):
    main(args.split())
