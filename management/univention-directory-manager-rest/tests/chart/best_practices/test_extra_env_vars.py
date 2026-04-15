# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from univention.testing.helm.best_practice.extra_env_vars import ExtraEnvVars
from univention.testing.helm.utils import apply_mapping


class TestExtraEnvVars(ExtraEnvVars):
    def adjust_values(self, values: dict):
        mapping = {
            "udmRestApi.extraEnvVars": "extraEnvVars",
            "ldapUpdateUniventionObjectIdentifier.extraEnvVars": "extraEnvVars",
            "blocklistCleanup.extraEnvVars": "extraEnvVars",
            "waitForDependency.extraEnvVars": "extraEnvVars",
        }
        apply_mapping(values, mapping, copy=True)
        values.pop("extraEnvVars", {})
        return values
