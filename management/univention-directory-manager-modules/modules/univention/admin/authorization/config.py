#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
A domain specific language (DSL) for UDM access rules
inspired by LDAP ACLs
realized with extended BNF grammar and a LALR (Look-Ahead Left <- Right) Parser
and compiled to Cerbos derived roles and resource-policy rules.
"""

import ast
import copy
import io
import logging
import re
import sys
from pathlib import Path
from typing import ClassVar

import lark
import yaml
from lark import Lark, Transformer

from .utils import udm_object_action, udm_property_action, udm_property_action_wildcards, udm_resource_kind


try:
    from ruamel.yaml import YAML as RuamelYAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
except ImportError:  # pragma: no cover - optional at build/test time
    RuamelYAML = None
    CommentedMap = dict
    CommentedSeq = list

try:
    import univention.admin.modules
except ImportError:  # pragma: no cover
    univention = None

try:
    from univention.config_registry import ucr
except ImportError:  # pragma: no cover
    ucr = {}


log = logging.getLogger('ACL').getChild(__name__)


UDM_DSL_GRAMMAR = r"""
start: statement+

statement: condition | access_block

condition: "condition" QUOTED_STRING condition_line

condition_line: "expr=" QUOTED_STRING

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

_SCOPES = {
    '': 'base',
    'one': 'one',
    'onelevel': 'one',
    'sub': 'subtree',
    'subtree': 'subtree',
    'base': 'base',
    'children': 'children',
}

ACTIONS = ('search', 'read', 'create', 'modify', 'rename', 'remove', 'move', 'report-create', 'restore')
PERMISSIONS = ('search', 'read', 'write', 'readonly', 'writeonly', 'none')
SORT_PRIO = {
    'actions': {v: k for k, v in [*list(enumerate(ACTIONS)), [len(ACTIONS), '*']]},
    'permission': {v: k for k, v in [*list(enumerate(PERMISSIONS)), [len(PERMISSIONS), '*']]},
}
RE_ROLE = re.compile(r'^[^!*?\[\]{}]+$')

RESOURCE_DN = 'request.resource.attr.dn'
RESOURCE_POSITION = 'request.resource.attr.position'
CONTEXT_ROLES = 'request.principal.attr.contextRoles'
POLICY_ROOT = '/usr/share/univention-guardian-server/policies/udm'


def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_.-]+', '-', name.replace('/', '-')).strip('-') or 'policy'


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def _policy_map(d, commented=False):
    return CommentedMap(d) if commented and RuamelYAML is not None else d


def _policy_seq(seq, commented=False):
    return CommentedSeq(seq) if commented and RuamelYAML is not None else seq


def _dump_yaml_all(documents, *, commented=False):
    if commented and RuamelYAML is not None:
        yaml_writer = RuamelYAML()
        yaml_writer.default_flow_style = False
        yaml_writer.indent(mapping=2, sequence=4, offset=2)
        stream = io.StringIO()
        yaml_writer.dump_all(documents, stream)
        return stream.getvalue()
    return yaml.dump_all(documents, Dumper=_NoAliasDumper, sort_keys=False, allow_unicode=True)


def _dump_yaml(document, *, commented=False):
    if commented and RuamelYAML is not None:
        yaml_writer = RuamelYAML()
        yaml_writer.default_flow_style = False
        yaml_writer.indent(mapping=2, sequence=4, offset=2)
        stream = io.StringIO()
        yaml_writer.dump(document, stream)
        return stream.getvalue()
    return yaml.dump(document, Dumper=_NoAliasDumper, sort_keys=False, allow_unicode=True)


def _add_rule_comment(rules, index, name, description=None):
    if RuamelYAML is None or not isinstance(rules, CommentedSeq):
        return
    lines = []
    if name:
        lines.append(str(name))
    if description:
        lines.append(str(description))
    if lines:
        rules.yaml_set_comment_before_after_key(index, before='\n'.join(lines))


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


class DSLSyntaxError(SyntaxError):
    pass


