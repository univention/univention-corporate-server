# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

import pytest


base_dir = (Path(__file__).parent / "../../").resolve()


@pytest.fixture()
def helm_default_values(request):
    default_values = [
        base_dir / "helm/udm-rest-api/linter_values.yaml",
    ]
    return default_values


@pytest.fixture()
def chart_default_path():
    chart_path = base_dir / "helm/udm-rest-api"
    return chart_path
