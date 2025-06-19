#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
A domain specific language (DSL) for UDM access rules
inspired by LDAP ACLs
realized with extended BNF grammar and a LALR (Look-Ahead Left <- Right) Parser.
"""

import copy
import hashlib
import io
import logging

import yaml
from lark import Lark, Transformer

from univention.authorization.config_parser import AuthorizationConfig


try:
    import univention.admin.modules
    from univention.config_registry import ucr
    univention.admin.modules.update()
    all_modules = list(univention.admin.modules.modules)
except ImportError:
    ucr = {
        'ldap/base': 'dc=example,dc=org',
    }
    all_modules = ('users/user', 'groups/group', 'computers/linux')


log = logging.getLogger('ACL').getChild(__name__)


UDM_DSL_GRAMMAR = r"""
start: statement+

statement: named_condition | access_block

named_condition: "named-condition" QUOTED_STRING condition_line param_line?

condition_line: "condition=" QUOTED_STRING
param_line: "parameters" kvpair+

access_block: "access" by_line+ to_line*

BY_KEY: "role" | "description"
by_line: "by" by_kvpair+
by_kvpair: NAME "=" value -> by_kvpair

TO_KEY: "objecttype" | "if" | "position" | "scope" | "name" | "description"
to_line: "to" to_kvlistpair+ grant_line*
to_kvlistpair: NAME "=" valuelist -> to_kvlistpair

GRANT_KEY: "actions" | "properties" | "permission" | "values"
grant_line: "grant" grant_kvlistpair+
grant_kvlistpair: NAME "=" valuelist -> grant_kvlistpair

kvpair: NAME "=" value
value: QUOTED_STRING | NAME

valuelist: QUOTED_STRING | list | NAME

list: "[" [QUOTED_STRING ("," QUOTED_STRING)*] "]"

