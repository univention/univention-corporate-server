#!/usr/bin/python3
#
# Univention Directory Manager
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2025 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
"""Authorization for UDM access."""

from logging import getLogger

import univention.admin.modules
from univention.admin import configRegistry
from univention.admin.guardian import GuardianRuleEvaluation
from univention.admin.uexceptions import permissionDenied


log = getLogger('ADMIN').getChild(__name__)

ldap_base = configRegistry['ldap/base']


def auth_log(action, actor, target, **kwargs):
    msg = f'{action} by {actor["id"]} to {target.get("id")} not allowed'
    if kwargs:
        extra = '; '.join(f'{k}={v!r}' for k, v in kwargs.items())
        msg = f'{msg}: {extra}'
    log.debug('%s', msg % kwargs)


def get_user(lo, user_dn: str) -> None:
    data = lo.authz_connection.get(user_dn, attr=['univentionObjectType'])
    try:
        mod = univention.admin.modules.get(data['univentionObjectType'][0].decode('UTF-8'))
    except KeyError as exc:
        raise KeyError(str(exc), user_dn)
    obj = mod.object(None, lo, None, user_dn)
    obj.open()
    return obj


def get_user_roles(obj) -> None:
    if hasattr(obj, 'open_guardian'):
        obj.open_guardian()
    role_set = set(obj.get("guardianInheritedRoles", []) + obj.get("guardianRoles", []))
    return role_set


def _san_module(module):
    return module.replace('/', '-')


def _san_property(prop):
    return prop.lower()


