#!/usr/bin/python3
#
# Univention Directory Manager
#
# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""Authorization for UDM access."""

from dataclasses import asdict, dataclass, field
from typing import Any

import univention.admin.modules
import univention.admin.types
from univention.admin import configRegistry
from univention.admin.authorization.authorization_client import CerbosAuthorizationClient, Principal, Resource
from univention.admin.authorization.utils import udm_object_action, udm_property_action, udm_resource_kind
from univention.admin.guardian_roles import get_roles_from_ldap
from univention.admin.log import log
from univention.admin.uexceptions import permissionDenied


__all__ = ('Authorization',)

log = log.getChild(__name__)

LDAP_BASE = configRegistry['ldap/base']
ROLE_CACHE_SIZE = 1000


def auth_log(action, actor, target, **kwargs):
    log.debug('%s by %s to %s not allowed', action, actor.id, target.get('id'), **kwargs)


def get_user(lo, user_dn: str):
    data = lo.authz_connection.get(user_dn, attr=['*', '+'])
    modname = data.get('univentionObjectType')
    if not modname:
        return

    mod = univention.admin.modules.get(modname[0].decode('UTF-8'))
    obj = mod.object(None, lo, None, user_dn, None, data)
    obj.open()
    return obj


@univention.admin._ldap_cache(ttl=3600)
def get_object_type(lo, dn: str) -> str:
    # TODO: what to do if object_type is empty?
    return (lo.authz_connection.getAttr(dn, 'univentionObjectType') or [b''])[0].decode('UTF-8')


def get_user_roles(obj) -> list[str]:
    if hasattr(obj, 'open_guardian'):
        obj.open_guardian()
    role_set = set(obj.get('guardianInheritedRoles', []) + obj.get('guardianRoles', []))
    return role_set


