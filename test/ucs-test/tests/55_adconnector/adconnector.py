import contextlib
import subprocess
from time import sleep

import ldap

import univention.config_registry
import univention.testing.connector_common as tcommon
import univention.testing.ucr as testing_ucr
from univention.config_registry import handler_set as ucr_set
from univention.connector import ad
from univention.testing import ldap_glue


configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()

LDAP_SERVER_SHOW_DELETED_OID = "1.2.840.113556.1.4.417"
LDB_CONTROL_DOMAIN_SCOPE_OID = "1.2.840.113556.1.4.1339"


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
    if min_wait_time > synctime:
        synctime = min_wait_time
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

    def wait_for_sync(self):
        return wait_for_sync()

    def restart(self):
        return restart_adconnector()

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

    def move(self, ad_dn, new_dn):
        self._ad.move(ad_dn, new_dn)
        self.wait_for_sync()
        return new_dn

    def set_attributes(self, ad_dn, attrs):
        self._ad.set_attributes(ad_dn, **attrs)
        self.wait_for_sync()

    def delete_object(self, ad_dn, udm_dn):
        self._ad.delete(ad_dn)
        try:
            self._created.remove((ad_dn, udm_dn))
        except ValueError:
            pass
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

    def restore_object(self, ad_dn):
        cn, *parent_dn = ldap.dn.str2dn(ad_dn)
        if not (cn and parent_dn):
            return
        parent_dn_string = ldap.dn.dn2str(parent_dn)
        filter_ad = ldap.filter.filter_format('(&(cn=%s\nDEL:*)(lastKnownParent=%s))', [cn[0][1], parent_dn_string])
        restore_dn = self._ad.search(filter_ad)[0][0][0]
        self._ad.lo.modify_ext_s(
            restore_dn,
            [(ldap.MOD_REPLACE, 'distinguishedName', restore_dn.encode('UTF-8'))],
            serverctrls=[ldap.controls.LDAPControl(LDAP_SERVER_SHOW_DELETED_OID, criticality=1)],
        )

    def get_dn(self, cn):
        filter = f'(cn={cn})'
        return self._ad.search(filter)[0][0]


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
