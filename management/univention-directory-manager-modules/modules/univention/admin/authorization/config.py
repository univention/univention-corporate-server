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
import sys
from collections import defaultdict
from pathlib import Path

import lark
import ldap.dn
import yaml
from lark import Lark, Transformer

import univention.admin.modules
from univention.authorization.config import AuthorizationConfig
from univention.config_registry import ucr
from univention.dn import DN


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

TO_KEY: "objecttype" | "if" | "position" | "name" | "description"
to_line: "to" to_kvlistpair+ grant_line*
to_kvlistpair: NAME "=" valuelist -> to_kvlistpair

GRANT_KEY: "actions" | "properties" | "permission" | "values"
grant_line: "grant" grant_kvlistpair+
grant_kvlistpair: NAME "=" valuelist -> grant_kvlistpair

kvpair: NAME "=" value
value: QUOTED_STRING | NAME

valuelist: QUOTED_STRING | list | NAME

list: "[" [QUOTED_STRING ("," QUOTED_STRING)*] "]"

NAME: /[a-zA-Z_][\w\/\-.,\/]*/
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

_SCOPES = {
    '': 'base',
    'one': 'one',
    'onelevel': 'one',
    'sub': 'subtree',
    'subtree': 'subtree',
    'base': 'base',
    'children': 'children',
}

_VALUE_OPERATORS = {
    '': '==',
    'equals': '==',
    'not-equals': '!=',
    'equals,i': '==-i',
    'not-equals,i': '!=-i',
    'regex': 'regex-match',
    'not-regex': 'regex-nomatch',
    'regex,i': 'regex-match-i',
    'not-regex,i': 'regex-nomatch-i',
    'dn': 'dn',
    'dn,base': 'dn',
    'dn,subtree': 'dn-subtree',
    'dn,one': 'dn-one',
    'dn,children': 'dn-children',
}

BUNDLE_NAMESPACE = 'udm:bundles'
ACTIONS = ('search', 'read', 'create', 'modify', 'rename', 'remove', 'move', 'report-create')
PERMISSIONS = ('search', 'read', 'write', 'readonly', 'writeonly', 'none')
SORT_PRIO = {
    'actions': {v: k for k, v in [*list(enumerate(ACTIONS)), [len(ACTIONS), '*']]},
    'permissions': {v: k for k, v in [*list(enumerate(PERMISSIONS)), [len(PERMISSIONS), '*']]},
}


class DSLSyntaxError(SyntaxError):
    pass