class _DSLTransformer(Transformer):
    """Transformer for the UDM DSL."""

    def __init__(self, filename, *args, strict=False, **kwargs):
        self.__filename = filename
        self.__strict = strict
        self.__unique_names = set()
        super().__init__(*args, **kwargs)

    def start(self, items):
        data = {'conditions': [], 'rules': []}
        for all_items in items:
            for item in all_items:
                if item['type'] == 'condition':
                    data['conditions'].append(item)
                elif item['type'] == 'access':
                    data['rules'].append(item)
                else:
                    raise DSLSyntaxError('unknown type', (self.__filename, 0, 0, item['type']))
                item.pop('type')
        return data

    def statement(self, items):
        return items

    def condition(self, items):
        name = items[0]
        cond = items[1]
        return {
            'type': 'condition',
            'name': name,
            'expr': cond,
        }

    def condition_line(self, items):
        return items[0]

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
        by = {'role': meta.pop('role')}
        self._assert_names('by', meta, {'description'})
        self._assert_names('by', by, {'role'})
        if by['role'] != '*' and not RE_ROLE.match(by['role']):
            raise DSLSyntaxError('role: must not contain any of the following characters: ! * ? [ ] { }', (self.__filename, 0, 0, by['role']))

        return {
            'type': 'by',
            'by': by,
            'meta': meta,
        }

    def to_line(self, items):
        current_to = {'grant': []}
        for item in items:
            if isinstance(item, tuple):
                current_to[item[0]] = item[1]
            elif isinstance(item, dict):  # grant_line
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

        mod = self._get_udm_module(object_type)
        if object_type != '*' and not mod:
            if self.__strict:
                raise DSLSyntaxError(f'Object type {object_type} unknown!', (self.__filename, 0, 0, object_type))
            print(f'Warning: No object type {object_type!r} exists.', file=sys.stderr)

        for grant in current_to.get('grant', []):
            for prop in grant.get('properties', []):
                if prop != '*' and (not mod or not getattr(mod, 'property_descriptions', {}).get(prop)):
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
        if 'permission' in grant and 'properties' not in grant:
            raise DSLSyntaxError('invalid "grant": permission requires properties', (self.__filename, 0, 0, ''))
        if 'values' in grant and 'properties' not in grant:
            raise DSLSyntaxError('invalid "grant": values requires properties', (self.__filename, 0, 0, ''))
        if 'values' in grant and len(grant.get('properties', [])) != 1:
            raise DSLSyntaxError('invalid "grant": values requires exactly one property', (self.__filename, 0, 0, ''))

        if 'permission' in grant:
            perms = grant['permission'].split(',') if isinstance(grant['permission'], str) else grant['permission']
            self._assert_names('permission', set(perms), {*PERMISSIONS, '*'})

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
        if operator and key == 'values':
            raise DSLSyntaxError('values.* operators are deprecated; use values="<CEL>"', (self.__filename, 0, 0, key))
        if key == 'position':
            value = (operator, value)
            self._assert_names('position.scope', {operator}, set(_SCOPES))
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
        return ast.literal_eval(str(s))

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
    def _get_udm_module(object_type):
        if univention is None or object_type == '*':
            return None
        return univention.admin.modules.get(object_type)

    @staticmethod
    def compose(parsed):
        result = io.StringIO()
        to_items = {'grant', 'objecttype', 'if', 'position', 'name', 'description'}

        def _v(k, v):
            if isinstance(v, list):
                sv = sorted(v, key=lambda x: SORT_PRIO.get(k, {}).get(x, x))
                return f'{k}="{",".join(sv)}"'
            if isinstance(v, str):
                return f'{k}="{v}"'
            if isinstance(v, tuple):
                if v[0]:
                    return f'{k}.{v[0]}="{v[1]}"'
                return f'{k}="{v[1]}"'
            return f'{k}="{v}"'

        def _kv(items, restricted=None):
            return ' '.join(
                _v(k, v)
                for k, v in items.items()
                if v is not None and (not restricted or k in restricted)
            )

        for cond in parsed['conditions']:
            params = '  parameters %s' % _kv(cond['parameters']) if cond.get('parameters') else ''
            print(f'condition "{cond["name"]}"\n  condition="{cond["condition"]}"\n{params}\n', file=result)
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
                for grant in grants:
                    print('    grant %s' % _kv(grant), file=result)
        return result.getvalue().strip()


