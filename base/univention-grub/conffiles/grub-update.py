#!/usr/bin/python3
#
# Univention Grub
#  baseconfig module for the grub update
#
# SPDX-FileCopyrightText: 2007-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import shutil


def postinst(configRegistry, changes):
    light_theme = configRegistry.get('bootsplash/theme') in ['ucs-light', 'ucs-appliance-light']
    backgroundimage_target = '/boot/grub/uniboot.png'
    backgroundimage_source = os.path.join('/usr/share/univention-grub/', 'light-background.png' if light_theme else 'dark-background.png')
    if configRegistry.get('grub/backgroundimage') == backgroundimage_target:
        try:
            os.makedirs(os.path.dirname(backgroundimage_target), mode=0o755)
        except OSError:
            pass
        shutil.copy(backgroundimage_source, backgroundimage_target)
    os.system('update-grub')  # noqa: S605
