#!/bin/sh
set -e -u

USER='Administrator'
PASS='univention'

umc-command -U "$USER" -P "$PASS" -r updater/updates/get
umc-command -U "$USER" -P "$PASS" -r updater/poll
umc-command -U "$USER" -P "$PASS" -r updater/updates/query
umc-command -U "$USER" -P "$PASS" -r updater/updates/serial
umc-command -U "$USER" -P "$PASS" -r updater/updates/available
umc-command -U "$USER" -P "$PASS" -r updater/updates/check
umc-command -U "$USER" -P "$PASS" -r updater/maintenance_information

umc-command -U "$USER" -P "$PASS" -r updater/installer/execute -o job=release
#DESTRUCTIVE# umc-command -U "$USER" -P "$PASS" -r updater/installer/reboot
umc-command -U "$USER" -P "$PASS" -r updater/installer/running
umc-command -U "$USER" -P "$PASS" -r updater/installer/logfile -o job=
umc-command -U "$USER" -P "$PASS" -r updater/installer/status -o job=release
umc-command -U "$USER" -P "$PASS" -r updater/hooks/call -e -o '{"hooks": ["updater_prohibit_update"]}'