@dataclass
class UDMObject:
    dn: str
    objectType: str
    position: str
    roles: set | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    policies: Any = None  # TODO: add policies? what for...
    uuid: str | None = None  # TODO: add univentionObjectIdentifier ?


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
            self.__class__.engine = CerbosAuthorizationClient()

    @classmethod
    def clear_caches(cls):
        cls._user_roles_cache.clear()

    @classmethod
    def _get_cached_actor(cls, lo):
        actor_dn = lo.binddn
        # FIXME: memory leak, use weakref.ref() ?
        actor = get_user(cls.get_privileged_connection(), actor_dn)
        if getattr(lo, 'actor_roles', None) is not None:
            return lambda: (actor, lo.actor_roles)
        return lambda: (actor, get_user_roles(actor))
        # FIXME: don't cache actor roles as we don't know when to invalidate the cache. Roles of groups can be changed at any time.
        if cls._user_roles_cache.get(actor_dn) is None:
            cls._user_roles_cache[actor_dn] = (actor, get_user_roles(actor))
        return lambda: cls._user_roles_cache[actor_dn]

    # @functools.lru_cache(maxsize=ROLE_CACHE_SIZE)
    def _get_cached_roles(self, lo, dn):
        return get_roles_from_ldap(self.lo, dn)

    def is_receive_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return True

        actor = self._get_actor(obj.lo)
        target = self._get_target(obj, old=True)
        allowed = self._check_actions(actor, target, [udm_object_action('read')])
        if not allowed:
            auth_log('read', actor, target)
            if raise_exception:
                raise permissionDenied()

        return allowed

    def filter_object_properties(self, obj):
        return self.filter_search_results(obj.lo, [obj])[0]

    def filter_search_results_dn(self, lo, results, context=None):
        if not self.enabled:
            return results

        # FIXME: This breaks ABAC, we just have a DN and create a dummy target without properties
        context = context or {}
        context['result_is_ldap_dn'] = True
        return self.filter_search_results(lo, results, context)

    def filter_search_results_attrs(self, lo, results):
        if not self.enabled:
            return results

        # FIXME: this is a best effort way which is very broken
        # 1. there could be any object in the result list, not just UDM representable objects
        # 2. the search attrs could only include a small subset, which wouldn't allow to pass all attributes to the authorization engine - breaking some conditions
        # 3. there could be attributes in the resultset which are not mapped by the UDM object - so there can't be a trueish result for "is readable" - should they be added (information leak) or removed (broken logic afterwards)?

        # TODO: complement with PlanResources
        # FIXME: needs to be chunked in 50er
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
                if prop:
                    props[prop] = mapping.unmapValue(attr, attrs[attr])

            attr = asdict(UDMObject(
                dn=dn,
                objectType=module,
                position=lo.parentDn(dn) or LDAP_BASE,
                roles=self._get_target_roles(module, dn),
                properties=props,  # FIXME: this is in raw UDM format, not UDM REST API
                options={},
            ))
            target = Resource(dn, udm_resource_kind(module), attr=attr)
            targets.append(target)
            results_ext.append((
                module, dn, result, set(mod.property_descriptions),

            ))

        filtered = self._filter_search_results(lo, results_ext, targets)
        response = []
        for result, module, readable_attributes in filtered:
            _, attrs = result
            for attr in list(attrs):
                prop = univention.admin.modules.get(module).mapping.unmapName(attr)
                if prop and not self._is_readable(readable_attributes, module, prop):  # FIXME: is module correct?
                    attrs.pop(attr)
            response.append(result)

        return response

    def filter_search_results(self, lo, results, context=None):
        if not self.enabled:
            return results
        if context and context.get('result_is_ldap_dn'):
            results = [
                (dn, context.get('module') or get_object_type(lo, dn)) for dn in results
            ]
            targets = [
                self._get_dn_target(dn, module, lo)
                for dn, module in results
            ]
            results_ext = [
                (module, dn, dn, set())
                for dn, module in results
            ]
        else:
            targets = [
                self._get_target(target_obj)
                for target_obj in results
            ]
            results_ext = [
                (result.module, result.dn, result, set(result.descriptions))
                for result in results
            ]
        filtered = self._filter_search_results(lo, results_ext, targets)

        response = []
        for result, module, readable_attributes in filtered:
            if not context or not context.get('result_is_ldap_dn'):
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
        actions = {udm_object_action('read'), udm_object_action('search')}
        for _, _, _, all_properties in results:
            actions.update(self._property_actions_for(all_properties, ('read', 'write', 'none', 'writeonly')))
        permissions_result = self._check_actions_by_targets(actor, targets, actions)

        filtered = []
        for i, (module, dn, result, all_properties) in enumerate(results):
            target_permissions = permissions_result[i]
            assert target_permissions['target_id'] == dn, (target_permissions['target_id'], dn)  # TODO: replace with UUID

            if not {udm_object_action('read'), udm_object_action('search')} & target_permissions['actions']:
                auth_log('search', actor, {'id': target_permissions['target_id']})
                continue

            readable_attributes = self._get_readable_properties(target_permissions['actions'], all_properties)
            filtered.append((result, module, readable_attributes))

        return filtered

    def is_create_allowed(self, obj, raise_exception=True):
        if self.enabled:
            # is_create_allowed is called to early, so that we have to compute the LDAP DN
            obj.ready()  # all required properties / DN identifying property must be set
            obj.dn = obj._ldap_dn()
        return self._is_write_action_allowed('create', obj, raise_exception=raise_exception)

    def is_restore_allowed(self, obj, raise_exception=True):
        return self._is_write_action_allowed('restore', obj, raise_exception=raise_exception)

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

        actor = self._get_actor(obj.lo)
        target = self._get_target_new(obj.lo, obj, moved_obj)
        if not self._check_actions(actor, target, [udm_object_action('move')]):
            auth_log('move', actor, target)
            if raise_exception:
                raise permissionDenied()
            return False
        return True

    def is_remove_allowed(self, obj, raise_exception=True):
        if not self.enabled:
            return
        actor = self._get_actor(obj.lo)
        target = self._get_target(obj, old=True)
        if not self._check_actions(actor, target, [udm_object_action('remove')]):
            auth_log('remove', actor, target)
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
        actor = self._get_actor(lo)
        attr = asdict(UDMObject(dn=report_type, objectType=module, position='', properties={'objectType': module}))
        target = Resource(report_type, udm_resource_kind(module), attr=attr)
        if not self._check_actions(actor, target, [udm_object_action('report-create')]):
            auth_log('report-create', actor, {})
            if raise_exception:
                raise permissionDenied()
            return False
        return True

    def _check_actions_by_targets(self, actor, targets, actions):
        actions = sorted(set(actions))
        with log.timing('Authorization operation', operation='check_actions_bulk', checking=actions):
            result = self.engine.check_actions_bulk(actor, targets, actions)
        return [
            {
                'target_id': item.target_id,
                'actions': set(item.actions),
            }
            for item in result
        ]

    def _check_actions(self, actor, target, actions):
        allowed_actions = self._check_actions_by_target(actor, target, actions)
        wanted = set(actions)
        return wanted <= allowed_actions

    def _check_actions_by_target(self, actor, target, actions):
        actions = sorted(set(actions))
        with log.timing('Authorization operation', operation='check_actions', checking=actions):
            return self.engine.check_actions(actor, target, actions).actions

    def _is_write_action_allowed(self, action, obj, raise_exception=True):
        if not self.enabled:
            return
        changed_properties = [
            prop
            for prop in obj.descriptions
            if obj.has_property(prop) and obj.hasChanged(prop)
        ]  # FIXME: we have a vulnerability if the logic of hasChanged is wrong. Then everyone can just change that property. but hasChanged might be overridden by single modules.

        actor = self._get_actor(obj.lo)
        target = self._get_target_new(obj.lo, obj, obj)
        actions = {udm_object_action(action)}
        actions.update(self._property_actions_for(changed_properties, ('write', 'none', 'readonly')))
        allowed_actions = self._check_actions_by_target(actor, target, actions)

        object_allowed = udm_object_action(action) in allowed_actions
        writeable_attributes = self._get_writeable_properties(allowed_actions, changed_properties)
        all_allowed = object_allowed and self._is_all_writeable(writeable_attributes, obj.module, changed_properties)
        if not all_allowed:
            auth_log(action, actor, target, general=object_allowed, changed_properties=changed_properties)
            if raise_exception:
                raise permissionDenied()
        return all_allowed

    def _is_readable(self, readable_attributes, module, prop):
        return prop in readable_attributes

    def _is_writable(self, writeable_attributes, module, prop):
        return prop in writeable_attributes

    def _is_all_writeable(self, writeable_attributes, module, changed_props):
        return all(self._is_writable(writeable_attributes, module, prop) for prop in changed_props)

    def _get_readable_properties(self, allowed_actions, all_properties):
        props = set()
        blocked = set()
        for prop in all_properties:
            if udm_property_action(prop, 'read') in allowed_actions or udm_property_action(prop, 'write') in allowed_actions:
                props.add(prop)
            if udm_property_action(prop, 'none') in allowed_actions or udm_property_action(prop, 'writeonly') in allowed_actions:
                blocked.add(prop)
        return props - blocked

    def _get_writeable_properties(self, allowed_actions, all_properties):
        props = set()
        blocked = set()
        for prop in all_properties:
            if udm_property_action(prop, 'write') in allowed_actions:
                props.add(prop)
            if udm_property_action(prop, 'none') in allowed_actions or udm_property_action(prop, 'readonly') in allowed_actions:
                blocked.add(prop)
        return props - blocked

    def _property_actions_for(self, properties, actions):
        return {
            udm_property_action(prop, action)
            for prop in properties
            for action in actions
        }

    def _get_actor(self, lo):
        actor, actor_roles = self._get_cached_actor(lo)()
        roles, role_contexts = self._normalize_actor_roles(actor_roles)
        attributes = self._get_representation(actor)
        if role_contexts:
            attributes['contextRoles'] = role_contexts
        return Principal(actor.dn, roles=set(roles), attr=attributes)

    def _normalize_actor_roles(self, actor_roles):
        roles = set()
        context_roles = []
        for raw_role in actor_roles:
            role, *context_parts = str(raw_role).split('&')
            roles.add(role)
            context_role = {'role': role}
            for context_part in context_parts:
                key, sep, value = context_part.partition('=')
                if not sep:
                    continue
                short_key = key.rsplit(':', 1)[-1]
                # Keep the compact key used by generated CEL expressions.
                # Additional context types can be exposed here later.
                context_role[short_key] = value
            if len(context_role) > 1:
                context_roles.append(context_role)
        return roles, context_roles

    def _get_target_new(self, lo, obj, new_target=None):
        attr = self._get_representation(obj, True)
        attr['roles'] = self._get_target_roles(obj.module, obj.old_dn)
        attr['new'] = self._get_representation(new_target, False)
        return Resource(obj.old_dn, udm_resource_kind(obj.module), attr=attr)

    def _get_target(self, obj, old=False):
        attr = self._get_representation(obj, old)
        attr['roles'] = self._get_target_roles(obj.module, obj.old_dn)
        return Resource(obj.old_dn if old else obj.dn, udm_resource_kind(obj.module), attr=attr)

    def _get_dn_target(self, dn, module, lo):
        attr = asdict(UDMObject(
            dn=dn,
            objectType=module,
            position=lo.parentDn(dn) or LDAP_BASE,
            roles=self._get_target_roles(module, dn),
            properties={},
            options={},
        ))
        return Resource(dn, udm_resource_kind(module), attr=attr)

    def _get_target_roles(self, module, dn):
        if module != 'users/user':
            return []
        return self._get_cached_roles(self.lo, dn)

    def _get_representation(self, obj, old=False):
        """Get a represenation of the object like UDM REST API would serve it"""
        return asdict(UDMObject(
            dn=obj.old_dn if old else obj.dn,
            objectType=obj.module,
            position=obj.lo.parentDn(obj.old_dn) or LDAP_BASE if old else obj.lo.parentDn(obj.dn) or LDAP_BASE,
            properties=self._decode_properties(obj, obj.oldinfo) if old else self._decode_properties(obj, obj.info),
            options=self._decode_options(obj, obj.old_options) if old else self._decode_options(obj, obj.options),
        ))

    def _decode_properties(self, obj, props):
        # FYI: this contains also the password hashes of users!
        props = {}
        for key, value in props.items():
            try:
                props[key] = univention.admin.types.TypeHint.detect(obj.descriptions[key], key).decode_json(value)
            except univention.admin.uexceptions.valueError as exc:
                log.error('Invalid user data', dn=obj.dn, error=exc)
            except Exception:
                log.exception('Invalid user data', dn=obj.dn)
        return props

    def _decode_options(self, obj, options):
        mod = univention.admin.modules.get(obj.module)
        return {
            opt: opt in options
            for opt in
            getattr(mod, 'options', {})
            if opt != 'default'
        }