class UDMAuthorizationConfig:
    """Compile the UDM DSL into Cerbos resource-policy (and derived roles) rules."""

    USED_NAMES: ClassVar = {}

    def __init__(self, filename, *, strict=False):
        self.filename = Path(filename)
        self.parser = Lark(UDM_DSL_GRAMMAR, parser='lalr', transformer=_DSLTransformer(str(self.filename), strict=strict))

    def parse(self):
        if univention is not None:
            univention.admin.modules.update()
        try:
            self.parsed = self.parser.parse(self.filename.read_text())
        except lark.exceptions.LarkError as exc:
            raise DSLSyntaxError(str(exc)) from exc

    def compose(self):
        return _DSLTransformer.compose(copy.deepcopy(self.parsed))

    def to_yaml(self):
        """Return resource policies (and derived roles) as YAML."""
        compiled = self.to_resource_policy_data(commented=True)

        documents = []
        if compiled['derivedRoles']:
            documents.append(self._derived_roles_document(compiled['derivedRoles'], commented=True))

        for resource in sorted(compiled['resources']):
            documents.append(_policy_map({
                'apiVersion': 'api.cerbos.dev/v1',
                'description': f'Automatically generated rules from {self.filename.name}.',
                'disabled': False,
                'resourcePolicy': _policy_map({
                    'resource': resource,
                    'version': 'default',
                    'importDerivedRoles': ([compiled['derivedRoleSet']] if any(rule.get('derivedRoles') for rule in compiled['resources'][resource]) else []),
                    'rules': compiled['resources'][resource],
                }, True),
                'metadata': {'sourceFile': str(self.filename), 'annotations': {}},
            }, True))

        return _dump_yaml_all(documents, commented=True) if documents else ''

    def write_files(self, output_dir=None):
        """Write standalone generated resource-policy and derived-role files."""
        root = Path(output_dir or POLICY_ROOT)
        compiled = self.to_resource_policy_data(commented=True)

        paths = []
        if compiled['derivedRoles']:
            derived_dir = root / 'derived_roles'
            derived_dir.mkdir(parents=True, exist_ok=True)
            path = derived_dir / f'{sanitize_filename(compiled["derivedRoleSet"])}.yaml'
            path.write_text(_dump_yaml(self._derived_roles_document(compiled['derivedRoles'], commented=True), commented=True))
            paths.append(path)

        resource_dir = root / 'resources'
        resource_dir.mkdir(parents=True, exist_ok=True)
        for resource, rules in sorted(compiled['resources'].items()):
            path = resource_dir / f'{sanitize_filename(resource)}.yaml'
            doc = {
                'apiVersion': 'api.cerbos.dev/v1',
                'description': f'Automatically generated rules from {self.filename.name}.',
                'disabled': False,
                'resourcePolicy': {
                    'resource': resource,
                    'version': 'default',
                    'importDerivedRoles': ([compiled['derivedRoleSet']] if any(rule.get('derivedRoles') for rule in rules) else []),
                    'rules': rules,
                },
                'metadata': {'sourceFile': str(self.filename), 'annotations': {}},
            }
            path.write_text(_dump_yaml(doc, commented=True))
            paths.append(path)

        return paths

    def to_resource_policy_data(self, *, commented=False):
        """
        Compile DSL data.

        Positional role contexts become derived roles.
        Named ``if`` and grant-specific ``values`` expressions remain conditions on the exact resource-policy rule whose actions they guard.
        """
        named_conditions = {cond['name']: cond['expr'] for cond in self.parsed['conditions']}
        resources = {}
        derived_by_key = {}

        for access_block in self.parsed['rules']:
            roles = sorted({entry['role'] for entry in access_block.get('by', [])})
            for to_clause in access_block.get('to', []):
                for object_type in self._expand_object_types(to_clause['objecttype']):
                    resource = udm_resource_kind(object_type) if object_type != '*' else '*'
                    rules = resources.setdefault(resource, _policy_seq([], commented))
                    used = self.USED_NAMES.setdefault(resource, set())

                    for grant in to_clause.get('grant', []):
                        actions = self._grant_to_actions(grant)
                        static_roles = []
                        derived_roles = []
                        rule_conditions = []

                        position = to_clause.get('position')
                        if position and not self._is_context_position(position[1]):
                            rule_conditions.append(self._position_to_cel(roles[0], *position))

                        for role in roles:
                            if position and self._is_context_position(position[1]):
                                expr = self._position_to_cel(role, *position)
                                key = (role, expr)
                                name = derived_by_key.get(key)
                                if name is None:
                                    name = self._derived_role_name(role, position, set(derived_by_key.values()))
                                    derived_by_key[key] = name
                            else:
                                static_roles.append(role)

                            if position and self._is_context_position(position[1]):
                                derived_roles.append(name)

                        if_cond = to_clause.get('if')
                        if if_cond:
                            rule_conditions.append(named_conditions.get(if_cond, if_cond))
                        if grant.get('values'):
                            rule_conditions.append(self._values_to_cel(grant['values'], grant['properties'][0]))

                        base_name = to_clause.get('name')
                        if base_name:
                            base_name += '-actions' if grant.get('actions') else '-properties'
                        rule_name = self._unique_rule_name(base_name, used, actions, object_type)
                        rule = _policy_map({
                            'name': rule_name,
                            'roles': sorted(set(static_roles)),
                            'derivedRoles': sorted(set(derived_roles)),
                            'actions': actions,
                            'effect': 'EFFECT_ALLOW',
                        }, commented)
                        if not static_roles:
                            rule.pop('roles')
                        if not derived_roles:
                            rule.pop('derivedRoles')
                        condition = self._condition(rule_conditions)
                        if condition:
                            rule['condition'] = condition

                        rules.append(rule)
                        description = to_clause.get('description') or access_block.get('description')
                        _add_rule_comment(rules, len(rules) - 1, rule_name, description)

        definitions = []
        for (role, expr), name in sorted(derived_by_key.items(), key=lambda item: item[1]):
            definitions.append(_policy_map({
                'name': name,
                'parentRoles': [role],
                'condition': self._condition([expr]),
            }, commented))

        return {
            'derivedRoleSet': f'udm_{sanitize_filename(self.filename.stem).replace("-", "_")}_contexts',
            'derivedRoles': _policy_seq(definitions, commented),
            'resources': resources,
        }

    def _derived_roles_document(self, definitions, *, commented=False):
        return _policy_map({
            'apiVersion': 'api.cerbos.dev/v1',
            'description': f'Automatically generated context roles from {self.filename.name}.',
            'derivedRoles': _policy_map({
                'name': f'udm_{sanitize_filename(self.filename.stem).replace("-", "_")}_contexts',
                'definitions': definitions,
            }, commented),
            'metadata': {'sourceFile': str(self.filename), 'annotations': {}},
        }, commented)

    @staticmethod
    def _is_context_position(position):
        return isinstance(position, str) and position.startswith('context=')

    def _derived_role_name(self, role, position, used_names):
        scope = _SCOPES.get(position[0], 'base')
        source = sanitize_filename(self.filename.stem).replace('-', '_')
        role_name = sanitize_filename(role).replace('-', '_')
        base = f'{source}_{role_name}_position_{scope}'
        name = base
        counter = 2
        while name in used_names:
            name = f'{base}_{counter}'
            counter += 1
        return name

    def _expand_object_types(self, object_type):
        if object_type != '*':
            return [object_type]
        if univention is not None:
            return sorted(univention.admin.modules.modules)
        return ['*']

    @staticmethod
    def _cel_string(value):
        return yaml.safe_dump(value, default_style='"').strip()

    def _position_to_cel(self, role, raw_scope, raw_position):
        scope = _SCOPES.get(raw_scope, 'base')
        position = self._format_position(raw_position)

        if isinstance(position, str) and position.startswith('context='):
            _, _, context = position.partition('context=')
            context_key = self._context_key(context)
            pos = f'cr.{context_key}'
            role_match = f'cr.role == {self._cel_string(role)}'
            dn_match = self._dn_position_scope_expr(scope, pos)
            return f'{CONTEXT_ROLES}.exists(cr, {role_match} && {dn_match})'

        return self._dn_position_scope_expr(scope, self._cel_string(position))

    @staticmethod
    def _context_key(context):
        if context == 'udm:contexts:position':
            return 'position'
        raise DSLSyntaxError(f'Unsupported context: {context}')

    @staticmethod
    def _dn_position_scope_expr(scope, position_expr):
        # UDM exposes request.resource.attr.position as the parent DN / current
        # container of the target. This avoids slicing the object RDN from the DN
        # for the common base/onelevel comparison.
        if scope in {'base', 'one'}:
            return f'{RESOURCE_POSITION} == {position_expr}'
        if scope == 'subtree':
            return f'({RESOURCE_POSITION} == {position_expr} || {RESOURCE_POSITION}.endsWith("," + {position_expr}))'
        if scope == 'children':
            return f'({RESOURCE_POSITION} != {position_expr} && {RESOURCE_POSITION}.endsWith("," + {position_expr}))'
        raise DSLSyntaxError(f'Unsupported position scope: {scope}')

    @staticmethod
    def _format_position(position):
        if isinstance(position, str) and not position.startswith('context='):
            return position.format_map(_SafeFormatDict(ucr))
        return position

    def _grant_to_actions(self, grant):
        if 'actions' in grant:
            actions = set(grant.get('actions', []))
            if '*' in actions:
                actions = set(ACTIONS)
            elif 'read' in actions:
                actions.add('search')
            return sorted([udm_object_action(act) for act in actions], key=self._action_sort_key)

        properties = grant['properties']
        permissions = grant['permission'].split(',') if isinstance(grant['permission'], str) else grant['permission']
        permissions = set(permissions)
        if '*' in permissions:
            permissions = set(PERMISSIONS)
        if 'read' in permissions:
            permissions.add('search')
        if 'write' in permissions:
            permissions.update({'read', 'search'})

        actions = {
            udm_property_action_wildcards(prop, permission) if prop == '*' else udm_property_action(prop, permission)
            for prop in properties
            for permission in permissions
        }
        return sorted(actions, key=self._action_sort_key)

    @staticmethod
    def _action_sort_key(action):
        if action.startswith('udm:property:'):
            _, _, prop, permission = action.split(':', 3)
            return (1, prop, SORT_PRIO['permission'].get(permission, permission))
        if action.startswith('udm:object:'):
            act = action.rsplit(':', 1)[-1]
            return (0, SORT_PRIO['actions'].get(act, act), act)
        return (2, action)

    @staticmethod
    def _values_to_cel(expr, prop):
        replacements = {
            '$oldValue$': f'request.resource.attr.properties["{prop}"]',
            '$newValue$': f'request.resource.attr.new.properties["{prop}"]',
            '$value$': f'request.resource.attr.properties["{prop}"]',
            '$old$': 'request.resource.attr.properties',
            '$new$': 'request.resource.attr.new.properties',
        }
        for name, replacement in replacements.items():
            # expr = re.sub(rf'\b{re.escape(name)}\b', replacement, expr)
            expr = expr.replace(name, replacement)
        return expr

    @staticmethod
    def _condition(exprs):
        exprs = [expr for expr in exprs if expr]
        if not exprs:
            return None
        if len(exprs) == 1:
            return {'match': {'expr': exprs[0]}}
        return {'match': {'all': {'of': [{'expr': expr} for expr in exprs]}}}

    def _unique_rule_name(self, base, used_names, actions, object_type):
        # FIXME: this is not unique accross multiple filenames/configurations
        if not base:
            prefix = self.filename.stem
            suffix = '-'.join(actions)
            ot = 'all-udm-modules' if object_type == '*' else object_type.replace('/', '-')
            base = f'{prefix}-{ot}-{suffix}'
        base = re.sub(r'[^a-zA-Z0-9_-]+', '-', base).strip('-') or 'rule'
        name = base
        counter = 2
        while name in used_names:
            name = f'{base}-{counter}'
            counter += 1
        used_names.add(name)
        return name


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    parser.add_argument('--compose', action='store_true')
    parser.add_argument('--convert', action='store_true')
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--output-dir', default=POLICY_ROOT)
    parser.add_argument('--unstrict', action='store_true')
    args = parser.parse_args()

    conf = UDMAuthorizationConfig(args.config, strict=not args.unstrict)
    conf.parse()
    if args.compose:
        print(conf.compose())
    if args.convert:
        print(conf.to_yaml())
    if args.write:
        for path in conf.write_files(args.output_dir):
            print(path)
