#!/bin/sh
# Run (uninstalled) univention.config_registry to make sure all commands work
PY="python2.7" UCR="${0%/*}/../python/univention/config_registry.py"
exec >/dev/null
set -e -x
"$PY" "$UCR" -\?
"$PY" "$UCR" -h
"$PY" "$UCR" --help
"$PY" "$UCR" -v
"$PY" "$UCR" --version
"$PY" "$UCR" set key?value
"$PY" "$UCR" set key=value
"$PY" "$UCR" set --force key?value
"$PY" "$UCR" set --force key=value
"$PY" "$UCR" set --schedule key?value
"$PY" "$UCR" set --schedule key=value
"$PY" "$UCR" set --ldap-policy key?value
"$PY" "$UCR" set --ldap-policy key=value
"$PY" "$UCR" get key
"$PY" "$UCR" unset key
"$PY" "$UCR" unset --force key
"$PY" "$UCR" unset --schedule key
"$PY" "$UCR" unset --ldap-policy key
"$PY" "$UCR" dump
"$PY" "$UCR" --shell dump
"$PY" "$UCR" --keys-only dump
"$PY" "$UCR" search
"$PY" "$UCR" search hostname
"$PY" "$UCR" search --key hostname
"$PY" "$UCR" search --value hostname
"$PY" "$UCR" search --all hostname
"$PY" "$UCR" search --category system-network hostname
"$PY" "$UCR" search --brief hostname
"$PY" "$UCR" search --non-empty hostname
"$PY" "$UCR" --shell search
"$PY" "$UCR" --shell search hostname
"$PY" "$UCR" --shell search --key hostname
"$PY" "$UCR" --shell search --value hostname
"$PY" "$UCR" --shell search --all hostname
"$PY" "$UCR" --shell search --category system-network hostname
"$PY" "$UCR" --shell search --brief hostname
"$PY" "$UCR" --shell search --non-empty hostname
"$PY" "$UCR" --shell search
"$PY" "$UCR" --shell search hostname
"$PY" "$UCR" --keys-only search
"$PY" "$UCR" --keys-only search hostname
"$PY" "$UCR" --keys-only search --key hostname
"$PY" "$UCR" --keys-only search --value hostname
"$PY" "$UCR" --keys-only search --all hostname
"$PY" "$UCR" --keys-only search --category system-network hostname
"$PY" "$UCR" --keys-only search --brief hostname
"$PY" "$UCR" --keys-only search --non-empty hostname
"$PY" "$UCR" info hostname
"$PY" "$UCR" shell
"$PY" "$UCR" shell hostname
#"$PY" "$UCR" commit
"$PY" "$UCR" commit /etc/hostname
"$PY" "$UCR" filter </dev/null
#"$PY" "$UCR" register ...
#"$PY" "$UCR" unregister ...
"$PY" "$UCR" update
