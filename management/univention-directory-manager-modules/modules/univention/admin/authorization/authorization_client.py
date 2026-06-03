#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Cerbos authorization adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cerbos.sdk.client import CerbosClient
from cerbos.sdk.model import Principal, Resource, ResourceList


if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = ('CerbosAuthorizationClient', 'Principal', 'Resource')


@dataclass(frozen=True)
class CerbosCheckResult:
    """Allowed actions for one checked UDM target."""

    target_id: str
    actions: frozenset[str]


class CerbosAuthorizationClient:
    """Thin adapter around the Cerbos Python SDK."""

    def __init__(self, endpoint: str = 'http://localhost:3592', *, tls_verify: bool = True):
        self.endpoint = endpoint
        self.tls_verify = tls_verify
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = CerbosClient(self.endpoint, tls_verify=self.tls_verify)
        return self._client

    def check_actions(self, principal: Principal, resource: Resource, actions: Iterable[str]) -> list[CerbosCheckResult]:
        """Check ``actions`` for ``principal`` on each UDM resource."""
        actions = sorted(set(actions))
        if not actions:
            return CerbosCheckResult(resource.id, frozenset())

        batch_resources = ResourceList()
        batch_resources.add(resource, actions)

        response = self.client.check_resources(principal=principal, resources=batch_resources)
        return CerbosCheckResult(resource.id, frozenset(self._allowed_actions(response, resource, actions)))

    def check_actions_bulk(self, principal: Principal, resources: Iterable[Resource], actions: Iterable[str]) -> list[CerbosCheckResult]:
        """Check ``actions`` for ``principal`` on each UDM resource."""
        actions = sorted(set(actions))
        resources = list(resources)
        if not resources or not actions:
            return [CerbosCheckResult(resource.id, frozenset()) for resource in resources]

        batch_resources = ResourceList()
        for resource in resources:
            batch_resources.add(resource, actions)

        response = self.client.check_resources(principal=principal, resources=batch_resources)
        return [
            CerbosCheckResult(resource.id, frozenset(self._allowed_actions(response, resource, actions)))
            for resource in resources
        ]

    def _allowed_actions(self, response: Any, resource: Resource, actions: list[str]) -> set[str]:
        response.raise_if_failed()  # TODO: handle
        resource_res = response.get_resource(resource.id)
        allowed: set[str] = set()
        for action in actions:
            if resource_res.is_allowed(action):
                allowed.add(action)
        return allowed