class Authorization:
    """Check authorization via access control lists"""

    enabled = False
    get_privileged_connection = lambda: None  # noqa: E731
    _cache_univention_object_identifier = {}
    _user_roles_cache = {}

    @classmethod
    def enable(cls, get_privileged_connection):
        """Enables ACL checking globally if the running service supports it"""
        cls.enabled = True
        cls.get_privileged_connection = get_privileged_connection

    @classmethod
    def inject_ldap_connection(cls, user_connection, metadata=None):
        if cls.enabled:
            user_connection.metadata = metadata
        return user_connection

    @classmethod
    def get_authz_connection(cls, lo):
        if cls.enabled:
            lo_admin = cls.get_privileged_connection()
            if cls._cache_univention_object_identifier.get(lo.binddn) is None:
                cls._cache_univention_object_identifier[lo.binddn] = lo_admin.lo.get_univention_object_identifier(lo.binddn)
            lo_admin.lo.set_univention_object_identifier(cls._cache_univention_object_identifier[lo.binddn])
            return lo_admin
        return lo

    @property
    def lo(self):
        return self.__class__.get_privileged_connection()

    def __init__(self):
        self.engine = GuardianRuleEvaluation()

    def _get_cached_user_roles(self, lo):
        actor_dn = lo.binddn
        # FIXME: memory leak, use weakref.ref() ?
        actor = get_user(self.lo, actor_dn)
        if self._user_roles_cache.get(actor_dn) is None:
            self._user_roles_cache[actor_dn] = (actor, get_user_roles(actor))
        return lambda: self._user_roles_cache[actor_dn]

    def is_receive_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True

        mod = _san_module(obj.module)
        actor, targets = self._get_targets(obj.lo, obj)
        allowed = self._check_permissions(
            actor,
            targets,
            *self._get_extras(),
            targeted_permissions_to_check=[f'udm:{mod}:read'],
        )
        if not allowed:
            auth_log('read', actor, targets[0])
            if raise_exception:
                raise permissionDenied()

        # TODO: strip out unreadable properties?
        return allowed

    def filter_search_results_dn(self, lo, results):
        if not self.enabled:
            return results

        # TODO: how could we realize filterting without receiving the object
        # TODO: skip authorization in get_object() ?
        # FIXME: remove this performance intensive search!!!
        results = [univention.admin.objects.get_object(lo, dn) for dn in results]
        results = [x for x in results if x is not None]  # cn=admin and others is not a UDM object

        filtered = self.filter_search_results(lo, results)
        return [obj.dn for obj in filtered]

    def filter_search_results_attrs(self, lo, results):
        if not self.enabled:
            return results

        targets = []
        results_ext = []
        for result in results:
            dn, attrs = result
            module = attrs['univentionObjectType'][0].decode('UTF-8')  # cn=admin and others is not a UDM object
            mod = univention.admin.modules.get(module)
            mapping = mod.mapping
            props = {}
            for attr in list(attrs):
                prop = mapping.unmapName(attr)
                props[prop] = attrs[attr]
            target = {
                'id': dn,
                'roles': [],  # TODO: get_user_roles(get_user(self.lo, dn)),
                'attributes': {
                    'dn': dn,
                    'id': dn,
                    'objectType': module,
                    'position': self.lo.parentDn(dn) or ldap_base,
                    'properties': props,
                    # 'options': ...,
                    'policies': None,
                    'uuid': None,
                },
            }
            targets.append({'old_target': target, 'new_target': self._empty_target()})
            results_ext.append((
                module, dn, result, set(mod.property_descriptions),

            ))

        filtered = self._filter_search_results(lo, results_ext, targets)
        response = []
        for result, module, readable_attributes in filtered:
            _, attrs = result
            for attr in list(attrs):
                prop = univention.admin.modules.get(module).mapping.unmapName(attr)
                if not self._is_readable(readable_attributes, module, prop):  # FIXME: is module correct?
                    attrs.pop(attr)
            response.append(result)

        return response

    def filter_search_results(self, lo, results):
        if not self.enabled:
            return results
        targets = [
            # {'old_target': self._get_target(target_obj, old=True) if target_obj.exists() else self._empty_target(), 'new_target': self._get_target(target_obj)}
            {'old_target': self._get_target(target_obj), 'new_target': self._empty_target()}
            for target_obj in results
        ]
        results_ext = [
            (result.module, result.dn, result, set(result.descriptions))
            for result in results
        ]
        filtered = self._filter_search_results(lo, results_ext, targets)

        response = []
        for result, module, readable_attributes in filtered:
            for prop in list(result.info):
                if not self._is_readable(readable_attributes, module, prop):
                    # TODO: remove from oldattr
                    # FIXME: what if the object is open()ed afterwards?
                    result.info.pop(prop)
                    result.oldinfo.pop(prop, None)
            response.append(result)

        return response

    def _filter_search_results(self, lo, results, targets):
        if not results:
            return results  # FIXME: less error prone but allows side channel timing attacks

        actor = self._get_actor(lo)
        allowed, permissions_result = self._get_and_check_permissions(
            actor,
            targets,
            *self._get_extras(),
            # general_permissions_to_check=[f'udm:{mod}:read'],  # FIXME: no general permission can be granted, as the object type might differ
        )
        if not permissions_result['actor_has_all_general_permissions']:
            auth_log('search', actor, {'id': 'multiple targets'}, general=allowed)
            return []
            # raise permissionDenied()

        filtered = []
        for i, (module, dn, result, all_properties) in enumerate(results):
            target_permissions = permissions_result['target_permissions'][i]
            assert target_permissions['target_id'] == dn, (target_permissions['target_id'], dn)  # TODO: replace with UUID

            if not {f'udm:{_san_module(module)}:read', f'udm:{_san_module(module)}:search'} & target_permissions['permissions']:
                auth_log('search', actor, {'id': target_permissions['target_id']})
                continue

            readable_attributes = self._get_readable_properties(target_permissions['permissions'], all_properties)
            filtered.append((result, module, readable_attributes))

        return filtered

    def is_create_allowed(self, obj, raise_exception=True):
        if self.enabled:
            obj.dn = obj._ldap_dn()
        return self._is_write_action_allowed('create', obj, raise_exception=raise_exception)

    def is_modify_allowed(self, obj, raise_exception=True):
        return self._is_write_action_allowed('modify', obj, raise_exception=True)

    def is_rename_allowed(self, obj, raise_exception=True):
        return self._is_write_action_allowed('rename', obj)

    def is_move_allowed(self, obj, dest, raise_exception=True):
        if not self.enabled:
            return True

        # FIXME: deepcopy is expensive
        import copy
        moved_obj = copy.deepcopy(obj)
        moved_obj.dn = dest

        mod = _san_module(obj.module)
        for _obj in [obj, moved_obj]:
            actor, targets = self._get_targets(obj.lo, _obj)
            if not self._check_permissions(
                actor,
                targets,
                *self._get_extras(),
                targeted_permissions_to_check=[f'udm:{mod}:move'],
            ):
                auth_log('move', actor, targets[0])
                if raise_exception:
                    raise permissionDenied()
                return False
        return True

    def is_remove_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return
        mod = _san_module(obj.module)
        actor, targets = self._get_targets(obj.lo, obj)
        if not self._check_permissions(
            actor,
            targets,
            *self._get_extras(),
            targeted_permissions_to_check=[f'udm:{mod}:remove'],
        ):
            auth_log('remove', actor, targets[0])
            if raise_exception:
                raise permissionDenied()
            return False
        return True

    def object_exists(self, obj):
        if not self.is_receive_allowed(obj, raise_exception=False):
            raise univention.admin.uexceptions.noObject(obj.dn)

    def is_reports_type_query_allowed(self, lo, module):
        if not self.enabled:
            return
        mod = _san_module(module)
        actor = self._get_actor(lo)
        if not self._check_permissions(
            actor,
            [],
            *self._get_extras(),
            general_permissions_to_check=[
                f'udm:{mod}:reports-type-query',
                f'udm:{mod}:report-create',  # TODO: check already?
            ],
        ):
            auth_log('report-query', actor, {})
            raise permissionDenied()

    def is_report_create_allowed(self, lo, module, report_type):
        if not self.enabled:
            return
        mod = _san_module(module)
        actor = self._get_actor(lo)
        if not self._check_permissions(
            actor,
            [],
            *self._get_extras(),
            general_permissions_to_check=[f'udm:{mod}:report-create'],
        ):
            auth_log('report-create', actor, {})
            raise permissionDenied()

    def _get_and_check_permissions(self, *args, **kwargs):
        result = self.engine.get_and_check_permissions(*args, **kwargs)
        if not kwargs.get('general_permissions_to_check'):
            result['actor_has_all_general_permissions'] = True
        if not kwargs.get('targeted_permissions_to_check'):
            result['actor_has_all_targeted_permissions'] = True
        return result['actor_has_all_general_permissions'] and result['actor_has_all_targeted_permissions'], result

    def _check_permissions(self, *args, **kwargs):
        result = self.engine.check_permissions(*args, **kwargs)
        if not kwargs.get('general_permissions_to_check'):
            result['actor_has_all_general_permissions'] = True
        if not kwargs.get('targeted_permissions_to_check'):
            result['actor_has_all_targeted_permissions'] = True
        return result['actor_has_all_general_permissions'] and result['actor_has_all_targeted_permissions']

    def _is_write_action_allowed(self, action, obj, raise_exception=True):
        if not self.enabled:
            return
        mod = _san_module(obj.module)
        changed_properties = [
            prop
            for prop in obj.descriptions
            if obj.has_property(prop) and obj.hasChanged(prop)
        ]

        if not changed_properties:
            return  # TODO: decode carefully: if nothing changed, allow it?

        # required_modify_permissions = [
        #     f'udm:{mod}:write-property-{_san_property(prop)}'
        #     for prop in changed_properties
        # ]
        actor, targets = self._get_targets(obj.lo, obj)
        allowed, permissions_result = self._get_and_check_permissions(
            actor,
            targets,
            *self._get_extras(),
            targeted_permissions_to_check=[f'udm:{mod}:{action}'],  # + required_modify_permissions,
        )

        writeable_attributes = self._get_writeable_properties(permissions_result['general_permissions'] | permissions_result['target_permissions'][0]['permissions'], set(obj.descriptions))
        all_allowed = allowed and self._is_all_writeable(writeable_attributes, obj.module, changed_properties)
        if not all_allowed:
            auth_log(action, actor, targets[0], general=allowed, changed_properties=changed_properties)
            if raise_exception:
                raise permissionDenied()
        return all_allowed

    def _is_readable(self, readable_attributes, module, prop):
        return _san_property(prop) in readable_attributes.get(module, [])

    def _is_writable(self, writeable_attributes, module, prop):
        return _san_property(prop) in writeable_attributes.get(module, [])

    def _is_all_writeable(self, writeable_attributes, module, changed_props):
        return all(self._is_writable(writeable_attributes, module, prop) for prop in changed_props)

    def _get_readable_properties(self, permissions, all_properties):
        readable = {}
        unreadable = {}
        for permission in permissions:
            app_name, mod, perm = permission.split(':', 2)
            if app_name != 'udm' or not mod:
                continue
            if perm.startswith('read-property-'):
                _, _, prop = perm.partition('read-property-')
                readable.setdefault(mod.replace('-', '/'), set()).add(prop)
            elif perm.startswith('none-property-'):
                _, _, prop = perm.partition('none-property-')
                unreadable.setdefault(mod.replace('-', '/'), set()).add(prop)
            elif perm.startswith('writeonly-property-'):
                _, _, prop = perm.partition('writeonly-property-')
                unreadable.setdefault(mod.replace('-', '/'), set()).add(prop)

        for modname, mod in readable.items():
            if '*' in mod:
                mod |= all_properties
            mod -= unreadable.get(modname, set())
        return readable

    def _get_writeable_properties(self, permissions, all_properties):
        writeable = {}
        unwriteable = {}
        for permission in permissions:
            app_name, mod, perm = permission.split(':', 2)
            if app_name != 'udm' or not mod:
                continue
            if perm.startswith('write-property-'):
                _, _, prop = perm.partition('write-property-')
                writeable.setdefault(mod.replace('-', '/'), set()).add(prop)
            elif perm.startswith('readonly-property-'):
                _, _, prop = perm.partition('readonly-property-')
                unwriteable.setdefault(mod.replace('-', '/'), set()).add(prop)
            elif perm.startswith('none-property-'):
                _, _, prop = perm.partition('none-property-')
                unwriteable.setdefault(mod.replace('-', '/'), set()).add(prop)

        for modname, mod in writeable.items():
            if '*' in mod:
                mod |= all_properties
            mod -= unwriteable.get(modname, set())
        return writeable

    def _get_targets(self, lo, target=None):
        actor = self._get_actor(lo)
        if target:
            targets = [{'old_target': self._get_target(target, old=True) if target.exists() else self._empty_target(), 'new_target': self._get_target(target)}]
        else:
            targets = []  # [{'old_target': self._empty_target(), 'new_target': self._empty_target()}]
        return actor, targets

    def _get_extras(self):
        contexts = []
        namespaces = []
        extra_request_data = {
            'ldap_base': ldap_base,
        }
        return contexts, namespaces, extra_request_data

    def _get_actor(self, lo):
        actor, actor_roles = self._get_cached_user_roles(lo)()
        return {
            'id': actor.dn,
            'roles': actor_roles,
            'attributes': self._get_representation(actor),
        }

    def _get_target(self, obj, old=False):
        return {
            'id': obj.old_dn if old else obj.dn,
            'roles': [],  # FIXME: get_user_roles(get_user(self.lo, obj.old_dn)),
            'attributes': self._get_representation(obj, old),
        }

    def _empty_target(self):
        return {'id': '', 'roles': [], 'attributes': {}}

    def _get_representation(self, obj, old=False):
        return {
            'dn': obj.old_dn if old else obj.dn,
            'id': None,
            'objectType': obj.module,
            'position': obj.lo.parentDn(obj.old_dn) or ldap_base if old else obj.lo.parentDn(obj.dn) or ldap_base,
            'properties': obj.oldinfo.copy() if old else obj.info.copy(),  # TODO: transform into UDM REST API representation
            'options': obj.old_options[:] if old else obj.options[:],  # TODO: transform into UDM REST API representation
            'policies': None,
            'uuid': None,
        }
