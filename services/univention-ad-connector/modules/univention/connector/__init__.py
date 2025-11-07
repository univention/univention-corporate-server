#!/usr/bin/python3
#
# Univention AD Connector
#  Basic class for the UCS connector part
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import collections
import copy
import logging
import os
import pickle  # noqa: S403
import pprint
import random
import re
import sqlite3 as lite
import string
import sys
from logging import getLogger
from types import FunctionType

import ldap
from ldap.controls.readentry import PostReadControl
from samba.dcerpc import misc
from samba.ndr import ndr_unpack

import univention.admin.modules
import univention.admin.objects
import univention.admin.uldap
import univention.debug as ud
import univention.logging
from univention.connector.adcache import ADCache
from univention.dn import DN
from univention.logging import Structured


log = Structured(getLogger("LDAP").getChild(__name__))

term_signal_caught = False

univention.admin.modules.update()

RE_NO_RESYNC = re.compile('^<NORESYNC(=.*?)?>;')


try:
    univention.admin.handlers.disable_ad_restrictions(disable=False)
except AttributeError:
    log.process('univention.admin.handlers.disable_ad_restrictions is not available')


def decode_guid(value):
    return str(ndr_unpack(misc.GUID, value))


password_charsets = [
    string.ascii_lowercase,
    string.ascii_uppercase,
    string.digits,
    r'^!\$%&/()=?{[]}+~#-_.:,;<>|\\',
]


def generate_strong_password(length=24):
    pwd = []
    charset = random.choice(password_charsets)
    while len(pwd) < length:
        pwd.append(random.choice(charset))
        charset = random.choice(list(set(password_charsets) - {charset}))
    return "".join(pwd)


def set_ucs_passwd_user(connector, key, ucs_object):
    """set random password to fulfill required values"""
    ucs_object['password'] = generate_strong_password()


def check_ucs_lastname_user(connector, key, ucs_object):
    """check if required values for lastname are set"""
    if not ucs_object.has_property('lastname') or not ucs_object['lastname']:
        ucs_object['lastname'] = ucs_object.get('username')


def set_primary_group_user(connector, key, ucs_object):
    """check if correct primary group is set"""
    connector.set_primary_group_to_ucs_user(key, ucs_object)


# compare functions
# helper
def dictonary_lowercase(dict_):
    if isinstance(dict_, dict):
        ndict = {}
        for key in dict_.keys():
            ndict[key] = []
            for val in dict_[key]:
                ndict[key].append(val.lower())
        return ndict
    elif isinstance(dict_, list):
        nlist = []
        for d in dict_:
            nlist.append(d.lower())
        return nlist
    else:
        try:  # should be string
            return dict_.lower()
        except Exception:  # FIXME: which exception is to be caught?
            pass


def compare_normal(val1, val2):  # noqa: FURB118
    return val1 == val2


def compare_lowercase(val1, val2):
    try:  # TODO: fails if conversion to ascii-str raises exception
        return dictonary_lowercase(val1) == dictonary_lowercase(val2)
    except Exception:  # FIXME: which exception is to be caught?
        return False


