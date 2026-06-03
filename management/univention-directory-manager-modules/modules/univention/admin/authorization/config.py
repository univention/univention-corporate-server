#!/usr/bin/python3
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
A domain specific language (DSL) for UDM access rules
inspired by LDAP ACLs
realized with extended BNF grammar and a LALR (Look-Ahead Left <- Right) Parser
and compiled to Cerbos role policies.
"""

import ast
import copy
import io
import logging
import re
import sys
from pathlib import Path

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
        if by['role'].count(':') != 2:
            raise DSLSyntaxError('role: must contain two ":"', (self.__filename, 0, 0, by['role']))

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
    """UDM DSL compiler that emits Cerbos rolePolicy documents."""

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
        """Return all generated Cerbos role policies as a multi-document YAML stream."""
        documents = self.to_role_policies(commented=True)
        if not documents:
            return ''
        return _dump_yaml_all(documents, commented=True)

    def write_files(self, output_dir=None):
        """
        Write generated role policies to ``generated/roles`` below ``output_dir``.

        Returns the written file paths. The default output root is the Cerbos/UDM
        policy directory used by the bootstrap script.
        """
        root = Path(output_dir or POLICY_ROOT)
        role_dir = root / 'generated' / self.filename.stem / 'roles'
        role_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for doc in self.to_role_policies(commented=True):
            role = doc['rolePolicy']['role']
            path = role_dir / f'{sanitize_filename(role)}.yaml'
            path.write_text(_dump_yaml(doc, commented=True))
            paths.append(path)
        return paths

    def to_role_policies(self, *, commented=False):
        # if self.parsed.get('conditions'):
        #     names = ', '.join(cond['name'] for cond in self.parsed['conditions'])
        #     print(f'Warning: Deprecated condition blocks are ignored for Cerbos output: {names}', file=sys.stderr)

        named_conditions = {}
        for cond in self.parsed['conditions']:
            named_conditions[cond['name']] = cond['expr']

        policies = {}
        used_names = {}
        for access_block in self.parsed['rules']:
            roles = sorted({role['role'] for role in access_block.get('by', [])})
            for to_clause in access_block.get('to', []):
                for role in roles:
                    rules = policies.setdefault(role, _policy_map({
                        'apiVersion': 'api.cerbos.dev/v1',
                        'rolePolicy': _policy_map({
                            'version': 'default',
                            'role': role,
                            'rules': _policy_seq([], commented),
                        }, commented),
                    }, commented))['rolePolicy']['rules']

                    used = used_names.setdefault(role, set())
                    for object_type in self._expand_object_types(to_clause['objecttype']):
                        conditions = []
                        if to_clause.get('position'):
                            conditions.append(self._position_to_cel(role, *to_clause['position']))
                        if_cond = to_clause.get('if')
                        if if_cond:
                            conditions.append(named_conditions.get(if_cond, if_cond))

                        actions = []
                        for grant in to_clause.get('grant', []):
                            actions.extend(self._grant_to_actions(grant))
                            if grant.get('values'):
                                prop = grant['properties'][0]
                                conditions.append(self._values_to_cel(grant['values'], prop))

                        rule = _policy_map({
                            'resource': udm_resource_kind(object_type) if object_type != '*' else '*',  # TODO: check if '*' or 'udm:*' is allowed
                            'allowActions': actions,
                        }, commented)

                        condition = self._condition(conditions)
                        if condition:
                            rule['condition'] = condition

                        rules.append(rule)

                        rule_name = self._unique_rule_name(used, to_clause, actions, object_type)
                        description = to_clause.get('description') or access_block.get('description')
                        # rule.yaml_set_start_comment(description, indent=0)
                        # _add_rule_comment(rule, 0, rule_name, description)
                        _add_rule_comment(rules, len(rules) - 1, rule_name, description)

        return [policies[role] for role in sorted(policies)]

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
            expr = re.sub(rf'\b{re.escape(name)}\b', replacement, expr)
        return expr

    @staticmethod
    def _condition(exprs):
        exprs = [expr for expr in exprs if expr]
        if not exprs:
            return None
        if len(exprs) == 1:
            return {'match': {'expr': exprs[0]}}
        return {'match': {'all': {'of': [{'expr': expr} for expr in exprs]}}}

    @staticmethod
    def _unique_rule_name(used_names, to_clause, actions, object_type):
        base = to_clause.get('name')
        if not base:
            suffix = '-'.join(actions)
            ot = 'all-udm-modules' if object_type == '*' else object_type.replace('/', '-')
            base = f'{ot}-{suffix}'
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
