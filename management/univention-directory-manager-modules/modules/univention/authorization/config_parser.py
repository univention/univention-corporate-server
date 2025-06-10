#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import yaml

from univention.authorization.guardian_management_client import (
    expand_condition, expand_permission, expand_role, expand_string, implode_string,
)


class AuthorizationConfig:
    """
    A YAML based configuration format for Guardian.

    This intermediate layer allows to de-duplicate data while Guardian dosen't offer capability bundles, permission bundles, and multiple role to capability assignments, etc.
    """

    def __init__(self, filename):
        self.filename = filename
        self.conditions = {}  # named reusable conditions
        self.permission_sets = {}  # named permission bundles (emulated as not actually implemented in Guardian)
        self.capabilities = {}  # raw capabilities suitable for re-use/reference, suitable as API for customers
        self.capability_bundles = {}  # re-useable capability bundles realizing one specific use case
        self.role_capability_mapping = {}

    def parse(self):
        with open(self.filename) as fd:
            data = yaml.safe_load(fd)
        self.conditions = data['conditions']
        self.permission_sets = data['permission-sets']
        self.capabilities = {f'{ns}:{cap_name}': cap for ns, caps in data['capabilities'].items() for cap_name, cap in caps.items()}
        self.capability_bundles = {f'{ns}:{cap_name}': cap for ns, caps in data['capability-bundles'].items() for cap_name, cap in caps.items()}
        self.role_capability_mapping = {f'{ns}:{cap_name}': cap for ns, caps in data['role-capability-mapping'].items() for cap_name, cap in caps.items()}

    def compose(self):
        return {
            'conditions': self.conditions,
            'permission-sets': self.permission_sets,
            'capabilities': self.capabilities,
            'capability-bundles': self.capability_bundles,
            'role-capability-mapping': self.role_capability_mapping,
        }

    def create(self, client):
        self.client = client
        for role_string, role in self.role_capability_mapping.items():
            app_name, namespace_name, role_name = expand_string(role_string)
            self.client.create_role(app_name, namespace_name, role_name, role.get('displayname', ''))

            for bundle in role.get('capability-bundles', []):
                self.create_capability_bundle(role_string, bundle)
            for capability in role.get('capabilities', []):
                self.create_capability(role_string, capability)
            self.create_permission(role_string, role.get('permissions', []))

    def create_permission(self, role_string, permissions):
        # permissions can't be granted in Guardian, so we need a capability for it
        if not permissions:
            return

        role_name = expand_string(role_string)[2]
        capability = {'grants-permissions': permissions}
        self._create_capability_from_obj(role_string, capability, f"{role_name}-capability-permissions")

    def create_capability_bundle(self, role_string, bundle_name):
        # there are no capability bundles in Guardian, so we create a new capability for each capability in the bundle
        for cap_name in self.capability_bundles[bundle_name]:
            self.create_capability(role_string, cap_name)

    def create_capability(self, role_string, capability_string):
        capability = self.capabilities[capability_string]

        capability_name = expand_string(capability_string)[2]
        role_name = expand_string(role_string)[2]

        self._create_capability_from_obj(role_string, capability, f"{role_name}-capability-{capability_name}")

    def _create_capability_from_obj(self, role_string, capability, capability_string):
        conditions = capability.get('conditions', {})
        relation = next(iter(conditions), 'AND')
        permissions = list(self.resolve_permissions(capability['grants-permissions']))

        self.client.create_role_capability_mapping(
            *expand_string(permissions[0])[:2],
            capability_string,
            capability.get('displayname', ''),
            expand_role(*expand_string(role_string)),
            [expand_permission(*expand_string(perm)) for perm in permissions],
            conditions=[
                expand_condition(*cd)
                for cond in conditions.get(relation, [])
                for cd in self.resolve_conditions(cond)
            ],
            relation=relation,
        )

    def resolve_conditions(self, condition_name):
        for cond, params in self.conditions[condition_name].items():
            yield cond, [{'name': name, 'value': value} for name, value in (params or {}).items()]

    def resolve_permissions(self, permission_names):
        for permission_name in permission_names:
            for perm in self.permission_sets[permission_name]:
                app_name, namespace_name, permission_name = expand_string(perm)
                # TODO: sanitization here?
                yield implode_string(app_name, self._sanitize_module_name(namespace_name), self._sanitize_property_name(permission_name))

    def _sanitize_module_name(self, module_name):
        return module_name.replace('/', '-')

    def _sanitize_property_name(self, property_name):
        return property_name.lower()


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    args = parser.parse_args()

    conf = AuthorizationConfig(args.config)
    conf.parse()
    print(json.dumps(conf.__dict__, indent=4))