# helper classes
class configdb:

    def __init__(self, filename):
        self.filename = filename
        self._dbcon = lite.connect(self.filename)

    def get_by_value(self, section, option):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute(f"SELECT key FROM '{section}' WHERE value=?", (option,))  # noqa: S608
                rows = cur.fetchall()
                cur.close()
                if rows:
                    return rows[0][0]
                return ''
            except lite.Error:
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def get(self, section, option):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute(f"SELECT value FROM '{section}' WHERE key=?", (option,))  # noqa: S608
                rows = cur.fetchall()
                cur.close()
                if rows:
                    return rows[0][0]
                return ''
            except lite.Error:
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def set(self, section, option, value):
        cmd = f"INSERT OR REPLACE INTO '{section}' (key, value) VALUES (?, ?);"  # noqa: S608
        val = [option, value]
        if section == "AD rejected":
            # update retry_count
            cmd = f"INSERT OR REPLACE INTO '{section}' (key, value, retry_count) VALUES (?, ?, COALESCE((SELECT retry_count FROM '{section}' WHERE key = ? )+1 ,0));"  # noqa: S608
            val = [option, value, option]
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute(cmd, val)
                self._dbcon.commit()
                cur.close()
                return
            except lite.Error as e:
                log.error("sqlite: %s", e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def items(self, section):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute(f"SELECT * FROM '{section}'")  # noqa: S608
                rows = cur.fetchall()
                cur.close()
                return rows
            except lite.Error as e:
                log.warning("sqlite: %s", e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def remove_option(self, section, option):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute(f"DELETE FROM '{section}' WHERE key=?", (option,))  # noqa: S608
                self._dbcon.commit()
                cur.close()
                return
            except lite.Error as e:
                log.warning("sqlite: %s", e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def has_section(self, section):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (section,))
                rows = cur.fetchone()
                cur.close()
                return bool(rows)
            except lite.Error as e:
                log.warning("sqlite: %s", e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def add_section(self, section):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                if section in ["AD rejected"]:
                    cur.execute(f"CREATE TABLE IF NOT EXISTS '{section}' (Key TEXT PRIMARY KEY, Value TEXT, retry_count NUMBER DEFAULT 0)")
                else:
                    cur.execute(f"CREATE TABLE IF NOT EXISTS '{section}' (Key TEXT PRIMARY KEY, Value TEXT)")
                self._dbcon.commit()
                cur.close()
                return
            except lite.Error as e:
                log.warning("sqlite: %s", e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def has_option(self, section, option):
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute(f"SELECT value FROM '{section}' WHERE key=?", (option,))  # noqa: S608
                rows = cur.fetchall()
                cur.close()
                return bool(rows)
            except lite.Error as e:
                log.warning("sqlite: %s", e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def get_rows_with_key_ending_in_dn(self, section, dn):
        ending = '%%,%s' % dn
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute("SELECT * FROM '%s' WHERE key LIKE ?" % section, (ending,))  # noqa: S608
                rows = cur.fetchall()
                cur.close()
                return rows or []
            except lite.Error as e:
                ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)

    def get_rows_with_value_ending_in_dn(self, section, dn):
        ending = '%%,%s' % dn
        for _i in [1, 2]:
            try:
                cur = self._dbcon.cursor()
                cur.execute("SELECT * FROM '%s' WHERE value LIKE ?" % section, (ending,))  # noqa: S608
                rows = cur.fetchall()
                cur.close()
                return rows or []
            except lite.Error as e:
                ud.debug(ud.LDAP, ud.WARN, "sqlite: %s" % e)
                if self._dbcon:
                    self._dbcon.close()
                self._dbcon = lite.connect(self.filename)


class RFC4514_dn:
    special_dn_chars = '"+,;<=>'
    pattern = '|'.join(f'({re.escape(ldap.dn.escape_dn_chars(s))})' for s in special_dn_chars)
    match = re.compile(pattern)
    substs = [f'\\{ord(s):X}' for s in special_dn_chars]
    replace = lambda m: RFC4514_dn.substs[m.lastindex - 1]  # noqa: E731

    @classmethod
    def to_ad(cls, dn):
        """Currently just for documentation purposes"""
        return ldap.dn.dn2str(ldap.dn.str2dn(dn))

    @classmethod
    def to_openldap(cls, dn):
        """Doing the inverse of RFC4514_dn.to_ad"""
        return cls.match.sub(cls.replace, dn)


class Mapping:

    def __init__(self, mapping):
        self.mapping = mapping

    def __repr__(self):
        mapping_lines = ['{']
        indent = "\t"
        for mapping_key, mapping_property in sorted(self.mapping.items()):
            prop_repr = '\n'.join(indent + x for x in repr(mapping_property).splitlines()).lstrip('\t')
            mapping_lines.append(f"{indent}{mapping_key!r}: {prop_repr}")
        mapping_lines.append("}")
        return '\n'.join(mapping_lines)
        return pprint.pformat(self.mapping, indent=4, width=250)


class attribute:
    """
    A mapping attribute description

    :param ucs_attribute: The property name of the object in UDM
    :type ucs_attribute: str

    :param ldap_attribute: The LDAP attribute name of the object in UCS LDAP
    :type ldap_attribute: str

    :param con_attribute: The LDAP attribute name of the object in AD LDAP
    :type con_attribute: str

    :param con_other_attribute: Further LDAP attribute name of the object in AD LDAP.
    :type con_other_attribute: str

    :param required: unused
    :type required: bool

    :param single_value: Whether the attribute is single_value in the AD LDAP.
    :type single_value: bool

    :param compare_function: A comparison function which compares raw ldap attribute values.
    :type compare_function: callable

    :param mapping: Mapping functions for (sync_to_ad, sync_to_ucs)
    :ptype mapping: tuple

    :param reverse_attribute_check: Make a reverse check of this mapping, if the mapping is not 1:1.
    :ptype reverse_attribute_check: bool

    :param sync_mode: The syncronization direction (read, write, sync)
    :ptype sync_mode: str
    """

    def __init__(
        self,
        ucs_attribute='',
        ldap_attribute='',
        con_attribute='',
        con_other_attribute='',
        required=0,
        single_value=False,
        compare_function='',
        mapping=(),
        reverse_attribute_check=False,
        sync_mode='sync',
        con_depends='',
        con_attribute_encoding='UTF-8',
    ):
        self.ucs_attribute = ucs_attribute
        self.ldap_attribute = ldap_attribute
        self.con_attribute = con_attribute
        self.con_attribute_encoding = con_attribute_encoding
        self.con_other_attribute = con_other_attribute
        self.con_depends = con_depends
        self.required = required
        # If no compare_function is given, we default to `compare_normal()`
        self.compare_function = compare_function or compare_normal
        if mapping:
            self.mapping = mapping
        # Make a reverse check of this mapping. This is neccessary if the attribute is
        # available in UCS and in AD but the mapping is not 1:1.
        # For example the homeDirectory attribute is in UCS and in AD, but the mapping is
        # from homeDirectory in AD to sambaHomePath in UCS. The homeDirectory in UCS is not
        # considered.
        # Seee https://forge.univention.org/bugzilla/show_bug.cgi?id=25823
        self.reverse_attribute_check = reverse_attribute_check
        self.sync_mode = sync_mode
        self.single_value = single_value

    def __repr__(self):
        mapping_lines = ["univention.connector.attribute("]
        indent = "\t"
        for attribute_member in sorted(vars(self)):
            subsubobj = getattr(self, attribute_member)
            if not subsubobj:
                continue
            if isinstance(subsubobj, FunctionType):
                mapping_lines.append(f"{indent}{attribute_member} = {subsubobj.__module__}.{subsubobj.__name__},  # function")
            else:
                mapping_lines.append(f"{indent}{attribute_member} = {subsubobj!r},")
        mapping_lines.append(")")
        return '\n'.join(mapping_lines)
        return f'univention.connector.attribute(**{pprint.pformat(dict(self.__dict__), indent=4, width=250)})'


class property:

    def __init__(
        self,
        ucs_default_dn='',
        con_default_dn='',
        ucs_module='',
        ucs_module_others=[],
        sync_mode='',
        scope='',
        con_search_filter='',
        ignore_filter=None,
        match_filter=None,
        allow_subtree=[],
        allow_filter=None,
        ignore_subtree=[],
        con_create_objectclass=[],
        con_create_attributes=[],
        dn_mapping_function=[],
        attributes=None,
        ucs_create_functions=[],
        post_con_create_functions=[],
        post_con_modify_functions=[],
        post_ucs_modify_functions=[],
        post_attributes=None,
        mapping_table=None,
        position_mapping=[],
        con_subtree_delete_objects=[],
    ):
        self.ucs_default_dn = ucs_default_dn

        self.con_default_dn = con_default_dn

        self.ucs_module = ucs_module

        # allow a 1:n mapping, for example a Windows client
        # could be a computers/windows or a computers/memberserver
        # object
        self.ucs_module_others = ucs_module_others
        self.sync_mode = sync_mode

        self.scope = scope

        self.con_search_filter = con_search_filter
        self.ignore_filter = ignore_filter
        self.match_filter = match_filter
        self.allow_subtree = allow_subtree
        self.allow_filter = allow_filter
        self.ignore_subtree = ignore_subtree

        self.con_create_objectclass = con_create_objectclass
        self.con_create_attributes = con_create_attributes
        self.dn_mapping_function = dn_mapping_function
        self.attributes = attributes

        self.ucs_create_functions = ucs_create_functions

        self.post_con_create_functions = post_con_create_functions
        self.post_con_modify_functions = post_con_modify_functions
        self.post_ucs_modify_functions = post_ucs_modify_functions

        self.post_attributes = post_attributes
        self.mapping_table = mapping_table or {}
        self.position_mapping = position_mapping

        self.con_subtree_delete_objects = con_subtree_delete_objects

    def __repr__(self):
        mapping_lines = ['univention.connector.property(']
        indent = "\t"
        for conn_attribute in sorted(vars(self)):
            subobj = getattr(self, conn_attribute)
            if not subobj:
                continue
            if isinstance(subobj, dict):
                mapping_lines.append(f"{indent}{conn_attribute} = {{")
                for attr_key, mapping_attr in subobj.items():
                    attr_repr = '\n'.join(indent + indent + x for x in repr(mapping_attr).splitlines()).lstrip('\t')
                    mapping_lines.append(f"{indent + indent}{attr_key!r}: {attr_repr},")
                mapping_lines.append(f"{indent}}},")
            elif isinstance(subobj, list):
                if subobj and isinstance(subobj[0], FunctionType):
                    subobj = [f'<function {x.__module__}.{x.__name__}()>' for x in subobj]
                mapping_lines.append("{}{} = {},".format(indent, conn_attribute, '\n'.join(indent + indent + x for x in pprint.pformat(subobj).splitlines()).lstrip(indent)))
            else:
                mapping_lines.append(f"{indent}{conn_attribute} = {subobj!r},")
        mapping_lines.append(")")
        return '\n'.join(mapping_lines)
        return f'univention.connector.property(**{pprint.pformat(dict(self.__dict__), indent=4, width=250)})'


class ucs:

    def __init__(self, CONFIGBASENAME, _property, configRegistry, listener_dir, logfilename, debug_level):
        self.CONFIGBASENAME = CONFIGBASENAME

        self.configRegistry = configRegistry
        self.property = _property  # this is the mapping!

        self._logfile = logfilename or f'/var/log/univention/{self.CONFIGBASENAME}-ad.log'
        self._debug_level = debug_level or int(self.configRegistry.get(f'{self.CONFIGBASENAME}/debug/level', ud.PROCESS))
        self.init_debug()

        self.listener_dir = listener_dir

        configdbfile = f'/etc/univention/{self.CONFIGBASENAME}/internal.sqlite'
        self.config = configdb(configdbfile)

        adcachedbfile = f'/etc/univention/{self.CONFIGBASENAME}/adcache.sqlite'
        self.adcache = ADCache(adcachedbfile)

        for section in ['DN Mapping UCS', 'DN Mapping CON', 'UCS rejected', 'UCS deleted', 'UCS entryCSN']:
            if not self.config.has_section(section):
                self.config.add_section(section)

        irrelevant_attributes = self.configRegistry.get(f'{self.CONFIGBASENAME}/ad/mapping/attributes/irrelevant', '')
        self.irrelevant_attributes = set(irrelevant_attributes.split(','))
        self.allow_subtree_ancestors = self.configRegistry.is_true(f'{self.CONFIGBASENAME}/ad/mapping/allow-subtree-ancestors', False)

    def init_ldap_connections(self):
        self.open_ucs()

    def __enter__(self):
        return self

    def __exit__(self, etype=None, exc=None, etraceback=None):
        self.close_debug()

    def dn_mapped_to_base(self, dn, base):
        """Introduced for Bug #33110: Fix case of base part of DN"""
        if dn.endswith(base):
            return dn
        return self._subtree_replace(dn, base.lower(), base)

    def open_ucs(self):
        bindpw_file = self.configRegistry.get(f'{self.CONFIGBASENAME}/ldap/bindpw', '/etc/ldap.secret')
        binddn = self.configRegistry.get(f'{self.CONFIGBASENAME}/ldap/binddn', 'cn=admin,' + self.configRegistry['ldap/base'])
        with open(bindpw_file) as fd:
            bindpw = fd.read().rstrip()

        host = self.configRegistry.get(f'{self.CONFIGBASENAME}/ldap/server', self.configRegistry.get('ldap/master'))

        try:
            port = int(self.configRegistry.get(f'{self.CONFIGBASENAME}/ldap/port', self.configRegistry.get('ldap/master/port', 7389)))
        except ValueError:
            port = 7389

        self.lo = univention.admin.uldap.access(host=host, port=port, base=self.configRegistry['ldap/base'], binddn=binddn, bindpw=bindpw, follow_referral=True)

    def search_ucs(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=0, required=0, timeout=-1, sizelimit=0):
        try:
            result = self.lo.search(filter=filter, base=base, scope=scope, attr=attr, unique=unique, required=required, timeout=timeout, sizelimit=sizelimit)
            return result
        except univention.admin.uexceptions.ldapError as search_exception:
            log.info('Lost connection to the LDAP server. Trying to reconnect ...')
            try:
                self.open_ucs()
            except ldap.SERVER_DOWN:
                log.info('LDAP-Server seems to be down')
                raise search_exception

    def init_debug(self):
        udm_debug_level = self.configRegistry.get_int(f'{self.CONFIGBASENAME}/debug/udm/level', ud.WARN)
        structured = self.configRegistry.is_true(f'{self.CONFIGBASENAME}/debug/structured-logging', True)
        univention.logging.basicConfig(filename=self._logfile, univention_debug_level=self._debug_level, use_structured_logging=structured)
        logging.getLogger('ADMIN').set_ud_level(udm_debug_level)

    def close_debug(self):
        log.trace("close debug")

    def _get_config_option(self, section, option):
        return self.config.get(section, option)

    def _set_config_option(self, section, option, value):
        self.config.set(section, option, value)

    def _remove_config_option(self, section, option):
        self.config.remove_option(section, option)

    def _get_config_items(self, section):
        return self.config.items(section)

    def _save_rejected_ucs(self, filename, dn, resync=True, reason=''):
        if not resync:
            # Note that unescaped <> are invalid in DNs. See also:
            # `_list_rejected_ucs()`.
            dn = '<NORESYNC{}:{}>;{}'.format('=' + reason if reason else '', os.path.basename(filename), dn)
        self._set_config_option('UCS rejected', filename, dn)

    def _remove_rejected_ucs(self, filename):
        self._remove_config_option('UCS rejected', filename)

    def list_rejected_ucs(self, filter_noresync=False):
        rejected = self._get_config_items('UCS rejected')
        if filter_noresync:
            return [(fn, dn) for (fn, dn) in rejected if RE_NO_RESYNC.match(dn) is None]
        return rejected

    def _list_rejected_ucs(self):
        return self.list_rejected_ucs(filter_noresync=True)

    def _list_rejected_filenames_ucs(self):
        return [fn for (fn, dn) in self.list_rejected_ucs()]

    def _set_dn_mapping(self, dn_ucs, dn_con):
        self._set_config_option('DN Mapping UCS', dn_ucs.lower(), dn_con.lower())
        self._set_config_option('DN Mapping CON', dn_con.lower(), dn_ucs.lower())

    def _remove_dn_mapping(self, dn_ucs, dn_con):
        # delete all if mapping failed in the past
        dn_con_mapped = self._get_dn_by_ucs(dn_ucs.lower())
        dn_ucs_mapped = self._get_dn_by_con(dn_con.lower())
        dn_con_re_mapped = self._get_dn_by_ucs(dn_ucs_mapped.lower())
        dn_ucs_re_mapped = self._get_dn_by_con(dn_con_mapped.lower())

        for ucs, con in [(dn_ucs, dn_con), (dn_ucs_mapped, dn_con_mapped), (dn_ucs_re_mapped, dn_con_re_mapped)]:
            if con:
                self._remove_config_option('DN Mapping CON', con.lower())
            if ucs:
                self._remove_config_option('DN Mapping UCS', ucs.lower())

    def _remember_entryCSN_commited_by_connector(self, entryUUID, entryCSN):
        """Remember the entryCSN of a change committed by the AD-Connector itself"""
        value = self._get_config_option('UCS entryCSN', entryUUID)
        if value:
            entryCSN_set = set(value.split(','))
            entryCSN_set.add(entryCSN)
            value = ','.join(entryCSN_set)
        else:
            value = entryCSN
        self._set_config_option('UCS entryCSN', entryUUID, value)

    def _forget_entryCSN(self, entryUUID, entryCSN):
        value = self._get_config_option('UCS entryCSN', entryUUID)
        if not value:
            return False

        entryCSN_set = set(value.split(','))
        if entryCSN not in entryCSN_set:
            return False

        entryCSN_set.remove(entryCSN)
        if entryCSN_set:
            value = ','.join(entryCSN_set)
            self._set_config_option('UCS entryCSN', entryUUID, value)
        else:
            self._remove_config_option('UCS entryCSN', entryUUID)
        return True

    def _get_dn_by_ucs(self, dn_ucs):
        return self._get_config_option('DN Mapping UCS', dn_ucs.lower())

    def get_dn_by_ucs(self, dn_ucs):
        if not dn_ucs:
            return dn_ucs
        dn = self._get_dn_by_ucs(dn_ucs)
        return self.dn_mapped_to_base(dn, self.lo_ad.base)

    def _get_dn_by_con(self, dn_con):
        if not dn_con:
            return dn_con
        return self._get_config_option('DN Mapping CON', dn_con.lower())

    def get_dn_by_con(self, dn_con):
        dn = self._get_dn_by_con(dn_con)
        return self.dn_mapped_to_base(dn, self.lo.base)

    def _update_subtree_dns_in_mappings_by_con(self, old_con_dn, old_ucs_dn, new_con_dn, new_ucs_dn):
        old_con_dn_lower = old_con_dn.lower()
        old_ucs_dn_lower = old_ucs_dn.lower()
        new_con_dn_lower = new_con_dn.lower()
        new_ucs_dn_lower = new_ucs_dn.lower()
        for row in self.config.get_rows_with_key_ending_in_dn('DN Mapping CON', old_con_dn_lower):
            _new_key = self._subtree_replace(row[0], old_con_dn_lower, new_con_dn_lower)
            _new_val = self._subtree_replace(row[1], old_ucs_dn_lower, new_ucs_dn_lower)
            self._remove_config_option('DN Mapping CON', row[0])
            self._set_config_option('DN Mapping CON', _new_key, _new_val)
        for row in self.config.get_rows_with_value_ending_in_dn('DN Mapping UCS', old_con_dn_lower):
            _new_key = self._subtree_replace(row[0], old_ucs_dn_lower, new_ucs_dn_lower)
            _new_val = self._subtree_replace(row[1], old_con_dn_lower, new_con_dn_lower)
            self._remove_config_option('DN Mapping UCS', row[0])
            self._set_config_option('DN Mapping UCS', _new_key, _new_val)

    def _check_dn_mapping(self, dn_ucs, dn_con):
        dn_con_mapped = self._get_dn_by_ucs(dn_ucs.lower())
        dn_ucs_mapped = self._get_dn_by_con(dn_con.lower())
        if dn_con_mapped != dn_con.lower() or dn_ucs_mapped != dn_ucs.lower():
            self._remove_dn_mapping(dn_ucs.lower(), dn_con_mapped.lower())
            self._remove_dn_mapping(dn_ucs_mapped.lower(), dn_con.lower())
            self._set_dn_mapping(dn_ucs.lower(), dn_con.lower())

    def context_log(self, property_type, obj, message='', to_ucs=True):
        direction = 'sync AD > UCS' if to_ucs else 'sync UCS > AD'
        prefix = '[%14s] [%10s] %r' % (property_type or '?', obj.get('modtype', '?'), obj.get('dn', '?'))
        return '{}: {}{}'.format(direction, prefix, f': {message}' if message else '')

    def __sync_file_from_ucs(self, filename, append_error=''):
        """sync changes from UCS stored in given file"""
        try:
            with open(filename, 'rb') as fob:
                (dn, new, old, old_dn) = pickle.load(fob, encoding='bytes')
                # With the Python 2 listener pickle files we got bytes here, otherwise already string
                if isinstance(dn, bytes):
                    dn = dn.decode('utf-8')
                if isinstance(old_dn, bytes):
                    old_dn = old_dn.decode('utf-8')
        except OSError:
            return True  # file not found so there's nothing to sync
        except (pickle.UnpicklingError, EOFError) as exc:
            message = 'file empty' if isinstance(exc, EOFError) else exc
            log.error('__sync_file_from_ucs: invalid pickle file %s: %s', filename, message)
            # ignore corrupted pickle file, but save as rejected to not try again
            self._save_rejected_ucs(filename, 'unknown', resync=False, reason='broken file')
            return False

        if dn == 'cn=Subschema':
            return True

        def recode_attribs(attribs):
            return {key.decode('UTF-8') if isinstance(key, bytes) else key: value for key, value in attribs.items()}

        new = recode_attribs(new)
        old = recode_attribs(old)

        key = None

        # if the object was moved into a ignored tree
        # we should delete this object
        ignore_subtree_match = False

        _attr = new or old
        _mod, key = self.identify_udm_object(dn, _attr)

        if not new:
            change_type = "delete"
            log.info("__sync_file_from_ucs: object was deleted")
            entryUUID = old.get('entryUUID', [b''])[0].decode('ASCII')
            entryCSN = old.get('entryCSN', [b''])[0].decode('ASCII')
            self._forget_entryCSN(entryUUID, entryCSN)
        else:
            entryUUID = new.get('entryUUID', [b''])[0].decode('ASCII')
            if entryUUID:
                if self.was_entryUUID_deleted(entryUUID):
                    if self._get_entryUUID(dn) == entryUUID:
                        log.process("__sync_file_from_ucs: Object with entryUUID %s has been removed before but became visible again.", entryUUID)
                    else:
                        log.process("__sync_file_from_ucs: Object with entryUUID %s has been removed before. Don't re-create.", entryUUID)
                        return True
            else:
                log.error("__sync_file_from_ucs: Object without entryUUID: %s", dn)
                return False

            entryCSN = new.get('entryCSN', [b''])[0].decode('ASCII')
            if self._forget_entryCSN(entryUUID, entryCSN):
                log.debug("__sync_file_from_ucs: Skipping back-sync of %s %s", key, dn)
                log.debug("__sync_file_from_ucs: because entryCSN %s was written by sync_to_ucs", entryCSN)
                return True

            # log.debug("__sync_file_from_ucs: old: %s" % old)
            # log.debug("__sync_file_from_ucs: new: %s" % new)
            if old and new:
                change_type = "modify"
                log.debug("__sync_file_from_ucs: object was modified")
                if old_dn and old_dn != dn:
                    log.debug("__sync_file_from_ucs: object was moved")
                    # object was moved
                    new_object = {'dn': dn, 'modtype': change_type, 'attributes': new}
                    old_object = {'dn': old_dn, 'modtype': change_type, 'attributes': old}
                    if self._ignore_object(key, new_object):
                        # moved into ignored subtree, delete:
                        log.debug("__sync_file_from_ucs: moved object is now ignored, will delete it")
                        change_type = 'delete'
                        ignore_subtree_match = True

                    if self._ignore_object(key, old_object):
                        # moved from ignored subtree, add:
                        log.debug("__sync_file_from_ucs: moved object was ignored, will add it")
                        change_type = 'add'

            else:
                object = {'dn': dn, 'modtype': 'modify', 'attributes': new}
                try:
                    if self._ignore_object(key, object):
                        if (new and not old) and (old_dn and old_dn != dn) and not self._ignore_object(key, {'dn': old_dn, 'attributes': new}):
                            # TODO: why do we not get an old,
                            # the _ignore_object in this case should operate on the old object, but currently we don't have it
                            # so we pass new because we need the attributes to check the ignore/allow filter
                            # we need to check if this is a move and in case that the new object is ignored and old object
                            # is not ignored we need to remove the object
                            log.error("__sync_file_from_ucs: object was moved and is ignored now, delete")
                            change_type = 'delete'
                            ignore_subtree_match = True
                        else:
                            log.debug("__sync_file_from_ucs: new object is ignored, nothing to do")
                            change_type = 'modify'
                            ignore_subtree_match = True
                            return True
                    else:
                        if old_dn and old_dn != dn:
                            change_type = "modify"
                            log.debug("__sync_file_from_ucs: object was moved")
                        else:
                            change_type = "add"
                            old_dn = ''  # there may be an old_dn if object was moved from ignored container
                            log.debug("__sync_file_from_ucs: object was added: %s", dn)
                except (ldap.SERVER_DOWN, SystemExit):
                    raise
                except Exception:  # FIXME: which exception is to be caught?
                    # the ignore_object method might throw an exception if the subschema will be synced
                    change_type = "add"
                    old_dn = ''  # there may be an old_dn if object was moved from ignored container
                    log.debug("__sync_file_from_ucs: object was added: %s", dn)

        if key:
            if change_type == 'delete':
                if old_dn:
                    object = {'dn': old_dn, 'modtype': change_type, 'attributes': old}
                else:
                    object = {'dn': dn, 'modtype': change_type, 'attributes': old}
            else:
                object = {'dn': dn, 'modtype': change_type, 'attributes': new}

            if change_type == 'modify' and old_dn:
                object['olddn'] = old_dn  # needed for correct samaccount-mapping

            if not self._ignore_object(key, object) or ignore_subtree_match:
                pre_mapped_ucs_dn = object['dn']
                # NOTE: pre_mapped_ucs_dn means: original ucs_dn (i.e. before _object_mapping)
                mapped_object = self._object_mapping(key, object, 'ucs')
                if not self._ignore_object(key, object) or ignore_subtree_match:
                    log.debug("__sync_file_from_ucs: finished mapping")

                    if change_type == 'modify':
                        # to be able to compare mapped values we need to map the old state of the object too
                        if old_dn:
                            object_old = {'dn': object['olddn'], 'modtype': change_type, 'attributes': old}
                        else:
                            object_old = {'dn': object['dn'], 'modtype': change_type, 'attributes': old}
                        object_old = self._object_mapping(key, object_old, 'ucs')
                    else:
                        object_old = {'dn': object['dn'], 'modtype': change_type, 'attributes': {}}  # Dummy

                    try:
                        if not self.sync_from_ucs(key, mapped_object, pre_mapped_ucs_dn, old_dn, object_old):
                            self._save_rejected_ucs(filename, dn)
                            return False
                        else:
                            return True
                    except ldap.SERVER_DOWN:
                        raise
                    except ldap.NO_SUCH_OBJECT:
                        self._save_rejected_ucs(filename, dn)
                        log.warning("sync failed, saved as rejected", filename=filename, exc_info=True)
                        return False
                    except Exception:
                        self._save_rejected_ucs(filename, dn)
                        log.warning("sync failed, saved as rejected", filename=filename, exc_info=True)
                        return False
                else:
                    return True
            else:
                return True
        else:
            log.debug("__sync_file_from_ucs: No mapping was found for dn: %s", dn)
            return True

    def get_ucs_ldap_object_dn(self, dn):
        try:
            return self.lo.lo.lo.search_s(dn, ldap.SCOPE_BASE, '(objectClass=*)', ('1.1',))[0][0]
        except ldap.NO_SUCH_OBJECT:
            return
        except ldap.INVALID_DN_SYNTAX:
            return None
        except ldap.INVALID_SYNTAX:
            return None

    def get_ucs_ldap_object(self, dn):
        try:
            return self.lo.get(dn, required=True)
        except ldap.NO_SUCH_OBJECT:
            return None
        except ldap.INVALID_DN_SYNTAX:
            return None
        except ldap.INVALID_SYNTAX:
            return None

    def get_ucs_object(self, property_type, dn):
        ucs_object = None
        searchdn = dn
        try:
            attr = self.get_ucs_ldap_object(searchdn)
            if not attr:
                log.debug("get_ucs_object: object not found: %s", searchdn)
                return None

            module, _key = self.identify_udm_object(searchdn, attr)
            if not module:
                module = self.modules[property_type]  # default, determined by mapping filter
                log.error("get_ucs_object: could not identify UDM object type: %s", searchdn)
                log.process("get_ucs_object: using default", module=module.module)

            ucs_object = univention.admin.objects.get(module, co=None, lo=self.lo, position='', dn=searchdn)
            log.debug("get_ucs_object: object found: %s", searchdn)
        except ldap.SERVER_DOWN:
            raise
        except Exception:  # FIXME: which exception is to be caught?
            log.debug("get_ucs_object: object search failed: %s", searchdn)
            log.warning("get_ucs_object: failure was", exc_info=True)
            return None

        return ucs_object

    def initialize_ucs(self):
        print("--------------------------------------")
        print("Initialize sync from UCS")
        sys.stdout.flush()

        # load UCS Modules
        self.modules = {}
        self.modules_others = {}
        position = univention.admin.uldap.position(self.lo.base)

        for key, mapping in self.property.items():
            if mapping.ucs_module:
                self.modules[key] = univention.admin.modules.get(mapping.ucs_module)
                if hasattr(mapping, 'identify'):
                    log.debug("Override identify function for %s", key)
                    self.modules[key].identify = mapping.identify
            else:
                self.modules[key] = None
            univention.admin.modules.init(self.lo, position, self.modules[key])

            self.modules_others[key] = []
            if mapping.ucs_module_others:
                for m in mapping.ucs_module_others:
                    if m:
                        self.modules_others[key].append(univention.admin.modules.get(m))
                for m in self.modules_others[key]:
                    if m:
                        univention.admin.modules.init(self.lo, position, m)

        # try to resync rejected changes
        self.resync_rejected_ucs()
        # call poll_ucs to sync
        self.poll_ucs()
        print("--------------------------------------")
        sys.stdout.flush()

    def initialize(self):
        # dummy
        pass

    def resync_rejected_ucs(self):
        """tries to resync rejected changes from UCS"""
        rejected = self._list_rejected_ucs()
        change_counter = 0
        print("--------------------------------------")
        print(f"Sync {len(rejected)} rejected changes from UCS")
        sys.stdout.flush()

        if rejected:
            for filename, dn in rejected:
                log.process('sync UCS > AD: Resync rejected file: %s', filename)
                try:
                    if self.__sync_file_from_ucs(filename, append_error=' rejected'):
                        try:
                            os.remove(os.path.join(filename))
                        except OSError:  # file not found
                            pass
                        self._remove_rejected_ucs(filename)
                        change_counter += 1
                except ldap.SERVER_DOWN:
                    raise
                except Exception:  # FIXME: which exception is to be caught?
                    self._save_rejected_ucs(filename, dn)
                    log.warning("sync failed, saved as rejected", filename=filename)

        print(f"restored {change_counter} rejected changes")
        print("--------------------------------------")
        sys.stdout.flush()

    def resync_rejected(self):
        # dummy
        pass

    def poll_ucs(self):
        """poll changes from UCS: iterates over files exported by directory-listener module"""
        # check for changes from ucs ldap directory

        log.debug("sync UCS > AD: polling")
        change_counter = 0
        MAX_SYNC_IN_ONE_INTERVAL = 50000

        self.rejected_files = self._list_rejected_filenames_ucs()

        print("--------------------------------------")
        print(f"try to sync {min(len(os.listdir(self.listener_dir)) - 1, MAX_SYNC_IN_ONE_INTERVAL)} changes from UCS")
        print("done:", end=' ')
        sys.stdout.flush()
        done_counter = 0
        files = sorted(os.listdir(self.listener_dir))

        # Only synchronize the first MAX_SYNC_IN_ONE_INTERVAL changes otherwise
        # the change list is too long and it took too much time
        files = files[:MAX_SYNC_IN_ONE_INTERVAL]

        # We may dropped the parent object, so don't show the traceback in any case
        for listener_file in files:
            sync_successfull = False
            filename = os.path.join(self.listener_dir, listener_file)
            if os.path.isfile(filename):
                if filename not in self.rejected_files:
                    try:
                        with open(filename, 'rb') as fob:
                            (dn, _new, _old, old_dn) = pickle.load(fob, encoding='bytes')
                            if isinstance(dn, bytes):
                                dn = dn.decode('utf-8')
                            if isinstance(old_dn, bytes):
                                old_dn = old_dn.decode('utf-8')
                    except OSError:
                        continue  # file not found so there's nothing to sync
                    except (pickle.UnpicklingError, EOFError) as exc:
                        message = 'file empty' if isinstance(exc, EOFError) else exc
                        log.error('poll_ucs: invalid pickle file %s: %s', filename, message)
                        # ignore corrupted pickle file, but save as rejected to not try again
                        self._save_rejected_ucs(filename, 'unknown', resync=False, reason='broken file')
                        continue

                    # If the list contains more than one file, the DN will be synced later
                    # but if the object was added or removed, the synchonization is required
                    for i in [0, 1]:  # do it twice if the LDAP connection was closed
                        try:
                            sync_successfull = self.__sync_file_from_ucs(filename)
                        except (ldap.SERVER_DOWN, SystemExit):
                            # once again, ldap idletimeout ...
                            if i == 0:
                                self.open_ucs()
                                continue
                            raise
                        except Exception:
                            self._save_rejected_ucs(filename, dn)
                            # We may dropped the parent object, so don't show this warning
                            log.exception("sync failed, saved as rejected: %s", filename)
                        if sync_successfull:
                            os.remove(os.path.join(self.listener_dir, listener_file))
                            change_counter += 1
                        break

                done_counter += 1
                print(f"{done_counter}", end=' ')
                sys.stdout.flush()

        print("")

        self.rejected_files = self._list_rejected_filenames_ucs()

        if self.rejected_files:
            print(f"Changes from UCS: {change_counter} ({len(self.rejected_files)} saved rejected)")
        else:
            print("Changes from UCS: {} ({} saved rejected)".format(change_counter, '0'))
        print("--------------------------------------")
        sys.stdout.flush()

        if self.profiling and change_counter:
            log.process("POLL FROM UCS: Processed %s", change_counter)
        return change_counter

    def poll(self, show_deleted=True):
        # dummy
        pass

    def __set_values(self, property_type, object, ucs_object, modtype='modify'):
        if modtype != 'add':
            ucs_object.open()
        log.debug('__set_values: object: %s', object)

        def set_values(attributes):
            if attributes.ldap_attribute in object['attributes']:
                ucs_key = attributes.ucs_attribute
                if ucs_key:
                    value = object['attributes'][attributes.ldap_attribute]
                    log.debug(self.context_log(property_type, object, 'set attribute %r as ucs property %r: value=%r', to_ucs=True), attributes.con_attribute, ucs_key, value)

                    if isinstance(value, list) and len(value) == 1:
                        value = value[0]

                    if attributes.con_attribute_encoding:
                        value = [x.decode(attributes.con_attribute_encoding) for x in value] if isinstance(value, list) else value.decode(attributes.con_attribute_encoding)

                    # set encoding
                    compare = [ucs_object[ucs_key], value]
                    if not attributes.compare_function(compare[0], compare[1]):
                        # This is deduplication of LDAP attribute values for AD -> UCS.
                        # It preserves ordering of the attribute values which is
                        # important for the handling of `con_other_attribute`.
                        log.debug("set key in ucs-object", property=ucs_key, value=value)
                        if not ucs_object.has_property(ucs_key) and ucs_key in ucs_object:
                            ucs_object.options.extend(ucs_object.descriptions[ucs_key].options)
                        if isinstance(value, list):
                            ucs_object[ucs_key] = list(collections.OrderedDict.fromkeys(value))
                        else:
                            ucs_object[ucs_key] = value
                        log.debug("result key in ucs-object", property=ucs_key, value=ucs_object[ucs_key])
                else:
                    log.trace("__set_values: no ucs_attribute found in %s", attributes)
            else:
                # the value isn't set in the AD directory, but it could be set in UCS, so we should delete it on UCS side

                # prevent value resets of mandatory attributes
                mandatory_attrs = ['lastname']

                ucs_key = attributes.ucs_attribute
                if ucs_object.has_property(ucs_key):
                    # Special handling for con other attributes, see Bug #20599
                    if attributes.con_other_attribute:
                        value = object['attributes'].get(attributes.con_other_attribute)
                        if value:
                            if attributes.con_attribute_encoding:
                                value = [x.decode(attributes.con_attribute_encoding) for x in value] if isinstance(value, list) else value.decode(attributes.con_attribute_encoding)
                            ucs_object[ucs_key] = value
                            log.trace('__set_values: no ldap_attribute defined in %r, we set the key %r in the ucs-object to con_other_attribute %r', object['dn'], ucs_key, attributes.con_other_attribute)
                        elif ucs_key not in mandatory_attrs:
                            ucs_object[ucs_key] = []
                            log.trace('__set_values: no ldap_attribute defined in %r, we unset the key %r in the ucs-object', object['dn'], ucs_key)
                        else:
                            log.warning('__set_values: The attributes for %s have not been removed as it represents a mandatory attribute', ucs_key)
                    else:
                        log.trace('__set_values: no ldap_attribute defined in %r, we unset the key %r in the ucs-object', object['dn'], ucs_key)

                        if ucs_key not in mandatory_attrs:
                            ucs_object[ucs_key] = []
                        else:
                            log.warning('__set_values: The attributes for %s have not been removed as it represents a mandatory attribute', ucs_key)

        MAPPING = self.property[property_type]
        for attr_key, attributes in MAPPING.attributes.items():
            if attributes.sync_mode not in ['read', 'sync']:
                log.debug("__set_values: Skip %s mode attribute %s ", attributes.sync_mode, attr_key)
                continue

            con_attribute = attributes.con_attribute
            con_other_attribute = attributes.con_other_attribute

            changed_attributes = object.get('changed_attributes')
            changed = (
                not changed_attributes
                or con_attribute in changed_attributes
                or (con_other_attribute and con_other_attribute in changed_attributes)
                or attributes.con_depends in changed_attributes
            )

            if changed or modtype == 'add':
                log.trace("__set_values: Set: %s", con_attribute)
                set_values(attributes)
            else:
                log.debug('__set_values: Skip: %s', con_attribute)

        # post-values
        if not MAPPING.post_attributes:
            return
        for attr_key, post_attributes in MAPPING.post_attributes.items():
            log.trace("__set_values: mapping for attribute: %s", attr_key)
            if post_attributes.sync_mode not in ['read', 'sync']:
                log.trace("__set_values: Skip %s mode attribute %s ", post_attributes.sync_mode, attr_key)
                continue

            con_attribute = post_attributes.con_attribute
            con_other_attribute = post_attributes.con_other_attribute

            changed_attributes = object.get('changed_attributes')

            changed = (
                not changed_attributes
                or con_attribute in changed_attributes
                or (con_other_attribute and con_other_attribute in changed_attributes)
                or post_attributes.con_depends in changed_attributes
            )
            if changed or modtype == 'add':
                log.trace("__set_values: Set: %s", con_attribute)
                if post_attributes.reverse_attribute_check:
                    if object['attributes'].get(post_attributes.ldap_attribute):
                        set_values(post_attributes)
                    else:
                        ucs_object[post_attributes.ucs_attribute] = ''
                else:
                    set_values(post_attributes)
            else:
                log.trace("__set_values: Skip: %s", con_attribute)

    def add_in_ucs(self, property_type, object, module, position):
        ucs_object = module.object(None, self.lo, position=position)
        ucs_object.open()
        if property_type == 'group':
            log.debug("sync_to_ucs: remove %s from ucs group cache", object['dn'])
            self.group_members_cache_ucs[object['dn'].lower()] = set()

        self.__set_values(property_type, object, ucs_object, modtype='add')
        for ucs_create_function in self.property[property_type].ucs_create_functions:
            log.debug("Call ucs_create_functions: %s", ucs_create_function)
            ucs_create_function(self, property_type, ucs_object)

        serverctrls = []
        response = {}

        serverctrls = [PostReadControl(True, ['entryUUID', 'entryCSN'])]
        res = ucs_object.create(serverctrls=serverctrls, response=response)
        if res:
            for c in response.get('ctrls', []):
                if c.controlType == PostReadControl.controlType:
                    entryUUID = c.entry['entryUUID'][0].decode('ASCII')
                    entryCSN = c.entry['entryCSN'][0].decode('ASCII')
                    self._remember_entryCSN_commited_by_connector(entryUUID, entryCSN)
            res = True
        return res

    def modify_in_ucs(self, property_type, object, module, position):
        ucs_object_dn = object.get('olddn', object['dn'])
        ucs_object = univention.admin.objects.get(module, None, self.lo, dn=ucs_object_dn, position='')
        self.__set_values(property_type, object, ucs_object)

        serverctrls = []
        response = {}

        serverctrls = [PostReadControl(True, ['entryUUID', 'entryCSN'])]
        res = ucs_object.modify(serverctrls=serverctrls, response=response)
        if res:
            for c in response.get('ctrls', []):
                if c.controlType == PostReadControl.controlType:  # If the modify actually did something
                    entryUUID = c.entry['entryUUID'][0].decode('ASCII')
                    entryCSN = c.entry['entryCSN'][0].decode('ASCII')
                    self._remember_entryCSN_commited_by_connector(entryUUID, entryCSN)
        return res

    def move_in_ucs(self, property_type, object, module, position):
        if self.lo.compare_dn(object['olddn'].lower(), object['dn'].lower()):
            log.warning("move_in_ucs: cancel move, old and new dn are the same (%r to %r)", object['olddn'], object['dn'])
            return True

        log.debug("move_in_ucs: move object from %r to %r", object['olddn'], object['dn'])
        ucs_object = univention.admin.objects.get(module, None, self.lo, dn=object['olddn'], position='')
        ucs_object.open()
        res = ucs_object.move(object['dn'])
        return res

    def _get_entryUUID(self, dn):
        try:
            result = self.search_ucs(base=dn, scope='base', attr=['entryUUID'], unique=True)
            if result:
                return result[0][1].get('entryUUID')[0].decode('ASCII')
            else:
                return None
        except univention.admin.uexceptions.noObject:
            return None

    def update_deleted_cache_after_removal(self, entryUUID, objectGUID):
        if not entryUUID:
            return
        if not objectGUID:
            objectGUID = 'objectGUID'  # use a dummy value
        log.debug("update_deleted_cache_after_removal: Save entryUUID %r as deleted to UCS deleted cache. ObjectGUUID: %r", entryUUID, objectGUID)
        self._set_config_option('UCS deleted', entryUUID, objectGUID)

    def was_entryUUID_deleted(self, entryUUID):
        objectGUID = self.config.get('UCS deleted', entryUUID)
        return bool(objectGUID)

    def was_objectGUID_deleted_by_ucs(self, objectGUID):
        try:
            entryUUID = self.config.get_by_value('UCS deleted', objectGUID)
            if entryUUID:
                return True
        except Exception as err:
            log.error("was_objectGUID_deleted_by_ucs: failed to look for objectGUID %r in 'UCS deleted': %s", objectGUID, err)
        return False

    def delete_in_ucs(self, property_type, object, module, position):
        """Removes an AD object in UCS-LDAP"""
        objectGUID = object['attributes'].get('objectGUID', [None])[0]
        if objectGUID:
            objectGUID = decode_guid(objectGUID)
        entryUUID = self._get_entryUUID(object['dn'])

        if property_type in ['ou', 'container'] and objectGUID and self.was_objectGUID_deleted_by_ucs(objectGUID):
            log.process("delete_in_ucs: object %s already deleted in UCS, ignoring delete", object['dn'])
            return True
        try:
            ucs_object = univention.admin.objects.get(module, None, self.lo, dn=object['dn'], position='')
        except univention.admin.uexceptions.noObject:
            raise  # object is already removed... TODO: enable if wanted!
            return True

        ucs_object.open()

        try:
            try:
                ucs_object.remove()
                self.update_deleted_cache_after_removal(entryUUID, objectGUID)
                return True
            except univention.admin.uexceptions.ldapError as exc:
                if isinstance(exc.original_exception, ldap.NOT_ALLOWED_ON_NONLEAF):
                    raise exc.original_exception
                raise
        except ldap.NOT_ALLOWED_ON_NONLEAF:
            log.debug("remove object from UCS failed, need to delete subtree")
            if self._remove_subtree_in_ucs(object):
                # FIXME: endless recursion if there is one subtree-object which is ignored, not identifyable or can't be removed.
                return self.delete_in_ucs(property_type, object, module, position)
            return False

    def _remove_subtree_in_ucs(self, parent_ucs_object):
        for subdn, subattr in self.search_ucs(base=parent_ucs_object['dn'], attr=['*', '+']):
            if self.lo.compare_dn(subdn.lower(), parent_ucs_object['dn'].lower()):  # TODO: search with scope=children and remove this check
                continue

            log.debug("delete: %r", subdn)

            _mod, key = self.identify_udm_object(subdn, subattr)
            subobject_ucs = {'dn': subdn, 'modtype': 'delete', 'attributes': subattr}
            back_mapped_subobject = self._object_mapping(key, subobject_ucs, 'ucs')
            log.warning("delete subobject: %r", back_mapped_subobject['dn'])

            if not self._ignore_object(key, back_mapped_subobject):
                # FIXME: this call is wrong!: sync_to_ucs() must be called with a ad_object not with a ucs_object!
                if not self.sync_to_ucs(key, subobject_ucs, back_mapped_subobject['dn'], parent_ucs_object):
                    log.warning("delete of subobject failed: %r", subdn)
                    return False
        return True

    def sync_to_ucs(self, property_type, object, pre_mapped_ad_dn, original_object):
        """
        Synchronize an object from AD-LDAP to UCS Open-LDAP.

        :param property_type:
            the type of the object to be synced, must be part of the mapping. (e.g. "user", "group", "dc", "windowscomputer", etc.)
        :param object:
            A dictionary describing the AD object as returned by _object_mapping()
            modtype: A modification type ("add", "modify", "move", "delete")
            dn: The DN of the object in the UCS-LDAP
            olddn: The olddn of the object object in UCS-LDAP (e.g. on "move" operation)
        :ptype object: dict
        :param pre_mapped_ad_dn:
            same as original_object['dn']
        :param original_object:
            as returned by __object_from_element()
        """
        # NOTE: pre_mapped_ad_dn means: original ad_dn (i.e. before _object_mapping)
        # this function gets an object from the ad class, which should be converted into a ucs module

        # if sync is write (sync to AD) or none, there is nothing to do
        if not property_type or self.property[property_type].sync_mode in ['write', 'none']:
            if property_type:
                log.debug(self.context_log(property_type, object, "sync ignored: sync_mode is %s", to_ucs=True), self.property[property_type].sync_mode)
            else:
                log.debug(self.context_log(property_type, object, "sync ignored: no mapping defined", to_ucs=True))
            return True

        if object['dn'].find('\\0ACNF:') > 0:
            log.process('Ignore conflicted object: %s', object['dn'])
            return True

        try:
            guid = decode_guid(original_object.get('attributes').get('objectGUID')[0])

            object['changed_attributes'] = []
            if object['modtype'] == 'modify' and original_object:
                old_ad_object = self.adcache.get_entry(guid)
                log.debug("sync_to_ucs: old_ad_object: %s", old_ad_object)
                log.debug("sync_to_ucs: new_ad_object: %s", original_object['attributes'])
                original_attributes = original_object['attributes']
                if old_ad_object:
                    for attr in original_object['attributes']:
                        if set(old_ad_object.get(attr, [])) != set(original_attributes.get(attr, [])):
                            object['changed_attributes'].append(attr)
                    for attr in old_ad_object:
                        if set(old_ad_object.get(attr, [])) != set(original_attributes.get(attr, [])) and attr not in object['changed_attributes']:
                            object['changed_attributes'].append(attr)
                    if not (set(object['changed_attributes']) - self.irrelevant_attributes):
                        if (
                            property_type == "user"
                            and self.configRegistry.is_false('connector/ad/mapping/user/password/disabled', True)
                            and not self.configRegistry.is_true('connector/ad/mapping/user/password/kinit', False)
                        ):
                            if object['attributes'].get('pwdLastSet', [b'1'])[0] == b'0':
                                log.debug("sync_to_ucs: pwdLastSet is 0. Do not ignore %r", original_object['dn'])
                            else:
                                log.debug("sync_to_ucs: ignore %r", original_object['dn'])
                                return True
                        else:
                            log.debug("sync_to_ucs: ignore %r", original_object['dn'])
                            log.trace("sync_to_ucs: changed_attributes=%s", object['changed_attributes'])
                            return True
                else:
                    object['changed_attributes'] = list(original_attributes.keys())
            log.debug("The following attributes have been changed: %s", object['changed_attributes'])

            result = False

            # Check if the object on UCS side should be synchronized
            #  https://forge.univention.org/bugzilla/show_bug.cgi?id=37351
            if property_type == "windowscomputer":
                old_ucs_ldap_object = {}
                old_ucs_ldap_object['dn'] = object.get('olddn', object['dn'])
                old_ucs_ldap_object['attributes'] = self.get_ucs_ldap_object(old_ucs_ldap_object['dn'])

                if old_ucs_ldap_object['attributes'] and self._ignore_object(property_type, old_ucs_ldap_object):
                    log.process('The object %r will be ignored because _ignore_object matched the old object state in OpenLDAP.', old_ucs_ldap_object['dn'])
                    return True

            old_object = self.get_ucs_object(property_type, object.get('olddn', object['dn']))

            # Corrections in case the target situation is unexpected:
            if old_object and object['modtype'] == 'add':
                object['modtype'] = 'modify'
            if not old_object and object['modtype'] == 'modify':
                object['modtype'] = 'add'
            if not old_object and object['modtype'] == 'move':
                if self.get_ucs_ldap_object_dn(object['dn']):
                    object['modtype'] = 'modify'
                else:
                    object['modtype'] = 'add'

            if self.group_member_mapping_cache_ucs.get(object['dn'].lower()) and object['modtype'] != 'delete':
                self.group_member_mapping_cache_ucs[object['dn'].lower()] = None

            log.process('sync to ucs:   [%14s] [%10s] %s', property_type, object['modtype'], object['dn'])
            position = univention.admin.uldap.position(self.configRegistry['ldap/base'])

            parent_dn = self.lo.parentDn(object['dn'])
            log.debug('sync_to_ucs: set position to %s', parent_dn)
            position.setDn(parent_dn)

            module = self.modules[property_type]  # default, determined by mapping filter
            if old_object:
                log.debug("sync_to_ucs: using existing target object type: %s", old_object.module)
                module = univention.admin.modules.get(old_object.module)

            if object['modtype'] == 'add':
                result = self.add_in_ucs(property_type, object, module, position)
                self._check_dn_mapping(object['dn'], pre_mapped_ad_dn)
                self.adcache.add_entry(guid, original_object.get('attributes'))
            if object['modtype'] == 'delete':
                if not old_object:
                    log.warning("Object to delete doesn't exists, ignore (%r)", object['dn'])
                    result = True
                else:
                    result = self.delete_in_ucs(property_type, object, module, position)
                self._remove_dn_mapping(object['dn'], pre_mapped_ad_dn)
                self.adcache.remove_entry(guid)
            if object['modtype'] == 'move':
                res = self.move_in_ucs(property_type, object, module, position)
                if isinstance(res, str):
                    old_con_dn = original_object.get('olddn')
                    if old_con_dn and pre_mapped_ad_dn != old_con_dn:
                        self._remove_dn_mapping(object['olddn'], old_con_dn)
                        self._update_group_related_caches(
                            property_type,
                            old_con_dn=old_con_dn,
                            old_ucs_dn=object['olddn'],
                            new_con_dn=pre_mapped_ad_dn,
                            new_ucs_dn=object['dn'],
                        )
                    # self._remove_dn_mapping(object['olddn'], '')  # we don't know the old ad-dn here anymore, will be checked by remove_dn_mapping
                    self._check_dn_mapping(object['dn'], pre_mapped_ad_dn)
                    result = True

            if object['modtype'] == 'modify':

                modified_dn = self.modify_in_ucs(property_type, object, module, position)
                modified_parent_dn = self.lo.parentDn(modified_dn).lower()
                parent_object_dn = self.lo.parentDn(object['dn']).lower()

                object['olddn'] = object.get('olddn', object['dn'])
                if not self.lo.compare_dn(modified_parent_dn, parent_object_dn):
                    # additionally move the object if position changed
                    # TODO: object['dn'] seems to be the correct target, but why?
                    ud.debug(ud.LDAP, ud.INFO, "sync_to_ucs: move object from %r to %r" % (modified_dn, object['dn']))
                    ucs_object = univention.admin.objects.get(module, None, self.lo, dn=modified_dn, position='')
                    ucs_object.open()
                    ucs_object.move(object['dn'])
                elif object['dn'].lower() != modified_dn.lower():
                    # TODO: in this case object['dn'] is the unchanged UCS DN, why?
                    # update group cache
                    object['dn'] = modified_dn

                old_con_dn = original_object.get('olddn', pre_mapped_ad_dn)
                self._update_group_related_caches(
                    property_type,
                    old_con_dn=old_con_dn,
                    old_ucs_dn=object['olddn'],
                    new_con_dn=pre_mapped_ad_dn,
                    new_ucs_dn=object['dn'],
                )

                if not self.lo.compare_dn(object['olddn'], object['dn']):
                    self._remove_dn_mapping(object['olddn'], old_con_dn)

                # Finally commit the current DNs to the DN mapping cache
                self._check_dn_mapping(object['dn'], pre_mapped_ad_dn)
                self.adcache.add_entry(guid, original_object.get('attributes'))
                result = True

            if not result:
                log.warning("Failed to get Result for DN (%r)", object['dn'])
                return False

            if object['modtype'] in ['add', 'modify']:
                for post_ucs_modify_function in self.property[property_type].post_ucs_modify_functions:
                    log.debug("Call post_ucs_modify_functions: %s", post_ucs_modify_function)
                    post_ucs_modify_function(self, property_type, object)
                    log.debug("Call post_ucs_modify_functions: %s (done)", post_ucs_modify_function)

            log.debug("Return  result for DN (%s)", object['dn'])
            return result

        except univention.admin.uexceptions.valueInvalidSyntax as msg:
            log.error("InvalidSyntax: %s (%r)", msg, object['dn'])
            return False
        except univention.admin.uexceptions.valueMayNotChange as msg:
            log.error("Value may not change: %s (%r)", msg, object['dn'])
            return False
        except ldap.SERVER_DOWN:
            raise
        except Exception:  # FIXME: which exception is to be caught?
            log.exception("Unknown Exception during sync_to_ucs")
            return False

    @staticmethod
    def _subtree_match(dn, subtree):
        x = ldap.dn.str2dn(subtree.lower())
        return ldap.dn.str2dn(dn.lower())[-len(x):] == x

    @staticmethod
    def _subtree_replace(dn, subtree, subtreereplace, case_folding=True):
        extra = ''
        if subtree.startswith(',') and subtreereplace.startswith(','):
            subtreereplace = subtreereplace[1:]
            subtree = subtree[1:]
            extra = ','
        _dn = ldap.dn.str2dn(dn.lower()) if case_folding else ldap.dn.str2dn(dn)
        _subtree = ldap.dn.str2dn(subtree.lower()) if case_folding else ldap.dn.str2dn(subtree)
        if _dn[-len(_subtree):] != _subtree or (extra and _dn == _subtree):
            return dn
        return ldap.dn.dn2str(ldap.dn.str2dn(dn)[:-len(_subtree)] + ldap.dn.str2dn(subtreereplace))

    # attributes ist ein dictionary von LDAP-Attributen und den zugeordneten Werten
    def _filter_match(self, filter, attributes):
        '''
        versucht eine Liste von Attributen auf einen LDAP-Filter zu matchen
        Besonderheiten des Filters:
        - immer case-sensitive
        - nur * als Wildcard
        - geht "lachser" mit Verschachtelten Klammern um
        '''
        filter_connectors = ['!', '&', '|']

        def list_lower(elements):
            if isinstance(elements, list):
                retlist = []
                for le in elements:
                    retlist.append(le.lower())
                return retlist
            else:
                return elements

        def dict_lower(dict_):
            if isinstance(dict_, dict):
                retdict = {}
                for key in dict_:
                    retdict[key.lower()] = dict_[key]
                return retdict
            else:
                return dict_

        def attribute_filter(filter, attributes):
            attributes = dict_lower(attributes)

            pos = filter.find('=')
            if pos < 0:
                raise ValueError(f'missing "=" in filter: {filter}')
            attribute = filter[:pos].lower()
            if not attribute:
                raise ValueError(f'missing attribute in filter: {filter}')
            value = filter[pos + 1:]

            if attribute.endswith(':1.2.840.113556.1.4.803:'):
                # bitwise filter
                attribute_name = attribute.replace(':1.2.840.113556.1.4.803:', '')
                attribute_value = attributes.get(attribute_name)
                if attribute_value:
                    try:
                        if isinstance(attribute_value, list):
                            attribute_value = int(attribute_value[0])
                        int_value = int(value)
                        return attribute_value & int_value == int_value
                    except ldap.SERVER_DOWN:
                        raise
                    except Exception:
                        log.warning("attribute_filter: Failed to convert attributes for bitwise filter")
                        return False

            if value == '*':
                return attribute in list_lower(attributes.keys())
            elif attribute in attributes:
                return value.lower().encode('UTF-8') in list_lower(attributes[attribute])
            else:
                return False

        def connecting_filter(filter, attributes):
            def walk(filter, attributes):
                def split(filter):
                    opened = []
                    closed = []
                    level = 0
                    for pos, char in enumerate(filter):
                        if char == '(':
                            if level == 0:
                                opened.append(pos)
                            level += 1
                        elif char == ')':
                            if level == 1:
                                closed.append(pos)
                            level -= 1
                        if level < 0:
                            raise ValueError(f"too many ')' in filter: {filter}")

                    if len(opened) != len(closed):
                        raise ValueError(f"'(' and ')' don't match in filter: {filter}")
                    filters = []
                    for i in range(len(opened)):
                        filters.append(filter[opened[i] + 1:closed[i]])
                    return filters

                if filter[0] == '(':
                    if not filter[-1] == ')':
                        raise ValueError(f"matching ) missing in filter: {filter}")
                    else:
                        filters = split(filter)
                        results = []
                        for filter in filters:
                            results.append(subfilter(filter, attributes))
                        return results
                else:
                    return [subfilter(filter, attributes)]

            if filter[0] == '!':
                return not subfilter(filter[1:], attributes)
            elif filter[0] == '|':
                return 1 in walk(filter[1:], attributes)
            elif filter[0] == '&':
                return 0 not in walk(filter[1:], attributes)

        def subfilter(filter, attributes):
            if filter[0] == '(':
                if not filter[-1] == ')':
                    raise ValueError(f"matching ) missing in filter: {filter}")
                else:
                    return subfilter(filter[1:-1], attributes)

            elif filter[0] in filter_connectors:
                return connecting_filter(filter, attributes)

            else:
                return attribute_filter(filter, attributes)

        return subfilter(filter, attributes)

    def _ignore_object(self, key, object):
        """
        parse if object should be ignored because of ignore_subtree, allow_subtree or ignore_filter

        :param key: the property_type from the mapping
        :param object: a mapped or unmapped AD or UCS object
        """
        if 'dn' not in object:
            log.debug("_ignore_object: ignore object without DN (key: %s)", key)
            return True  # ignore not existing object

        if (
            self.property[key].allow_subtree
            and not any(self._subtree_match(object['dn'], dn) for dn in self.property[key].allow_subtree)
            and (not self.allow_subtree_ancestors or not any(DN(subtree_dn).endswith(object['dn']) for subtree_dn in self.property[key].allow_subtree))
        ):
            log.debug('_ignore_object: ignore object because it is not in one of the allowed subtrees: [%r:%r]', key, object['dn'])
            return True

        if self.property[key].allow_filter:
            if not self._filter_match(self.property[key].allow_filter, object['attributes']):
                log.debug("_ignore_object: ignore object because of allow_filter: [%r:%r]", key, object['dn'])
                return True

        for subtree in self.property[key].ignore_subtree:
            if self._subtree_match(object['dn'], subtree):
                log.debug("_ignore_object: ignore object because of subtree match: [%r:%r]", key, object['dn'])
                return True

        if self.property[key].ignore_filter and self._filter_match(self.property[key].ignore_filter, object['attributes']):
            log.debug("_ignore_object: ignore object because of ignore_filter: [%r:%r]", key, object['dn'])
            return True

        if self.property[key].match_filter and not self._filter_match(self.property[key].match_filter, object['attributes']):
            log.debug("_ignore_object: ignore object because of match_filter: [%r:%r]", key, object['dn'])
            return True

        log.debug("_ignore_object: Do not ignore %r:%r", key, object['dn'])

        return False

    def _object_mapping(self, key, old_object, object_type='con'):
        """
        Create a mapped object from AD or UCS object definition.

        :param key:
            the mapping key
        :param old_object:
            the object definition in univention directory listener style
        :ptype old_object: dict
        :param object_type:
            "con" if `old_object` is a AD object.
            "ucs" if `old_object` is a UCS object.
        :ptype object_type: str
        """
        log.debug("_object_mapping: map with key %s and type %s", key, object_type)
        # ingoing object format:
        #    'dn': dn
        #    'modtype': 'add', 'delete', 'modify', 'move'
        #    'attributes': { attr: [values] }
        #       'olddn' : dn (only on move)
        # outgoing object format:
        #    'dn': dn
        #    'modtype':  'add', 'delete', 'modify', 'move'
        #    'attributes': { attr: [values] }
        #       'olddn' : dn (only on move)

        if object_type == 'ucs':
            return self._object_mapping_ucs(key, old_object)
        else:
            return self._object_mapping_con(key, old_object)

    def _object_mapping_ucs(self, key, old_object):
        object = copy.deepcopy(old_object)

        # DN mapping
        dn_mapping_stored = []
        for dntype in ['dn', 'olddn']:  # check if all available dn's are already mapped
            if dntype in object and self._get_dn_by_ucs(object[dntype]):
                # if this is a "modrdn", don't map the target position by cache, but actually
                # move the object
                if (dntype == 'dn') and ('olddn' in object):
                    continue

                object[dntype] = self._get_dn_by_ucs(object[dntype])
                object[dntype] = self.dn_mapped_to_base(object[dntype], self.lo_ad.base)
                dn_mapping_stored.append(dntype)

        try:
            MAPPING = self.property[key]
        except KeyError:
            return object

        # DN mapping functions
        for function in MAPPING.dn_mapping_function:
            object = function(self, object, dn_mapping_stored, isUCSobject=True)

        for dntype in ['dn', 'olddn']:
            if dntype in object and dntype not in dn_mapping_stored:
                dn_mapped = object[dntype]
                # save the old rdn with the correct upper and lower case
                rdn_store = ldap.dn.explode_dn(dn_mapped)[0]
                if self.lo_ad.base == dn_mapped[-len(self.lo_ad.base):] and len(self.lo_ad.base) > len(self.lo.base):
                    # avoid additional _subtree_replace in case dn_mapping_function already found an AD DN (can happen for account type objects)
                    log.debug("The dn %s is already converted to the AD base, don't do additional ldap base mapping.", dn_mapped)
                else:
                    for mapping in MAPPING.position_mapping:  # note: position_mapping == [] by default
                        replaced_dn_mapped_lower = self._subtree_replace(dn_mapped.lower(), mapping[0].lower(), mapping[1])
                        if replaced_dn_mapped_lower != dn_mapped.lower():
                            # explanation: only change dn_mapped if _subtree_replace actually changed anything and not only MixedCase.lower()
                            dn_mapped = replaced_dn_mapped_lower

                    if dn_mapped == object[dntype]:
                        if self.lo_ad.base == dn_mapped[-len(self.lo_ad.base):] and len(self.lo_ad.base) > len(self.lo.base):
                            # Introduced via Bug #13745#c14 : avoid default _subtree_replace in case position_mapping was applied
                            log.debug("The dn %s is already converted to the AD base, don't do this again.", dn_mapped)
                        else:
                            dn_mapped = self._subtree_replace(object[dntype].lower(), self.lo.base.lower(), self.lo_ad.base)  # FIXME: lo_ad may change with other connectors
                # write the correct upper and lower case back to the DN
                object[dntype] = dn_mapped.replace(dn_mapped[0:len(rdn_store)], rdn_store, 1)

        object_out = object

        for attribute, values in list(object['attributes'].items()):
            for attr_key, attributes in (MAPPING.attributes or {}).items():
                if attribute.lower() == attributes.ldap_attribute.lower():
                    # mapping function
                    if hasattr(attributes, 'mapping'):
                        # direct mapping
                        if attributes.mapping[0]:
                            object_out['attributes'][attributes.con_attribute] = attributes.mapping[0](self, key, object)
                    else:
                        if attributes.con_other_attribute:
                            object_out['attributes'][attributes.con_attribute] = [values[0]]
                            object_out['attributes'][attributes.con_other_attribute] = values[1:]
                        else:
                            object_out['attributes'][attributes.con_attribute] = values

                    # mapping_table
                    for ucsval, conval in MAPPING.mapping_table.get(attr_key, []):
                        if isinstance(object_out['attributes'][attributes.con_attribute], list):
                            encoding = attributes.con_attribute_encoding or 'UTF-8'
                            object_out['attributes'][attributes.con_attribute] = [
                                conval.encode(encoding) if x.lower() == ucsval.encode(encoding).lower() else x
                                for x in object_out['attributes'][attributes.con_attribute]
                            ]

            for post_attributes in (MAPPING.post_attributes or {}).values():
                if attribute.lower() == post_attributes.ldap_attribute.lower():
                    if hasattr(post_attributes, 'mapping'):
                        if post_attributes.mapping[0]:
                            object_out['attributes'][post_attributes.con_attribute] = post_attributes.mapping[0](self, key, object)
                    else:
                        if post_attributes.con_other_attribute:
                            object_out['attributes'][post_attributes.con_attribute] = [values[0]]
                            object_out['attributes'][post_attributes.con_other_attribute] = values[1:]
                        else:
                            object_out['attributes'][post_attributes.con_attribute] = values

        log.trace("_object_mapping_ucs: object_out : %r", object_out)
        return object_out

    def _object_mapping_con(self, key, old_object):
        object = copy.deepcopy(old_object)

        # DN mapping
        dn_mapping_stored = []
        for dntype in ['dn', 'olddn']:  # check if all available dn's are already mapped
            if dntype in object and self._get_dn_by_con(object[dntype]):
                object[dntype] = self._get_dn_by_con(object[dntype])
                object[dntype] = self.dn_mapped_to_base(object[dntype], self.lo.base)
                dn_mapping_stored.append(dntype)

        try:
            MAPPING = self.property[key]
        except KeyError:
            return object

        # DN mapping functions
        for function in MAPPING.dn_mapping_function:
            object = function(self, object, dn_mapping_stored, isUCSobject=False)

        for dntype in ['dn', 'olddn']:
            if dntype in object and dntype not in dn_mapping_stored:
                dn_mapped = object[dntype]
                # save the old rdn with the correct upper and lower case
                rdn_store = ldap.dn.explode_dn(dn_mapped)[0]
                for mapping in MAPPING.position_mapping:  # note: position_mapping == [] by default
                    replaced_dn_mapped_lower = self._subtree_replace(dn_mapped.lower(), mapping[1].lower(), mapping[0])
                    if replaced_dn_mapped_lower != dn_mapped.lower():
                        # explanation: only change dn_mapped if _subtree_replace actually changed anything and not only MixedCase.lower()
                        dn_mapped = replaced_dn_mapped_lower

                if dn_mapped == object[dntype]:
                    if self.lo.base == dn_mapped[-len(self.lo.base):] and len(self.lo.base) > len(self.lo_ad.base):
                        # Introduced via Bug #13745#c14 : avoid default _subtree_replace in case position_mapping was applied
                        log.debug("The dn %s is already converted to the UCS base, don't do this again.", dn_mapped)
                    else:
                        dn_mapped = self._subtree_replace(dn_mapped.lower(), self.lo_ad.base.lower(), self.lo.base)  # FIXME: lo_ad may change with other connectors
                # write the correct upper and lower case back to the DN
                dn_mapped = dn_mapped.replace(dn_mapped[0:len(rdn_store)], rdn_store, 1)
                # group_members_sync_to_ucs uses _object_mapping to map AD group
                # member DNs to OpenLDAP group member DNs. To avoid cache
                # inconsistencies between the use of AD DN escaping (using '\+')
                # and OpenLDAP DN escaping (using '\2B') we convert AD DNs to
                # OpenLDAP notation here. TODO: In _object_mapping_ucs we could
                # do the inverse simply by using dn2str(str2dn(dn)).
                object[dntype] = RFC4514_dn.to_openldap(dn_mapped)

        object_out = object

        # other mapping
        # Filter out Configuration objects w/o DN
        if object['dn'] is None:
            return object_out

        for attribute, values in sorted(object['attributes'].items()):
            for attr_key, attributes in (MAPPING.attributes or {}).items():
                if attribute.lower() == attributes.con_attribute.lower():
                    # mapping function
                    if hasattr(attributes, 'mapping'):
                        # direct mapping
                        if attributes.mapping[1]:
                            object_out['attributes'][attributes.ldap_attribute] = attributes.mapping[1](self, key, object)
                    else:
                        if attributes.con_other_attribute and object['attributes'].get(attributes.con_other_attribute):
                            object_out['attributes'][attributes.ldap_attribute] = values + object['attributes'].get(attributes.con_other_attribute)
                        else:
                            object_out['attributes'][attributes.ldap_attribute] = values

                    # mapping_table
                    for ucsval, conval in MAPPING.mapping_table.get(attr_key, []):
                        if isinstance(object_out['attributes'][attributes.ldap_attribute], list):
                            encoding = attributes.con_attribute_encoding or 'UTF-8'
                            object_out['attributes'][attributes.ldap_attribute] = [
                                ucsval.encode(encoding) if x.lower() == conval.encode(encoding).lower() else x
                                for x in object_out['attributes'][attributes.ldap_attribute]
                            ]

            for post_attributes in (MAPPING.post_attributes or {}).values():
                if attribute.lower() == post_attributes.con_attribute.lower():
                    if hasattr(post_attributes, 'mapping'):
                        if post_attributes.mapping[1]:
                            object_out['attributes'][post_attributes.ldap_attribute] = post_attributes.mapping[1](self, key, object)
                    else:
                        if post_attributes.con_other_attribute and object['attributes'].get(post_attributes.con_other_attribute):
                            object_out['attributes'][post_attributes.ldap_attribute] = values + object['attributes'].get(post_attributes.con_other_attribute)
                        else:
                            object_out['attributes'][post_attributes.ldap_attribute] = values

        log.trace("_object_mapping_con: object_out : %r", object_out)
        return object_out

    def identify_udm_object(self, dn, attrs):
        """Get the type of the specified UCS object"""
        for k in self.property.keys():
            if self.modules[k].identify(dn, attrs):
                return self.modules[k], k
            for m in self.modules_others.get(k, []):
                if m and m.identify(dn, attrs):
                    return m, k
        return None, None
