import base64
import contextlib
import subprocess
from time import sleep
from types import SimpleNamespace

import ldap

import univention.admin.modules
import univention.admin.objects
import univention.admin.uldap
import univention.config_registry
import univention.testing.connector_common as tcommon
import univention.testing.ucr as testing_ucr
from univention.config_registry import handler_set as ucr_set
from univention.connector import ad, configdb
from univention.testing import ldap_glue
from univention.testing.strings import random_username


configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


class ADConnection(ldap_glue.ADConnection):
    """helper functions to modify AD-objects"""

    @classmethod
    def decode_sid(cls, sid):
        return ad.decode_sid(sid)


def connector_running_on_this_host():
    return configRegistry.is_true("connector/ad/autostart")


def restart_adconnector():
    print("Restarting AD-Connector")
    subprocess.check_call(["service", "univention-ad-connector", "restart"])


def ad_in_sync_mode(sync_mode, configbase='connector'):
    """Set the AD-Connector into the given `sync_mode` restart."""
    ucr_set([f'{configbase}/ad/mapping/syncmode={sync_mode}'])
    restart_adconnector()


def wait_for_sync(min_wait_time=0):
    synctime = int(configRegistry.get("connector/ad/poll/sleep", 5))
    synctime = ((synctime + 3) * 2)
    synctime = max(synctime, min_wait_time)
    print(f"Waiting {synctime} seconds for sync...")
    sleep(synctime)


@contextlib.contextmanager
def connector_setup(sync_mode):
    user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
    group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
    with testing_ucr.UCSTestConfigRegistry():
        ucr_set([user_syntax, group_syntax])
        tcommon.restart_univention_cli_server()
        ad_in_sync_mode(sync_mode)
        yield


