#!/usr/share/ucs-test/runner pytest-3 -s
## desc: "Test the UCS<->AD sync with ignorefilter in sync mode with {users,groups,windowscomputer,cn,ou}"
## exposure: dangerous
## packages:
## - univention-ad-connector
## bugs:
##  - 55150
## tags:
##  - skip_admember

import pytest
from ldap.dn import dn2str, str2dn
from ldap.filter import filter_format

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
from univention.testing.connector_common import NormalContainer, NormalGroup, NormalOU, NormalUser, NormalWindows

from adconnector import connector_running_on_this_host, connector_setup2


OBJECTS = [{
    "object_class": "users/user",
    "identifying_attr": "uid",
    "identifying_udm_attr": "username",
    "filtered_attr": "givenName",
    "filtered_udm_attr": "firstname",
    "non_filtered_attr": "sn",
    "non_filtered_udm_attr": "lastname",
    "object_attrs": NormalUser().user,
}, {
    "object_class": "groups/group",
    "identifying_attr": "cn",
    "identifying_udm_attr": "name",
    "filtered_attr": "cn",
    "filtered_udm_attr": "name",
    "non_filtered_attr": "description",
    "non_filtered_udm_attr": "description",
    "object_attrs": NormalGroup().group,
}, {
    "object_class": "computers/windows",
    "identifying_attr": "cn",
    "identifying_udm_attr": "name",
    "filtered_attr": "description",
    "filtered_udm_attr": "description",
    "non_filtered_attr": "operatingSystemVersion",
    "non_filtered_udm_attr": "operatingSystemVersion",
    "object_attrs": NormalWindows().obj,
}, {
    "object_class": "container/cn",
    "identifying_attr": "cn",
    "identifying_udm_attr": "name",
    "filtered_attr": "description",
    "filtered_udm_attr": "description",
    "non_filtered_attr": "cn",
    "non_filtered_udm_attr": "name",
    "object_attrs": NormalContainer().obj,
}, {
    "object_class": "container/ou",
    "identifying_attr": "ou",
    "identifying_udm_attr": "name",
    "filtered_attr": "description",
    "filtered_udm_attr": "description",
    "non_filtered_attr": "ou",
    "non_filtered_udm_attr": "name",
    "object_attrs": NormalOU().obj,
}]


@pytest.mark.parametrize("object_class,identifying_attr,identifying_udm_attr,filtered_attr,filtered_udm_attr,non_filtered_attr,non_filtered_udm_attr,object_attrs", [(obj["object_class"], obj["identifying_attr"], obj["identifying_udm_attr"], obj["filtered_attr"], obj["filtered_udm_attr"], obj["non_filtered_attr"], obj["non_filtered_udm_attr"], obj["object_attrs"]) for obj in OBJECTS])
@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention AD Connector not configured.")
def test_user_sync_from_ad_to_udm_with_ignorefilter(object_class, identifying_attr, identifying_udm_attr, filtered_attr, filtered_udm_attr, non_filtered_attr, non_filtered_udm_attr, object_attrs):
    """
    This test creates an object in AD while no filter is set.
    Then the filter is activated with an attr=value that the object was created with (now it should be ignored)
    Then some other attribute is changed *in AD*; nothing should be synced
    Then that attribute is changed again *in UDM*; nothing should be synced
    Then the filtered attribute is changed in AD, effectively "leaving" the filter: The changes should be synced, the change from before should also be "corrected"
    Then the filtered attribute is changed *in UDM*; this should also result in a sync
    """
    with connector_setup2("sync") as ad, udm_test.UCSTestUDM() as udm, ucr_test.UCSTestConfigRegistry() as ucr:
        print("\nCreating AD user within an ignorefilter (which is not active yet!)\n")
        identifying_udm_attr_value, filtered_attr_value, non_filtered_attr_value = object_attrs[identifying_udm_attr], object_attrs[filtered_udm_attr], object_attrs[non_filtered_udm_attr]
        ad_dn = ad.create_object(object_class, object_attrs)
        udm_dn = udm._lo.searchDn(filter_format(f"{identifying_attr}=%s", [identifying_udm_attr_value.decode("utf-8")]))[0]
        udm._cleanup.setdefault(object_class, []).append(udm_dn)  # FIXME: needed for udm.modify_object
        udm.verify_udm_object(object_class, udm_dn, object_attrs)
        ignorefilter = filter_format(f"({filtered_attr}=%s)", [filtered_attr_value.decode("utf-8")])
        filter_name = object_class.split('/')[1]
        if filter_name == "windows":
            filter_name = "windowscomputer"
        if filter_name == "cn":
            filter_name = "container"
        ucr.handler_set([f"connector/ad/mapping/{filter_name}/ignorefilter={ignorefilter}"])
        ad.restart()

        print("\nModifying AD object while within ignorefilter\n")
        object_attrs[non_filtered_udm_attr] = non_filtered_attr_value * 2
        if non_filtered_attr == identifying_attr:
            # if attr == id, we effectively move the object, not just modify it
            parent = str2dn(ad_dn)[1:]
            new_dn = dn2str([[(non_filtered_attr, object_attrs[non_filtered_udm_attr].decode("utf-8"), 1)], *parent])
            ad_dn = ad.move(ad_dn, new_dn)
        else:
            ad.set_attributes(ad_dn, {non_filtered_attr: [object_attrs[non_filtered_udm_attr]]})
        with pytest.raises(AssertionError):
            udm.verify_udm_object(object_class, udm_dn, object_attrs)
        print("\nModifying UDM object while within ignorefilter\n")
        udm_dn = udm.modify_object(object_class, dn=udm_dn, **{non_filtered_udm_attr: non_filtered_attr_value.decode("utf-8") * 3})
        ad.wait_for_sync()
        ad.verify_object(object_class, ad_dn, object_attrs)

        print("\nModifying AD object out of ignorefilter\n")
        object_attrs[filtered_udm_attr] = filtered_attr_value * 2
        if filtered_attr == identifying_attr:
            # if attr == id, we effectively move the object, not just modify it
            new_rdn = object_attrs[filtered_udm_attr].decode("utf-8")
            parent = str2dn(ad_dn)[1:]
            new_dn = dn2str([[(filtered_attr, new_rdn, 1)], *parent])
            ad_dn = ad.move(ad_dn, new_dn)
            # in this case, the UDM object wont sync as it is still matching the ignore filter. too bad...
            object_attrs[filtered_udm_attr] = filtered_attr_value
            object_attrs[non_filtered_udm_attr] = non_filtered_attr_value * 3
            udm.verify_udm_object(object_class, udm_dn, object_attrs)
            # yupp, still the same. test ends here
            return
        else:
            ad.set_attributes(ad_dn, {filtered_attr: [object_attrs[filtered_udm_attr]]})
            if filtered_attr == filtered_udm_attr:
                # both attributes are the same, so although we are escapted the filter on the AD side
                # with the set_attributes above, we still don't sync because the filter applies to
                # the UDM object
                with pytest.raises(AssertionError):
                    udm.verify_udm_object(object_class, udm_dn, object_attrs)
                return
        udm.verify_udm_object(object_class, udm_dn, object_attrs)
        print("\nModifying UDM object while out of ignorefilter\n")
        udm.modify_object(object_class, dn=udm_dn, **{non_filtered_udm_attr: non_filtered_attr_value.decode("utf-8") * 3})
        ad.wait_for_sync()
        with pytest.raises(AssertionError):
            ad.verify_object(object_class, ad_dn, object_attrs)