NAME: /[a-zA-Z_][\w\/\-]*/
%import common.ESCAPED_STRING -> QUOTED_STRING
%import common.WS
%ignore WS
%ignore /#.*/  // Kommentare
"""

# FIXME: can't reference keys due to NAME
"""
by_kvpair: BY_KEY "=" value -> by_kvpair
to_kvlistpair: TO_KEY "=" valuelist -> to_kvlistpair
grant_kvlistpair: GRANT_KEY "=" valuelist -> grant_kvlistpair
"""


class DSLSyntaxError(SyntaxError):
    pass


class _DSLTransformer(Transformer):

    def start(self, items):
        data = {'conditions': [], 'rules': []}
        for all_items in items:
            for item in all_items:
                if item['type'] == 'named-condition':
                    data['conditions'].append(item)
                elif item['type'] == 'access':
                    data['rules'].append(item)
                else:
                    raise DSLSyntaxError("unknown type", ("", 0, 0, item['type']))
                item.pop('type')

        return data

    def statement(self, items):
        return items

    def named_condition(self, items):
        name = items[0]
        cond = items[1]
        parameters = items[2] if len(items) > 2 else {}
        return {
            "type": "named-condition",
            "name": name,
            "condition": cond,
            "parameters": parameters,
        }

    def condition_line(self, items):
        return items[0]

    def param_line(self, items):
        return dict(items)

    def access_block(self, items):
        by_blocks = []
        to_blocks = []
        meta = {}
        for item in items:
            if item.get("type") == "by":
                by_blocks.append(item['by'])
                meta = item['meta']
            elif item['type'] == 'to':
                to_blocks.append(item['to'])
            else:
                raise DSLSyntaxError("unknown type", ("", 0, 0, item['type']))

        return {
            "type": "access",
            "by": by_blocks,
            "to": to_blocks,
            **meta,
        }

    def by_line(self, items):
        meta = dict(items)
        by = {'role': meta.pop('role'), 'context': meta.pop('context', None)}
        assert not set(meta) - {'description'}, set(meta)
        assert not set(by) - {'role', 'context'}, set(by)

        return {
            "type": "by",
            'by': by,
            'meta': meta,
        }

    def to_line(self, items):
        current_with = {}
        current_with["grant"] = []
        for item in items:
            if isinstance(item, tuple):
                current_with[item[0]] = item[1]
            elif isinstance(item, dict):  # grant_line
                if current_with['grant'] is None:
                    raise ValueError("'to' without preceding 'grant'")
                current_with["grant"].append(item)
        assert not set(current_with) - {'grant', 'objecttype', 'if', 'position', 'scope', 'name', 'description'}, set(current_with)
        assert current_with.get('objecttype') and '/' in current_with['objecttype'] or current_with['objecttype'] == '*'
        return {
            "type": "to",
            "to": current_with,
        }

    def grant_line(self, items):
        grant = dict(items)
        assert not set(grant) - {'actions', 'properties', 'permission', 'values'}, set(grant)
        assert 'permission' in grant or 'actions' in grant and set(grant) & {'actions', 'permission'} != {'actions', 'permission'}
        if 'permission' in grant:
            assert grant['permission'] in {'read', 'search', 'write', 'readonly', 'writeonly', 'none', '*'}
        return grant

    def by_kvpair(self, items):
        return self.kvpair(items)

    def to_kvlistpair(self, items):
        return self.kvlistpair(items)

    def grant_kvlistpair(self, items):
        return self.kvlistpair(items)

    def kvpair(self, items):
        key, value = items
        return (str(key), value)

    def kvlistpair(self, items):
        key, (value,) = items
        key = str(key)
        if key in {"actions", "properties"} and isinstance(value, str):
            value = [v.strip() for v in value.split(",")]
            if key == "actions":
                assert not set(value) - {'search', 'read', 'create', 'modify', 'rename', 'remove', 'move', 'reports-type-query', 'report-create', '*'}, value
        return (key, value)

    def value(self, items):
        return items[0]

    def valuelist(self, items):
        return items

    def list(self, items):
        return items

    def QUOTED_STRING(self, s):
        return s[1:-1]  # remove quotes

    def NAME(self, s):
        return str(s)

    def __default__(self, data, children, meta):  # noqa: PLW3201
        if not data.startswith('__'):
            log.error("UNHANDLED RULE: %s", data)
        return super().__default__(data, children, meta)

    @staticmethod
    def compose(parsed):
        result = io.StringIO()
        to_items = {'grant', 'objecttype', 'if', 'position', 'scope'}

        def _kv(items, restricted=None):
            return ' '.join(f'{k}="{",".join(v)}"' if isinstance(v, list) else f'{k}="{v}"' for k, v in items.items() if v is not None and (not restricted or k in restricted))

        for cond in parsed['conditions']:
            params = '  parameters %s' % _kv(cond['parameters']) if cond.get('parameters') else ''
            print(f'named-condition "{cond["name"]}"\n  condition="{cond["condition"]}"\n{params}\n', file=result)
        for rule in parsed['rules']:
            by = rule.pop('by')
            to = rule.pop('to')
            roles = ' by %s' % _kv(by[0]) if len(by) == 1 else '\n  ' + '\n  '.join('by %s' % _kv(r) for r in by)
            params = '\n  %s' % _kv(rule) if rule else ''
            print(file=result)
            print(f'access{roles}{params}', file=result)
            for to_clause in to:
                print(file=result)
                grants = to_clause.pop('grant')
                print('  to %s' % _kv(to_clause, to_items), file=result)
                if set(to_clause) - to_items:
                    print('    %s\n' % _kv(to_clause, set(to_clause) - to_items), file=result)
                for grant in grants:
                    print('    grant %s' % _kv(grant), file=result)
        return result.getvalue().strip()


class UDMAuthorizationConfig:
    """UDM specific DSL"""

    def __init__(self, filename):
        self.filename = filename
        self.parser = Lark(UDM_DSL_GRAMMAR, parser="lalr", transformer=_DSLTransformer())

    def parse(self):
        self.parsed = self.parser.parse(open(self.filename).read())

    def compose(self):
        return _DSLTransformer.compose(copy.deepcopy(self.parsed))

    def to_yaml(self):
        conf = AuthorizationConfig(self.filename.replace('.acl', '') + '.yaml')

        for cond in self.parsed['conditions']:
            conf.conditions[cond['name']] = {cond['condition']: cond['parameters']}

        for rule in self.parsed['rules']:
            by = rule.get('by')
            to = rule.get('to')
            for role in by:
                role_namespace, role_name = role['role'].rsplit(':', 1)

                # create capability bundle (in the namespace of the role) and assign it to the role-capability-mapping
                bundle_name = role['role'].rsplit(':', 1)[-1]
                cap_bundle_string = f'{role_namespace}:{bundle_name}'
                bundle = conf.capability_bundles.setdefault(role_namespace, {}).setdefault(bundle_name, [])

                # create one role capability mapping for each role and assign one capability bundle, where all capabilities are added
                role_cap_map = conf.role_capability_mapping.setdefault(role_namespace, {}).setdefault(role_name, {
                    'permissions': [],
                    'capabilities': [],
                    'capability-bundles': [cap_bundle_string],
                })
                role_cap_map['displayname'] = rule.get('description', '')

                more_tos = []
                for to_clause in to:
                    object_type = to_clause["objecttype"]
                    if object_type == '*':
                        for oc in all_modules:
                            new_to_clase = copy.deepcopy(to_clause)
                            new_to_clase['objecttype'] = oc
                            more_tos.append(new_to_clase)
                    else:
                        more_tos.append(to_clause)

                for to_clause in more_tos:
                    object_type = to_clause["objecttype"]
                    grants = to_clause.get('grant', [])

                    # create a capability and assign it to the capability budle
                    capability_name = bundle_name
                    capability_namespace = f'udm:{object_type}'

                    if capability_name in conf.capabilities.get(capability_namespace, {}):
                        capability_name = f'{capability_name}-{len(conf.capabilities[capability_namespace])}'

                    capability_string = f'udm:{object_type}:{capability_name}'

                    bundle.append(capability_string)
                    cap = conf.capabilities.setdefault(capability_namespace, {}).setdefault(capability_name, {
                        'displayname': to_clause.get('displayname', ''),
                        'grants-permissions': [],
                        'conditions': {'AND': []},
                    })
                    conditions = cap['conditions']['AND']

                    # create a permission set for each capibility and assign it to the capability
                    psetname = f"{object_type.replace('/', '-')}-{capability_name}-all"
                    if psetname in conf.permission_sets:
                        psetname = f'{psetname}-{len(conf.permission_sets)}'
                    # assert psetname not in conf.permission_sets, psetname
                    permissions = conf.permission_sets.setdefault(psetname, [])
                    cap['grants-permissions'].append(psetname)

                    for prop in grants:
                        # grant given actions
                        if 'properties' not in prop:
                            all_actions = {'search', 'read', 'create', 'modify', 'rename', 'remove', 'move', 'reports-type-query', 'report-create'}
                            actions = set(prop.get('actions', []))
                            if '*' in actions:
                                actions.update(all_actions)
                                actions.remove('*')
                            elif 'read' in actions:
                                actions.add('search')

                            permissions.extend(
                                f'udm:{object_type}:{action}' for action in sorted(actions)
                            )
                            continue

                        # grant given properties
                        perms = set(prop['properties'])
                        all_perms = {'read', 'search', 'write', 'readonly', 'writeonly', 'none'}

                        if '*' in perms:
                            perms.update(all_perms)
                            perms.remove('*')
                        if 'read' in perms:
                            perms.add('search')
                        if 'write' in perms:
                            perms.add('read')
                            perms.add('write')
                            perms.add('search')

                        permissions.extend(
                            f"udm:{object_type}:{prop['permission']}-property-{propname}"
                            for propname in sorted(prop['properties'])
                        )

                    # restrict capability to conditions
                    if object_type != '*':
                        ot_condition = f'object-type-is-{object_type.replace("/", "-")}'
                        cap['conditions'].setdefault('AND', []).append(ot_condition)
                        conf.conditions[ot_condition] = {
                            "udm:conditions:target_object_type_equals": {
                                "objectType": object_type,
                            },
                        }

                    position = to_clause.get('position')
                    scope = to_clause.get('scope', 'base')
                    if position and position == '{context}':
                        context = role['context']
                        assert context, to_clause
                        name = self._unique(f"{scope}-{context}")
                        pos_condition = f"position-from-context-{name}"
                        conditions.append(pos_condition)
                        conf.conditions[pos_condition] = {
                            "udm:conditions:target_position_from_context": {
                                "context": context,
                                "scope": scope,
                            },
                        }
                    elif position:
                        position = position.format(ldap_base=ucr['ldap/base'])
                        name = self._unique(f"{scope}-{position}")
                        pos_condition = f"position-{name}"
                        conditions.append(pos_condition)
                        conf.conditions[pos_condition] = {
                            "udm:conditions:target_position_in": {
                                "position": position,
                                "scope": scope,
                            },
                        }

                    if not conditions:
                        cap['conditions'].pop('AND')

                    if to_clause.get('if'):
                        conditions.append(to_clause['if'])

        return yaml.dump(conf.compose())

    def _unique(self, string):
        return hashlib.sha1(string.encode()).hexdigest()[:8]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    parser.add_argument('--compose', action='store_true')
    parser.add_argument('--convert', action='store_true')
    args = parser.parse_args()

    conf = UDMAuthorizationConfig(args.config)
    conf.parse()
    if args.compose:
        print(conf.compose())
    if args.convert:
        print(conf.to_yaml())
