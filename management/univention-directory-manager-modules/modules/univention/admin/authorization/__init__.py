#!/usr/bin/python3
#
# Univention Directory Manager
#
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Authorization for UDM access."""

from logging import getLogger

import univention.admin.modules
import univention.admin.types
from univention.admin import configRegistry
from univention.admin.uexceptions import permissionDenied
from univention.authorization.authorization import LocalGuardianAuthorizationClient


__all__ = ('Authorization',)

log = getLogger('ADMIN').getChild(__name__)

LDAP_BASE = configRegistry['ldap/base']
ROLE_CACHE_SIZE = 1000


def auth_log(action, actor, target, **kwargs):
    msg = f'{action} by {actor["id"]} to {target.get("id")} not allowed'
    if kwargs:
        extra = '; '.join(f'{k}={v!r}' for k, v in kwargs.items())
        msg = f'{msg}: {extra}'
    log.debug('%s', msg % kwargs)


def get_user(lo, user_dn: str):
    data = lo.authz_connection.get(user_dn, attr=['univentionObjectType'])
    modname = data.get('univentionObjectType')
    if not modname:
        return

    mod = univention.admin.modules.get(modname[0].decode('UTF-8'))
    obj = mod.object(None, lo, None, user_dn)
    obj.open()
    return obj


def get_user_roles(obj) -> list[str]:
    if hasattr(obj, 'open_guardian'):
        obj.open_guardian()
    role_set = set(obj.get('guardianInheritedRoles', []) + obj.get('guardianRoles', []))
    return role_set


def _san_module(module):
    return module.replace('/', '-')


def _san_property(prop):
    return prop.lower()


class Authorization:
    """Check authorization via access control lists"""

    global_enabled = False
    engine = None
    get_privileged_connection = lambda: None  # noqa: E731
    _user_roles_cache = {}

    @classmethod
    def enable(cls, get_privileged_connection):
        """Enables ACL checking globally if the running service supports it"""
        cls.global_enabled = True
        cls.get_privileged_connection = get_privileged_connection

    @classmethod
    def inject_ldap_connection(cls, user_connection, metadata=None):
        """Extends the user connection to get admin powers and store metadata per connection"""
        if cls.global_enabled:
            user_connection.authz.enabled = True
            user_connection.metadata = metadata
        return user_connection

    @classmethod
    def get_authz_connection(cls, lo):
        if cls.global_enabled:
            return cls.get_privileged_connection()
        return lo

    @property
    def lo(self):
        return self.__class__.get_privileged_connection()

    def __init__(self):
        self.enabled = False
        if self.engine is None:
            self.__class__.engine = LocalGuardianAuthorizationClient('/var/lib/univention-directory-manager-modules/guardian/')

    @classmethod
    def clear_caches(cls):
        if cls.engine:
            cls.engine.reload()
        cls._user_roles_cache.clear()

    @classmethod
    def _get_cached_actor(cls, lo):
        actor_dn = lo.binddn
        # FIXME: memory leak, use weakref.ref() ?
        actor = get_user(cls.get_privileged_connection(), actor_dn)
        if hasattr(lo, 'actor_roles') and lo.actor_roles is not None:
            return lambda: (actor, lo.actor_roles)
        return lambda: (actor, get_user_roles(actor))
        # FIXME: don't cache actor roles as we don't know when to invalidate the cache. Roles of groups can be changed at any time.
        if cls._user_roles_cache.get(actor_dn) is None:
            cls._user_roles_cache[actor_dn] = (actor, get_user_roles(actor))
        return lambda: cls._user_roles_cache[actor_dn]

    # @functools.lru_cache(maxsize=ROLE_CACHE_SIZE)
    def _get_cached_roles(self, lo, dn):
        user = get_user(lo, dn)
        if not user:
            return []
        return get_user_roles(user)

    def is_receive_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True

        mod = _san_module(obj.module)
        actor, targets = self._get_actor_and_targets(obj.lo, obj)
        allowed = self._check_permissions(
            actor,
            targets,
            *self._get_extras({mod}),
            targeted_permissions_to_check=[f'udm:{mod}:read'],
        )
        if not allowed:
            auth_log('read', actor, targets[0])
            if raise_exception:
                raise permissionDenied()

        return allowed

    def filter_object_properties(self, obj):
        return self.filter_search_results(obj.lo, [obj])[0]

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
                'roles': self._get_target_roles(module, dn),
                'attributes': {
                    'dn': dn,
                    'id': dn,
                    'objectType': module,
                    'position': self.lo.parentDn(dn) or LDAP_BASE,
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
            self._get_targets(lo, None, target_obj)
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
            *self._get_extras({x[0] for x in results}),
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

            mod = _san_module(module)

            if not {f'udm:{mod}:read', f'udm:{mod}:search'} & target_permissions['permissions']:
                auth_log('search', actor, {'id': target_permissions['target_id']})
                continue

            readable_attributes = self._get_readable_properties(target_permissions['permissions'], mod, all_properties)
            filtered.append((result, module, readable_attributes))

        return filtered

    def is_create_allowed(self, obj, raise_exception=True):
        if self.enabled:
            # is_create_allowed is called to early, so that we have to compute the LDAP DN
            obj.ready()  # all required properties / DN identifying property must be set
            obj.dn = obj._ldap_dn()
        return self._is_write_action_allowed('create', obj, raise_exception=raise_exception)

    def is_modify_allowed(self, obj, raise_exception=True):
        return self._is_write_action_allowed('modify', obj, raise_exception=raise_exception)

    def is_rename_allowed(self, obj, raise_exception=True):
        return self._is_write_action_allowed('rename', obj, raise_exception=raise_exception)

    def is_move_allowed(self, obj, dest, raise_exception=True):
        if not self.enabled:
            return True

        # FIXME: deepcopy is expensive
        import copy

        moved_obj = copy.deepcopy(obj)
        moved_obj.dn = dest

        mod = _san_module(obj.module)
        actor, targets = self._get_actor_and_targets(obj.lo, obj, moved_obj)
        if not self._check_permissions(
            actor,
            targets,
            *self._get_extras({mod}),
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
        actor, targets = self._get_actor_and_targets(obj.lo, obj, None)
        if not self._check_permissions(
            actor,
            targets,
            *self._get_extras({mod}),
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

    def is_report_create_allowed(self, lo, module, report_type, raise_exception=True):
        if not self.enabled:
            return True
        mod = _san_module(module)
        actor = self._get_actor(lo)
        if not self._check_permissions(
            actor,
            [{
                'old_target': {
                    'id': report_type,
                    'roles': [],
                    'attributes': {
                        'objectType': module,
                        # 'position': obj.lo.parentDn(obj.old_dn) or LDAP_BASE if old else obj.lo.parentDn(obj.dn) or LDAP_BASE,
                    },
                },
                'new_target': self._empty_target(),
            }],
            *self._get_extras({mod}),
            targeted_permissions_to_check=[f'udm:{mod}:report-create'],
        ):
            auth_log('report-create', actor, {})
            if raise_exception:
                raise permissionDenied()
            return False
        return True

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

        actor, targets = self._get_actor_and_targets(obj.lo, obj, obj)
        allowed, permissions_result = self._get_and_check_permissions(
            actor,
            targets,
            *self._get_extras({mod}),
            targeted_permissions_to_check=[f'udm:{mod}:{action}'],
        )

        writeable_attributes = self._get_writeable_properties(
            permissions_result['general_permissions'] | permissions_result['target_permissions'][0]['permissions'], mod, set(obj.descriptions),
        )
        all_allowed = allowed and self._is_all_writeable(writeable_attributes, obj.module, changed_properties)
        if not all_allowed:
            auth_log(action, actor, targets[0], general=allowed, changed_properties=changed_properties)
            if raise_exception:
                raise permissionDenied()
        return all_allowed

    def _is_readable(self, readable_attributes, module, prop):
        return _san_property(prop) in readable_attributes

    def _is_writable(self, writeable_attributes, module, prop):
        return _san_property(prop) in writeable_attributes

    def _is_all_writeable(self, writeable_attributes, module, changed_props):
        return all(self._is_writable(writeable_attributes, module, prop) for prop in changed_props)

    def _get_readable_properties(self, permissions, module, all_properties):
        readable = {}
        unreadable = {}
        for mod, perms in self._parse_permissions(permissions).items():
            for action in ('write', 'read'):
                readable.setdefault(mod, set()).update(perms.get(action, set()))
            for action in ('none', 'writeonly'):
                unreadable.setdefault(mod, set()).update(perms.get(action, set()))

        props = readable.get(module, set())
        if '*' in props:
            props |= {_san_property(p) for p in all_properties}
            props -= {'*'}
        props -= unreadable.get(module, set())
        return props

    def _get_writeable_properties(self, permissions, module, all_properties):
        writeable = {}
        unwriteable = {}
        for mod, perms in self._parse_permissions(permissions).items():
            for action in ('write',):
                writeable.setdefault(mod, set()).update(perms.get(action, set()))
            for action in ('none', 'readonly'):
                unwriteable.setdefault(mod, set()).update(perms.get(action, set()))

        props = writeable.get(module, set())
        if '*' in props:
            props |= {_san_property(p) for p in all_properties}
            props -= {'*'}
        props -= unwriteable.get(module, set())
        return props

    def _parse_permissions(self, permissions):
        parsed = {}
        for permission in permissions:
            app_name, mod, perm = permission.split(':', 2)
            if app_name != 'udm' or not mod:
                continue
            action, _, prop = perm.partition('-property-')
            if not _:
                continue
            if action in ('write', 'writeonly', 'read', 'readonly', 'none'):
                parsed.setdefault(mod, {}).setdefault(action, set()).add(prop)
        return parsed

    def _get_targets(self, lo, old_target, new_target=None):
        return {
            'old_target': self._get_target(old_target, old=True) if old_target is not None and old_target.exists() else self._empty_target(),
            'new_target': self._get_target(new_target) if new_target is not None else self._empty_target(),
        }

    def _get_actor_and_targets(self, lo, old_target, new_target=None):
        return self._get_actor(lo), [self._get_targets(lo, old_target, new_target)]

    def _get_extras(self, modules):
        contexts = []
        namespaces = [f'udm:{_san_module(mod)}' for mod in modules]
        extra_request_data = {
            'ldap_base': LDAP_BASE,
        }
        return contexts, namespaces, extra_request_data

    def _get_actor(self, lo):
        actor, actor_roles = self._get_cached_actor(lo)()
        return {
            'id': actor.dn,
            'roles': actor_roles,
            'attributes': self._get_representation(actor),
        }

    def _get_target(self, obj, old=False):
        return {
            'id': obj.old_dn if old else obj.dn,
            'roles': self._get_target_roles(obj.module, obj.old_dn),
            'attributes': self._get_representation(obj, old),
        }

    def _get_target_roles(self, module, dn):
        if module != 'users/user':
            return []
        return self._get_cached_roles(self.lo, dn)

    def _empty_target(self):
        return {'id': '', 'roles': [], 'attributes': {}}

    def _get_representation(self, obj, old=False):
        """Get a represenation of the object like UDM REST API would serve it"""
        return {
            'dn': obj.old_dn if old else obj.dn,
            'id': None,
            'objectType': obj.module,
            'position': obj.lo.parentDn(obj.old_dn) or LDAP_BASE if old else obj.lo.parentDn(obj.dn) or LDAP_BASE,
            'properties': self._decode_properties(obj, obj.oldinfo) if old else self._decode_properties(obj, obj.info),
            'options': self._decode_options(obj, obj.old_options) if old else self._decode_options(obj, obj.options),
            'policies': None,
            'uuid': None,
        }

    def _decode_properties(self, obj, props):
        return {
            key: univention.admin.types.TypeHint.detect(obj.descriptions[key], key).decode_json(value)
            for key, value in props.items()
        }

    def _decode_options(self, obj, options):
        mod = univention.admin.modules.get(obj.module)
        return {
            opt: opt in options
            for opt in
            getattr(mod, 'options', {})
            if opt != 'default'
        }