class _DSLTransformer(Transformer):
    """Transformer for the UDM DSL"""

    def __init__(self, filename, *args, strict=False, **kwargs):
        self.__filename = filename
        self.__strict = strict
        self.__unique_names = set()
        super().__init__(*args, **kwargs)

    def start(self, items):
        data = {'conditions': [], 'rules': []}
        for all_items in items:
            for item in all_items:
                if item['type'] == 'named-condition':
                    data['conditions'].append(item)
                elif item['type'] == 'access':
                    data['rules'].append(item)
                else:
                    raise DSLSyntaxError('unknown type', (self.__filename, 0, 0, item['type']))
                item.pop('type')

        return data

    def statement(self, items):
        return items

    def named_condition(self, items):
        name = items[0]
        cond = items[1]
        parameters = items[2] if len(items) > 2 else {}
        return {
            'type': 'named-condition',
            'name': name,
            'condition': cond,
            'parameters': parameters,
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
            if item.get('type') == 'by':
                by_blocks.append(item['by'])
                meta = item['meta']
            elif item['type'] == 'to':
                to_blocks.append(item['to'])
            else:
                raise DSLSyntaxError('unknown type', (self.__filename, 0, 0, item['type']))

        return {
            'type': 'access',
            'by': by_blocks,
            'to': to_blocks,
            **meta,
        }

    def by_line(self, items):
        meta = dict(items)
        by = {'role': meta.pop('role'), 'context': meta.pop('context', None)}
        self._assert_names('by', meta, {'description'})
        self._assert_names('by', by, {'role', 'context'})
        if by['role'].count(':') != 2:
            raise DSLSyntaxError('role: must contain two ":"', (self.__filename, 0, 0, by['role']))

        return {
            'type': 'by',
            'by': by,
            'meta': meta,
        }

    def to_line(self, items):
        current_to = {}
        current_to['grant'] = []
        for item in items:
            if isinstance(item, tuple):
                current_to[item[0]] = item[1]
            elif isinstance(item, dict):  # grant_line
                if current_to['grant'] is None:
                    raise ValueError("'to' without preceding 'grant'")
                current_to['grant'].append(item)

        self._assert_names('to', current_to, {'grant', 'objecttype', 'if', 'position', 'name', 'description'})
        object_type = current_to.get('objecttype')
        if not object_type:
            raise DSLSyntaxError('objecttype required', (self.__filename, 0, 0, repr(items)))
        if '/' not in object_type and object_type != '*':
            raise DSLSyntaxError('invalid objecttype', (self.__filename, 0, 0, object_type))

        if name := current_to.get('name'):
            if name in self.__unique_names:
                raise DSLSyntaxError('duplicated name', (self.__filename, 0, 0, current_to['name']))
            self.__unique_names.add(name)

        mod = univention.admin.modules.get(object_type)
        if object_type != '*' and not mod:
            if self.__strict:
                raise DSLSyntaxError(f'Object type {object_type} unknown!', (self.__filename, 0, 0, object_type))
            print(f'Warning: No object type {object_type!r} exists.', file=sys.stderr)

        for grant in current_to.get('grant', []):
            for prop in grant.get('properties', []):
                if prop != '*' and (not mod or not mod.property_descriptions.get(prop)):
                    if self.__strict:
                        raise DSLSyntaxError(f'Property {object_type}:{prop} unknown!', (self.__filename, 0, 0, f'{object_type}:{prop}'))
                    print(f'Warning: No property {prop!r} for {object_type!r} exists. Assuming it is an extended attribute.', file=sys.stderr)

        return {
            'type': 'to',
            'to': current_to,
        }

    def grant_line(self, items):
        grant = dict(items)
        self._assert_names('grant', grant, {'actions', 'properties', 'permission', 'values'})

        if ('permission' not in grant and 'actions' not in grant) or set(grant) & {'actions', 'permission'} == {'actions', 'permission'}:
            raise DSLSyntaxError('invalid "grant": requires only one of actions or permission', (self.__filename, 0, 0, ''))

        if 'permission' in grant:
            self._assert_names('permission', set(grant['permission'].split(',')), {*PERMISSIONS, '*'})

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
        key, _, operator = str(key).partition('.')
        if key in ('values', 'position'):
            value = (operator, value)
            if key == 'position':
                self._assert_names('position.scope', {operator}, set(_SCOPES))
            elif key == 'values':
                self._assert_names('values.operator', {operator}, set(_VALUE_OPERATORS))
        if key in {'actions', 'properties'} and isinstance(value, str):
            value = [v.strip() for v in value.split(',')]
            if key == 'actions':
                self._assert_names('actions', set(value), {*ACTIONS, '*'})
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
            log.error('UNHANDLED RULE: %s', data)
        return super().__default__(data, children, meta)

    def _assert_names(self, name, obj, names):
        if set(obj) - names:
            invalid = ','.join(set(obj) - names)
            raise DSLSyntaxError(f'unknown {name!r}: {invalid!r}', (self.__filename, 0, 0, invalid))

    @staticmethod
    def compose(parsed):
        result = io.StringIO()
        to_items = {'grant', 'objecttype', 'if', 'position'}

        def _v(k, v):
            if isinstance(v, list):
                sv = sorted(v, key=lambda x: SORT_PRIO.get(k, {}).get(x, x))
                return f'{k}="{",".join(sv)}"'
            if isinstance(v, str):
                return f'{k}="{v}"'
            if v[0]:
                return f'{k}.{v[0]}="{v[1]}"'
            return f'{k}="{v[1]}"'

        def _kv(items, restricted=None):
            return ' '.join(
                _v(k, v)
                for k, v in items.items()
                if v is not None and (not restricted or k in restricted)
            )

        for cond in parsed['conditions']:
            params = '  parameters %s' % _kv(cond['parameters']) if cond.get('parameters') else ''
            print(f'named-condition "{cond["name"]}"\n  condition="{cond["condition"]}"\n{params}\n', file=result)
        for rule in parsed['rules']:
            by = rule.pop('by')
            to = rule.pop('to')
            roles = ' by %s' % _kv(by[0]) if len(by) == 1 else '\n  ' + '\n  '.join('by %s' % _kv(r) for r in sorted(by, key=lambda x: x['role']))
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

    def __init__(self, filenames, *, strict=False):
        self.filenames = filenames
        self.strict = strict
        self.parsed = {}

    def parse(self):
        univention.admin.modules.update()
        try:
            for filename in self.filenames:
                parser = Lark(UDM_DSL_GRAMMAR, parser='lalr', transformer=_DSLTransformer(str(filename), strict=self.strict))
                result = parser.parse(filename.read_text())
                for k, v in result.items():
                    self.parsed.setdefault(k, []).extend(v)
        except lark.exceptions.LarkError as exc:
            raise DSLSyntaxError(str(exc)) from exc

    def compose(self):
        return _DSLTransformer.compose(copy.deepcopy(self.parsed))

    def to_yaml(self):
        univention.admin.modules.update()
        all_modules = [name for name in univention.admin.modules.modules if not univention.admin.modules.virtual(name)]
        conf = AuthorizationConfig(self.filenames[0].with_suffix('.yaml'))

        for cond in self.parsed['conditions']:
            conf.conditions[cond['name']] = {cond['condition']: cond['parameters']}

        for rule in self.parsed['rules']:
            by = rule.get('by')
            to = rule.get('to')

            bundle_name = '--'.join(sorted(role['role'].rsplit(':', 1)[-1] for role in by))
            bundle_name = self._unique(conf.capability_bundles.setdefault(BUNDLE_NAMESPACE, {}), bundle_name)

            cap_bundle_string = f'{BUNDLE_NAMESPACE}:{bundle_name}'
            bundle = conf.capability_bundles.setdefault(BUNDLE_NAMESPACE, {}).setdefault(bundle_name, [])

            for role in by:
                role_namespace, _, role_name = role['role'].rpartition(':')
                # create one role capability mapping for each role and assign one capability bundle, where all capabilities are added
                role_cap_map = conf.role_capability_mapping.setdefault(role_namespace, {}).setdefault(role_name, {
                    'permissions': [],
                    'capabilities': [],
                    'capability-bundles': [],
                })
                role_cap_map['displayname'] = rule.get('description', '')
                if cap_bundle_string not in role_cap_map['capability-bundles']:
                    role_cap_map['capability-bundles'].append(cap_bundle_string)

            wildcard_object_type = False
            expanded_to_clauses = []
            for to_clause in to:
                object_type = to_clause['objecttype']
                if object_type == '*':
                    wildcard_object_type = True
                    for oc in all_modules:
                        new_to_clase = copy.deepcopy(to_clause)
                        new_to_clase['objecttype'] = oc
                        expanded_to_clauses.append(new_to_clase)
                else:
                    expanded_to_clauses.append(to_clause)

            for to_clause in expanded_to_clauses:
                object_type = to_clause['objecttype']
                grants = to_clause.get('grant', [])

                # create a capability and assign it to the capability budle
                capability_namespace = f'udm:{object_type}'
                capability_name = self._unique(conf.capabilities.get(capability_namespace, {}), bundle_name)
                capability_string = f'{capability_namespace}:{capability_name}'

                bundle.append(capability_string)
                cap = conf.capabilities.setdefault(capability_namespace, {}).setdefault(capability_name, {
                    'displayname': to_clause.get('displayname', ''),
                    'grants-permissions': [],
                    'conditions': {'AND': []},
                })
                conditions = cap['conditions']['AND']

                # create a permission set for each capibility and assign it to the capability
                psetname = to_clause.get('name')
                if psetname and wildcard_object_type:
                    psetname = f'{psetname}-{object_type.replace("/", "-")}'
                psetname = psetname or f'{object_type.replace("/", "-")}-{capability_name}-all'
                psetname = self._unique(conf.permission_sets, psetname)
                # assert psetname not in conf.permission_sets, psetname
                permissions = set()
                cap['grants-permissions'].append(psetname)

                for prop in grants:
                    # grant given actions
                    if 'properties' not in prop:
                        actions = set(prop.get('actions', []))
                        if '*' in actions:
                            actions.update(set(ACTIONS))
                            actions.remove('*')
                        elif 'read' in actions:
                            actions.add('search')

                        permissions.update({
                            f'udm:{object_type}:{action}' for action in sorted(actions)
                        })
                        continue

                    # grant given properties
                    perms = set(prop['permission'].split(',')) if isinstance(prop['permission'], str) else set(prop['permission'])
                    # perms = {prop['permission']}

                    if '*' in perms:
                        perms.update(set(PERMISSIONS))
                        perms.remove('*')
                    if 'read' in perms:
                        perms.add('search')
                    if 'write' in perms:
                        perms.add('read')
                        perms.add('write')
                        perms.add('search')

                    permissions.update({
                        f'udm:{object_type}:{perm}-property-{propname}'
                        for propname in prop['properties']
                        for perm in perms
                    })

                    for propname in sorted(prop['properties']):
                        operator, values = prop.get('values', [None, None])
                        if not values:
                            continue

                        if len(grants) != 1:
                            raise RuntimeError('Security warning: Value based checks must create exactly only one capability (to block)!')
                        if len(prop['properties']) != 1:
                            raise RuntimeError('Security warning: Value based checks must check only one property!')
                        if prop['permission'] == 'write' or 'write' in perms:
                            raise RuntimeError('Security warning: Value based checks most likely should not add write permissions, design it the opposite way!')

                        operator = _VALUE_OPERATORS.get(operator, '==')
                        val_condition = self._unique(conf.conditions, f'{object_type.replace("/", "-")}-{propname}-values-{operator}', values='||'.join(sorted(values)))
                        conditions.append(val_condition)
                        conf.conditions[val_condition] = {
                            'udm:conditions:target_property_value_compares': {
                                'property': propname,
                                'operator': operator,
                                'values': values,
                            },
                        }

                conf.permission_sets.setdefault(psetname, []).extend(sorted(permissions))

                # restrict capability to conditions
                if object_type != '*':
                    ot_condition = f'object-type-is-{object_type.replace("/", "-")}'
                    cap['conditions'].setdefault('AND', []).append(ot_condition)
                    conf.conditions[ot_condition] = {
                        'udm:conditions:target_object_type_equals': {
                            'objectType': object_type,
                        },
                    }

                scope, position = to_clause.get('position', [None, None])
                scope = _SCOPES.get(scope, 'base')
                if position and position == '{context}':
                    context = role['context']
                    assert context, to_clause
                    pos_condition = self._unique(conf.conditions, 'position-from-context', scope=scope, context=context)
                    conditions.append(pos_condition)
                    conf.conditions[pos_condition] = {
                        'udm:conditions:target_position_from_context': {
                            'context': context,
                            'scope': scope,
                        },
                    }
                elif position:
                    position = position.format(ldap_base=ucr['ldap/base'])
                    pos_condition = self._unique(conf.conditions, 'position', scope=scope, position=position)
                    conditions.append(pos_condition)
                    conf.conditions[pos_condition] = {
                        'udm:conditions:target_position_in': {
                            'position': position,
                            'scope': scope,
                        },
                    }

                if not conditions:
                    cap['conditions'].pop('AND')

                if to_clause.get('if'):
                    conditions.append(to_clause['if'])

        return yaml.dump(conf.compose())

    def create_container(self, lo, pos):
        container_cn = univention.admin.modules.get('container/cn')
        for dn in DN(pos).walk(ucr['ldap/base']):
            if not univention.admin.objects.get_object(lo, str(dn)):
                po = univention.admin.uldap.position(ucr['ldap/base'])
                po.setDn(str(dn.parent))
                obj = container_cn.object(None, lo, po)
                obj['name'] = dn.rdn[1]
                obj.create()

    def to_udm(self):
        univention.admin.modules.update()
        lo, po = univention.admin.uldap.getAdminConnection()
        all_modules = [name for name in univention.admin.modules.modules if not univention.admin.modules.virtual(name)]
        conf = AuthorizationConfig(self.filenames[0].with_suffix('.yaml'))

        privilege_base = f"cn={ldap.dn.escape_dn_chars(self.filenames[0].stem)},cn=privileges,cn=authz,cn=univention,{ucr['ldap/base']}"
        policy_base = f"cn={ldap.dn.escape_dn_chars(self.filenames[0].stem)},cn=policies,cn=authz,cn=univention,{ucr['ldap/base']}"

        authz_policy = univention.admin.modules.get('authorization/policy')
        authz_privilege = univention.admin.modules.get('authorization/privilege')
        self.create_container(lo, privilege_base)
        self.create_container(lo, policy_base)

        for cond in self.parsed['conditions']:
            conf.conditions[cond['name']] = {cond['condition']: cond['parameters']}

        for rule in self.parsed['rules']:
            by = rule.get('by')
            to = rule.get('to')
            privileges = []

            bundle_name = '--'.join(sorted(role['role'].rsplit(':', 1)[-1] for role in by))
            bundle_name = self._unique(conf.capability_bundles.setdefault(BUNDLE_NAMESPACE, {}), bundle_name)

            cap_bundle_string = f'{BUNDLE_NAMESPACE}:{bundle_name}'
            bundle = conf.capability_bundles.setdefault(BUNDLE_NAMESPACE, {}).setdefault(bundle_name, [])

            for role in by:
                role_namespace, _, role_name = role['role'].rpartition(':')
                # create one role capability mapping for each role and assign one capability bundle, where all capabilities are added
                role_cap_map = conf.role_capability_mapping.setdefault(role_namespace, {}).setdefault(
                    role_name,
                    {
                        'permissions': [],
                        'capabilities': [],
                        'capability-bundles': [],
                    },
                )
                role_cap_map['displayname'] = rule.get('description', '')
                if cap_bundle_string not in role_cap_map['capability-bundles']:
                    role_cap_map['capability-bundles'].append(cap_bundle_string)

            expanded_to_clauses = []
            wildcard_object_type = False
            for to_clause in to:
                object_type = to_clause['objecttype']
                if object_type == '*':
                    wildcard_object_type = True
                    for oc in all_modules:
                        new_to_clase = copy.deepcopy(to_clause)
                        new_to_clase['objecttype'] = oc
                        expanded_to_clauses.append(new_to_clase)
                else:
                    expanded_to_clauses.append(to_clause)

            for to_clause in expanded_to_clauses:
                object_type = to_clause['objecttype']
                grants = to_clause.get('grant', [])

                # create a capability and assign it to the capability budle
                capability_namespace = f'udm:{object_type}'
                capability_name = self._unique(conf.capabilities.get(capability_namespace, {}), bundle_name)
                capability_string = f'{capability_namespace}:{capability_name}'

                bundle.append(capability_string)
                cap = conf.capabilities.setdefault(capability_namespace, {}).setdefault(
                    capability_name,
                    {
                        'displayname': to_clause.get('displayname', ''),
                        'grants-permissions': [],
                        'conditions': {'AND': []},
                    },
                )
                conditions = cap['conditions']['AND']

                # create a permission set for each capibility and assign it to the capability
                psetname = to_clause.get('name')
                if psetname and wildcard_object_type:
                    psetname = f'{psetname}-{object_type.replace("/", "-")}'
                psetname = psetname or f'{object_type.replace("/", "-")}-{capability_name}-all'
                psetname = self._unique(conf.permission_sets, psetname)
                # assert psetname not in conf.permission_sets, psetname
                permissions = set()
                cap['grants-permissions'].append(psetname)
                priv_dn = f'cn={ldap.dn.escape_dn_chars(psetname)},{privilege_base}'
                try:
                    priv = authz_privilege.object(None, lo, po, priv_dn)
                except univention.admin.uexceptions.noObject:
                    priv = authz_privilege.object(None, lo, po)
                    po.setDn(privilege_base)
                priv['objecttype'] = object_type
                priv['description'] = to_clause.get('description')
                priv['name'] = psetname  # capability_name
                priv_actions = set()
                priv_props = []

                for prop in grants:
                    # grant given actions
                    if 'properties' not in prop:
                        actions = set(prop.get('actions', []))
                        if '*' in actions:
                            actions.update(set(ACTIONS))
                            actions.remove('*')
                        elif 'read' in actions:
                            actions.add('search')

                        permissions.update({f'udm:{object_type}:{action}' for action in sorted(actions)})
                        priv_actions.update(actions)
                        continue

                    # grant given properties
                    perms = set(prop['permission'].split(','))

                    if '*' in perms:
                        perms.update(set(PERMISSIONS))
                        perms.remove('*')
                    if 'read' in perms:
                        perms.add('search')
                    if 'write' in perms:
                        perms.add('read')
                        perms.add('write')
                        perms.add('search')

                    priv_props.extend([[propname, perm, ''] for propname in prop['properties'] for perm in perms])
                    permissions.update({f'udm:{object_type}:{perm}-property-{propname}' for propname in prop['properties'] for perm in perms})

                    for propname in sorted(prop['properties']):
                        operator, values = prop.get('values', [None, None])
                        if not values:
                            continue

                        if len(grants) != 1:
                            raise RuntimeError('Security warning: Value based checks must create exactly only one capability (to block)!')
                        if len(prop['properties']) != 1:
                            raise RuntimeError('Security warning: Value based checks must check only one property!')
                        if prop['permission'] == 'write' or 'write' in perms:
                            raise RuntimeError('Security warning: Value based checks most likely should not add write permissions, design it the opposite way!')

                        operator = _VALUE_OPERATORS.get(operator, '==')
                        val_condition = self._unique(conf.conditions, f'{object_type.replace("/", "-")}-{propname}-values-{operator}', values='||'.join(sorted(values)))
                        conditions.append(val_condition)
                        conf.conditions[val_condition] = {
                            'udm:conditions:target_property_value_compares': {
                                'property': propname,
                                'operator': operator,
                                'values': values,
                            },
                        }

                conf.permission_sets.setdefault(psetname, []).extend(sorted(permissions))

                # restrict capability to conditions
                if object_type != '*':
                    ot_condition = f'object-type-is-{object_type.replace("/", "-")}'
                    cap['conditions'].setdefault('AND', []).append(ot_condition)
                    conf.conditions[ot_condition] = {
                        'udm:conditions:target_object_type_equals': {
                            'objectType': object_type,
                        },
                    }

                scope, position = to_clause.get('position', [None, None])
                scope = _SCOPES.get(scope, 'base')
                if position:
                    priv['position'] = [scope, position.format(context='cn={context}', ldap_base=ucr['ldap/base'])]
                if position and position == '{context}':
                    context = role['context']
                    assert context, to_clause
                    pos_condition = self._unique(conf.conditions, 'position-from-context', scope=scope, context=context)
                    conditions.append(pos_condition)
                    conf.conditions[pos_condition] = {
                        'udm:conditions:target_position_from_context': {
                            'context': context,
                            'scope': scope,
                        },
                    }
                elif position:
                    position = position.format(ldap_base=ucr['ldap/base'])
                    pos_condition = self._unique(conf.conditions, 'position', scope=scope, position=position)
                    conditions.append(pos_condition)
                    conf.conditions[pos_condition] = {
                        'udm:conditions:target_position_in': {
                            'position': position,
                            'scope': scope,
                        },
                    }

                if not conditions:
                    cap['conditions'].pop('AND')

                if to_clause.get('if'):
                    conditions.append(to_clause['if'])
                    priv['condition'] = to_clause['if']

                priv['actions'] = sorted(priv_actions)
                priv['properties'] = sorted(priv_props)
                privileges.append(priv.modify() if priv.exists() else priv.create())

            name = '--'.join(role['role'].rsplit(':', 1)[-1] for role in by)
            pol_dn = f'cn={ldap.dn.escape_dn_chars(name)},{policy_base}'
            try:
                pol = authz_policy.object(None, lo, po, pol_dn)
            except univention.admin.uexceptions.noObject:
                pol = authz_policy.object(None, lo, po)
                po.setDn(policy_base)
            pol['description'] = rule.get('description', '')
            pol['roles'] = [role['role'] for role in by]
            pol['name'] = name
            pol['privileges'] = privileges
            if pol.exists():
                pol.modify()
            else:
                pol.create()

    def load_from_udm(self):
        univention.admin.modules.update()
        lo, _po = univention.admin.uldap.getAdminConnection()
        all_modules = [name for name in univention.admin.modules.modules if not univention.admin.modules.virtual(name)]
        rules = []
        authz_policy = univention.admin.modules.get('authorization/policy')
        authz_privilege = univention.admin.modules.get('authorization/privilege')

        for policy in authz_policy.lookup(None, lo, ''):
            policy.open()
            ocs = {}
            for privilege in policy['privileges']:
                privilege = authz_privilege.object(None, lo, None, privilege)
                data = ocs.setdefault(privilege['objecttype'], {'grants': [], 'actions': set()})
                data['name'] = privilege['name']

                data['actions'].update(set(privilege['actions']))
                if privilege['condition']:
                    data['if'] = privilege['condition']

                context = None
                position = (None, None)
                if privilege['position']:
                    scope, pos = privilege['position']
                    pos = pos.replace('cn={context}', '{context}').replace(ucr['ldap/base'], '{ldap_base}')
                    if pos == '{context}':
                        context = 'udm:contexts:position'
                    position = (scope, pos)
                    data['position'] = position
                else:
                    data['position'] = None
                data['description'] = privilege['description']

                perm_to_props = defaultdict(set)
                for prop, perm, _ in privilege['properties']:
                    perm_to_props[perm].add(prop)

                propset_to_perms = defaultdict(set)
                for perm, props in perm_to_props.items():
                    key = tuple(frozenset(sorted(props)))
                    propset_to_perms[key].add(perm)

                for propset, permissions in sorted(propset_to_perms.items(), key=lambda x: sorted(x[1])):
                    data['grants'].append(
                        {
                            'properties': list(propset),
                            'permission': list(permissions),
                        },
                    )

            rule = {}
            rule['to'] = []
            first = next(iter(ocs.values()))
            if all(d == first for d in ocs.values()) and set(ocs) == set(all_modules):
                ocs = {'*': first}
            for objecttype, data in ocs.items():
                to_clause = {
                    'grant': [{'actions': list(data['actions'])}] + data['grants'],
                    'objecttype': objecttype,
                    'name': data.get('name'),
                    'if': data.get('if'),
                    'position': data['position'],
                    'description': data['description'],
                }
                for k in ('position', 'if', 'name'):
                    if not to_clause[k]:
                        to_clause.pop(k)
                rule['to'].append(to_clause)
            rule['description'] = policy['description']
            rule['by'] = [{'role': r, 'context': context} for r in policy['roles']]
            rules.append(rule)

        self.parsed['rules'] = rules
        # self.parsed = {'conditions': [{'name': 'is-self', 'condition': 'guardian:builtin:target_is_self', 'parameters': {}}], 'rules': rules}

    def _unique(self, parent, string, **unique):
        if unique:
            hash_ = hashlib.sha1('-'.join(sorted(unique.values())).encode()).hexdigest()[:8]
        else:
            if string not in parent:
                return string
            hash_ = str(len(parent))
        return f'{string}-{hash_}'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', action='append', type=Path)
    parser.add_argument('--compose-from-udm', action='store_true')
    parser.add_argument('--compose', action='store_true')
    parser.add_argument('--convert', action='store_true')
    parser.add_argument('--unstrict', action='store_true')
    args = parser.parse_args()

    conf = UDMAuthorizationConfig(args.config, strict=not args.unstrict)
    conf.parse()
    if args.compose_from_udm:
        conf.load_from_udm()
        print(conf.compose())
    if args.compose:
        print(conf.compose())
    if args.convert:
        print(conf.to_yaml())
