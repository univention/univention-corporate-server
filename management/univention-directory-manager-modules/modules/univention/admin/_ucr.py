# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Non public UCR instance."""

import univention.config_registry


configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()
