#!/bin/sh

rm -f ../modules/univention/management/console/wizards/localization/de.po
rm -f ../modules/univention/management/console/wizards/localization/en.po
rm -f ../modules/univention/management/console/wizards/localization/translation.py
${1}/create_translation.sh ${1} > /dev/null