class _Connector:
    def __init__(self):
        self._ad = ADConnection()
        self._created = []
        self.ldap_base = self._ad.adldapbase
        self.domain = self._ad.addomain
        self.cache_internal = configdb('/etc/univention/connector/internal.sqlite')
        self.connector_log = '/var/log/univention/connector-ad.log'

    def tracebacks(self):
        traceback_started = False
        tracebacks = []
        traceback = ""
        with open(self.connector_log) as f_log:
            for line in f_log.readlines():
                if not traceback_started and 'Traceback (most recent call last)' in line:
                    traceback_started = True
                    traceback = f'{traceback}{line}'
                    continue
                if traceback_started and line[0].isalnum():
                    traceback = f'{traceback}{line}'
                    tracebacks.append(traceback)
                    traceback_started = False
                    traceback = ""
                if traceback_started:
                    traceback = f'{traceback}{line}'
        return tracebacks

    # TODO: remove from 504test_group_cache_after_move.py
    def create_ou_structure_and_user(self, udm, in_ad=False):
        # create user and groups in AD
        ou1_name = f'ou1-{random_username(mixed_case=True)}'
        ou11_name = f'ou11-{random_username(mixed_case=True)}'
        ou2_name = f'ou2-{random_username(mixed_case=True)}'
        group1_name = f'grp1-{random_username(mixed_case=True)}'
        group2_name = f'grp2-{random_username(mixed_case=True)}'
        username = random_username(mixed_case=True)
        if in_ad:
            ou1_dn_ad = self.create_ou(ou1_name, wait_for_replication=False)
            ou2_dn_ad = self.create_ou(ou2_name, wait_for_replication=False)
            ou11_dn_ad = self.create_ou(ou11_name, position=ou1_dn_ad, wait_for_replication=False)
            user_dn_ad = self.create_user(username, position=ou11_dn_ad, wait_for_replication=False)
            group1_dn_ad = self.create_group(group1_name, wait_for_replication=False)
            group2_dn_ad = self.create_group(group2_name, wait_for_replication=False)
            self.add_to_group(group1_dn_ad, user_dn_ad)
            self.wait_for_sync()
            user_dn = self.ucs_dn(user_dn_ad)
            group1_dn = self.ucs_dn(group1_dn_ad)
            group2_dn = self.ucs_dn(group2_dn_ad)
            ou1_dn = self.ucs_dn(ou1_dn_ad)
            ou2_dn = self.ucs_dn(ou2_dn_ad)
            ou11_dn = self.ucs_dn(ou11_dn_ad)
        else:
            ou1_dn = udm.create_object('container/ou', name=ou1_name, wait_for_replication=False)
            ou2_dn = udm.create_object('container/ou', name=ou2_name, wait_for_replication=False)
            ou11_dn = udm.create_object('container/ou', name=ou11_name, position=ou1_dn, wait_for_replication=False)
            group1_dn, _ = udm.create_group(wait_for_replication=False)
            group2_dn, _ = udm.create_group(wait_for_replication=False)
            user_dn, username = udm.create_user(groups=[group1_dn], position=ou11_dn, wait_for_replication=False)
            self.wait_for_sync()
            user_dn_ad = self.ad_dn(user_dn)
            group1_dn_ad = self.ad_dn(group1_dn)
            group2_dn_ad = self.ad_dn(group2_dn)
            ou1_dn_ad = self.ad_dn(ou1_dn)
            ou2_dn_ad = self.ad_dn(ou2_dn)
            ou11_dn_ad = self.ad_dn(ou11_dn)

        return SimpleNamespace(
            ou1_name=ou1_name,
            ou1_dn=ou1_dn,
            ou1_dn_ad=ou1_dn_ad,
            ou11_name=ou11_name,
            ou11_dn=ou11_dn,
            ou11_dn_ad=ou11_dn_ad,
            ou2_name=ou2_name,
            ou2_dn=ou2_dn,
            ou2_dn_ad=ou2_dn_ad,
            group1_dn=group1_dn,
            group1_dn_ad=group1_dn_ad,
            group2_dn=group2_dn,
            group2_dn_ad=group2_dn_ad,
            user_dn=user_dn,
            user_dn_ad=user_dn_ad,
            username=username,
            user_position_ad=ou11_dn_ad,
            user_position=ou11_dn,
        )

    def get_logs(self, level='PROCESS', mode='sync to ucs', object_type='user', change_type='modify'):
        lines = []
        with open(self.connector_log) as f_log:
            for line in f_log.readlines():
                if f'({level}' in line and f'{mode}:' in line and f' {object_type}]' in line and f' {change_type}]' in line:
                    lines.append(line)
        return lines

    def last_traceback(self):
        tracebacks = self.tracebacks()
        if tracebacks:
            return tracebacks[-1]
        return None

    def wait_for_sync(self):
        return wait_for_sync()

    def restart(self):
        return restart_adconnector()

    def get(self, dn):
        return self._ad.get(dn)

    def ad_dn(self, dn):
        return self.cache_internal.get('DN Mapping UCS', dn.lower())

    def ucs_dn(self, dn):
        return self.cache_internal.get('DN Mapping CON', dn.lower())

    def __encode_guid(self, guid):
        return base64.b64encode(guid).decode('ASCII')

    def guid(self, dn):
        return self.get(dn)['objectGUID'][0]

    def cache_guid2dn(self, guid):
        return self.cache_internal.get('AD GUID', self.__encode_guid(guid))

    def get_groups(self, dn):
        attr = self._ad.get(dn)
        return {x.decode('utf-8').casefold() for x in attr.get('memberOf', [])}

    def remove_from_group(self, group, dn):
        return self._ad.remove_from_group(group, dn.encode('UTF-8'))

    def add_to_group(self, group, dn):
        return self._ad.add_to_group(group, dn.encode('UTF-8'))

    def create_ou(self, name, position=None, wait_for_replication=True):
        dn = self._ad.createou(name, position=position)
        if wait_for_replication:
            self.wait_for_sync()
        return dn

    def create_user(self, name, position=None, wait_for_replication=True, **attributes):
        dn = self._ad.createuser(name, position=position, **attributes)
        if wait_for_replication:
            self.wait_for_sync()
        return dn

    def create_group(self, name, position=None, wait_for_replication=True):
        dn = self._ad.group_create(name, position=position)
        if wait_for_replication:
            self.wait_for_sync()
        return dn

    def create_object(self, object_type, attrs):
        if object_type == "users/user":
            dn = self._ad.createuser(attrs["username"], None, **tcommon.map_udm_user_to_con(attrs))
        elif object_type == "groups/group":
            dn = self._ad.group_create(attrs["name"].decode("utf-8"), None, **tcommon.map_udm_group_to_con(attrs))
        elif object_type == "computers/windows":
            dn = self._ad.windows_create(attrs["name"].decode("utf-8"), None, **tcommon.map_udm_windows_to_con(attrs))
        elif object_type == "container/cn":
            dn = self._ad.container_create(attrs["name"].decode("utf-8"), None, attrs.get("description"))
        elif object_type == "container/ou":
            dn = self._ad.createou(attrs["name"].decode("utf-8"), None, attrs.get("description"))
        else:
            raise NotImplementedError(f"Dont know how to create {object_type}")
        self.wait_for_sync()
        return dn

    def rename(self, ad_dn, name, wait_for_replication=True):
        rdn_attr = 'ou' if ad_dn.startswith('ou=') else 'cn'
        exploded = ldap.dn.str2dn(ad_dn)
        new_rdn = [(rdn_attr, name, ldap.AVA_STRING)]
        new_position = exploded[1:]
        new_dn = ldap.dn.dn2str([new_rdn] + new_position)
        self._ad.move(ad_dn, new_dn)
        if wait_for_replication:
            self.wait_for_sync()
        return new_dn

    def move(self, ad_dn, new_dn, wait_for_replication=True):
        self._ad.move(ad_dn, new_dn)
        if wait_for_replication:
            self.wait_for_sync()
        return new_dn

    def set_attributes(self, ad_dn, attrs, wait_for_replication=True):
        self._ad.set_attributes(ad_dn, **attrs)
        if wait_for_replication:
            self.wait_for_sync()

    def delete_attribute(self, dn, attr, wait_for_replication=True):
        self._ad.delete_attribute(dn, attr)
        if wait_for_replication:
            self.wait_for_sync()

    def delete_object(self, ad_dn, udm_dn, wait_for_replication=True):
        self._ad.delete(ad_dn)
        try:
            self._created.remove((ad_dn, udm_dn))
        except ValueError:
            pass
        if wait_for_replication:
            self.wait_for_sync()

    def verify_object(self, object_type, ad_dn, obj):
        if object_type == "users/user":
            obj = tcommon.map_udm_user_to_con(obj)
        elif object_type == "groups/group":
            obj = tcommon.map_udm_group_to_con(obj)
        elif object_type == "computers/windows":
            obj = tcommon.map_udm_windows_to_con(obj)
        elif object_type == "container/cn":
            obj = tcommon.map_udm_container_to_con(obj)
        elif object_type == "container/ou":
            obj = tcommon.map_udm_ou_to_con(obj)
        self._ad.verify_object(ad_dn, obj)


@contextlib.contextmanager
def connector_setup2(mode):
    with connector_setup(mode):
        connector = _Connector()
        try:
            yield connector
        finally:
            for ad_dn, udm_dn in connector._created[::-1]:
                connector.delete_object(ad_dn, udm_dn)
            connector.restart()
