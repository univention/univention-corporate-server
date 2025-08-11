# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from subprocess import call


def postinst(baseConfig, changes):
    theme = changes.get("bootsplash/theme", False)
    try:
        _old, new = theme
    except (TypeError, ValueError):
        pass
    else:
        if new:
            call(("plymouth-set-default-theme", "--rebuild-initrd", new))
