#!/usr/bin/python3
#
# Univention S4 Connector
#  control the password sync communication with the s4 password service
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import binascii
import time
from datetime import datetime
from logging import getLogger

import heimdal
import ldap
from ldap.controls import LDAPControl
from samba.dcerpc import drsblobs
from samba.ndr import ndr_pack, ndr_print, ndr_unpack

import univention.s4connector.s4
from univention.admin import uexceptions
from univention.logging import Structured
from univention.s4connector.s4 import format_escaped


log = Structured(getLogger("LDAP").getChild(__name__))


class Krb5Context:
    def __init__(self):
        self.ctx = heimdal.context()
        self.etypes = self.ctx.get_permitted_enctypes()
        self.etype_ids = [et.toint() for et in self.etypes]


krb5_context = Krb5Context()


def calculate_krb5key(unicodePwd, supplementalCredentials, kvno=0):
    up_blob = unicodePwd
    sc_blob = supplementalCredentials

    keys = []
    keytypes = []
    context = heimdal.context()

    if up_blob:
        # log.debug("calculate_krb5key: up_blob: %s" % binascii.b2a_base64(up_blob))
        assert len(up_blob) == 16
        key = heimdal.keyblock_raw(context, 23, up_blob)
        keys.append(heimdal.asn1_encode_key(key, None, kvno))

    if sc_blob:
        # log.debug("calculate_krb5key: sc_blob: %s" % binascii.b2a_base64(sc_blob))
        try:
            sc = ndr_unpack(drsblobs.supplementalCredentialsBlob, sc_blob)
            for p in sc.sub.packages:
                krb = None
                log.debug("calculate_krb5key: parsing %s blob", p.name)
                if p.name == "Primary:Kerberos":
                    krb_blob = binascii.unhexlify(p.data)
                    krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
                    assert krb.version == 3

                    for k in krb.ctr.keys:
                        if k.keytype not in keytypes:
                            log.debug("calculate_krb5key: ctr3.key.keytype: %s", k.keytype)
                            try:
                                key = heimdal.keyblock_raw(context, k.keytype, k.value)
                                krb5SaltObject = heimdal.salt_raw(context, krb.ctr.salt.string)
                                keys.append(heimdal.asn1_encode_key(key, krb5SaltObject, kvno))
                                keytypes.append(k.keytype)
                            except Exception:  # FIXME: which exception?
                                if k.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) for this
                                    if k.value == up_blob:  # the known case
                                        log.debug("calculate_krb5key: ignoring arc4 NThash with special keytype %s in %s", k.keytype, p.name)
                                    else:  # unknown special case
                                        log.debug("calculate_krb5key: ignoring unknown key with special keytype %s in %s", k.keytype, p.name)
                                else:
                                    log.exception("calculate_krb5key: krb5Key with keytype %s could not be parsed in %s. Ignoring this keytype.", k.keytype, p.name)

                elif p.name == "Primary:Kerberos-Newer-Keys":
                    krb_blob = binascii.unhexlify(p.data)
                    krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
                    assert krb.version == 4

                    for k in krb.ctr.keys:
                        if k.keytype not in keytypes:
                            log.debug("calculate_krb5key: ctr4.key.keytype: %s", k.keytype)
                            try:
                                key = heimdal.keyblock_raw(context, k.keytype, k.value)
                                krb5SaltObject = heimdal.salt_raw(context, krb.ctr.salt.string)
                                keys.append(heimdal.asn1_encode_key(key, krb5SaltObject, kvno))
                                keytypes.append(k.keytype)
                            except Exception:  # FIXME: which exception?
                                if k.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) for this
                                    if k.value == up_blob:  # the known case
                                        log.debug("calculate_krb5key: ignoring arc4 NThash with special keytype %s in %s", k.keytype, p.name)
                                    else:  # unknown special case
                                        log.debug("calculate_krb5key: ignoring unknown key with special keytype %s in %s", k.keytype, p.name)
                                else:
                                    log.exception("calculate_krb5key: krb5Key with keytype %s could not be parsed in %s. Ignoring this keytype.", k.keytype, p.name)

        except Exception as exc:
            if isinstance(exc, RuntimeError) and len(exc.args) == 2 and exc.args[1] == 'Buffer Size Error' or exc.args[0] == 11:
                log.warning("calculate_krb5key: '%s' while unpacking supplementalCredentials:: %s", exc, binascii.b2a_base64(sc_blob))
                log.warning("calculate_krb5key: the krb5Keys from the PrimaryKerberosBlob could not be parsed. Continuing anyway.")
            else:
                log.exception("calculate_krb5key: the krb5Keys from the PrimaryKerberosBlob could not be parsed. Continuing anyway.")

    return keys


def calculate_supplementalCredentials(ucs_krb5key, old_supplementalCredentials, nt_hash):
    old_krb = {}
    if old_supplementalCredentials:
        sc = ndr_unpack(drsblobs.supplementalCredentialsBlob, old_supplementalCredentials)

        for p in sc.sub.packages:
            log.debug("calculate_supplementalCredentials: parsing %s blob", p.name)
            if p.name == "Primary:Kerberos":
                krb_blob = binascii.unhexlify(p.data)
                try:
                    krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
                    assert krb.version == 3
                    old_krb['ctr3'] = krb.ctr
                    for k in krb.ctr.keys:
                        log.debug("calculate_supplementalCredentials: ctr3.key.keytype: %s", k.keytype)
                except Exception:  # FIXME: which exception?
                    log.exception("calculate_supplementalCredentials: ndr_unpack of S4 Primary:Kerberos blob failed.")
                    log.error("calculate_supplementalCredentials: Continuing anyway, Primary:Kerberos (DES keys) blob will be missing in supplementalCredentials ctr3.old_keys.")
            elif p.name == "Primary:Kerberos-Newer-Keys":
                krb_blob = binascii.unhexlify(p.data)
                try:
                    krb = ndr_unpack(drsblobs.package_PrimaryKerberosBlob, krb_blob)
                    assert krb.version == 4
                    old_krb['ctr4'] = krb.ctr
                    for k in krb.ctr.keys:
                        log.debug("calculate_supplementalCredentials: ctr4.key.keytype: %s", k.keytype)
                except Exception:  # FIXME: which exception?
                    log.exception("calculate_supplementalCredentials: ndr_unpack of S4 Primary:Kerberos-Newer-Keys blob failed.")
                    log.error("calculate_supplementalCredentials: Continuing anyway, Primary:Kerberos-Newer-Keys (AES and DES keys) blob will be missing in supplementalCredentials ctr4.old_keys.")

    krb5_aes256 = ''
    krb5_aes128 = ''
    krb5_des_md5 = ''
    krb5_des_crc = ''
    krb_ctr3_salt = ''
    krb_ctr4_salt = ''
    for k in ucs_krb5key:
        (keyblock, salt, _kvno) = heimdal.asn1_decode_key(k)
        key_data = keyblock.keyvalue()
        saltstring = salt.saltvalue()
        enctype = keyblock.keytype()
        enctype_id = enctype.toint()
        if enctype_id not in krb5_context.etype_ids:
            log.warning("calculate_supplementalCredentials: ignoring unsupported krb5_keytype: (%d)", enctype_id)
            continue

        log.trace("calculate_supplementalCredentials: krb5_keytype: %s (%d)", enctype, enctype_id)
        if enctype_id == 18:
            krb5_aes256 = key_data
            if not krb_ctr4_salt:
                krb_ctr4_salt = saltstring
        elif enctype_id == 17:
            krb5_aes128 = key_data
            if not krb_ctr4_salt:
                krb_ctr4_salt = saltstring
        elif enctype_id == 3:
            krb5_des_md5 = key_data
            if not krb_ctr3_salt:
                krb_ctr3_salt = saltstring
        elif enctype_id == 1:
            krb5_des_crc = key_data
            if not krb_ctr3_salt:
                krb_ctr3_salt = saltstring
        if not krb_ctr3_salt:
            krb_ctr3_salt = saltstring

    # build new drsblobs.supplementalCredentialsBlob

    sc_blob = None
    cred_List = []
    package_names = []

    # Primary:Kerberos-Newer-Keys : AES keys
    if krb5_aes256 or krb5_aes128:
        log.debug("calculate_supplementalCredentials: building Primary:Kerberos-Newer-Keys blob")
        kerberosKey4list = []
        if krb5_aes256:
            assert len(krb5_aes256) == 32
            next_key = drsblobs.package_PrimaryKerberosKey4()
            next_key.keytype = 18
            next_key.value = krb5_aes256
            next_key.value_len = len(krb5_aes256)
            kerberosKey4list.append(next_key)
        if krb5_aes128:
            assert len(krb5_aes128) == 16
            next_key = drsblobs.package_PrimaryKerberosKey4()
            next_key.keytype = 17
            next_key.value = krb5_aes128
            next_key.value_len = len(krb5_aes128)
            kerberosKey4list.append(next_key)
        if krb5_des_md5:
            assert len(krb5_des_md5) == 8
            next_key = drsblobs.package_PrimaryKerberosKey4()
            next_key.keytype = 3
            next_key.value = krb5_des_md5
            next_key.value_len = len(krb5_des_md5)
            kerberosKey4list.append(next_key)
        if not krb5_des_md5:
            next_key = drsblobs.package_PrimaryKerberosKey4()
            next_key.keytype = 4294967156
            next_key.value = nt_hash
            if nt_hash:
                next_key.value_len = len(nt_hash)
            else:
                next_key.value_len = 0
            kerberosKey4list.append(next_key)
        if krb5_des_crc:
            assert len(krb5_des_crc) == 8
            next_key = drsblobs.package_PrimaryKerberosKey4()
            next_key.keytype = 1
            next_key.value = krb5_des_crc
            next_key.value_len = len(krb5_des_crc)
            kerberosKey4list.append(next_key)
        # Windows Server 2012 does not always send the des encryption types.
        # Samba does not allow a key number != 4, which is why we add a "dummy" hash.
        if not krb5_des_crc:
            next_key = drsblobs.package_PrimaryKerberosKey4()
            next_key.keytype = 4294967156
            next_key.value = nt_hash
            if nt_hash:
                next_key.value_len = len(nt_hash)
            else:
                next_key.value_len = 0
            kerberosKey4list.append(next_key)

        salt4 = drsblobs.package_PrimaryKerberosString()
        salt4.string = krb_ctr4_salt

        ctr4 = drsblobs.package_PrimaryKerberosCtr4()
        ctr4.salt = salt4
        ctr4.num_keys = len(kerberosKey4list)
        ctr4.keys = kerberosKey4list

        if old_krb.get('ctr4'):
            # Backup old_keys to s4_old_keys
            s4_num_old_keys = old_krb['ctr4'].num_old_keys
            s4_old_keys = []
            for key in old_krb['ctr4'].old_keys:
                s4_old_keys.append(key)  # noqa: PERF402

            # keys -> old_keys
            if len(old_krb['ctr4'].keys) > ctr4.num_keys:
                cleaned_old_keys = []
                for key in old_krb['ctr4'].keys:
                    if key.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) to include the arc4 hash
                        log.debug("calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys filtering keytype %s from old_keys", key.keytype)
                        continue
                    else:  # TODO: can we do something better at this point to make old_keys == num_keys ?
                        cleaned_old_keys.append(key)

                ctr4.old_keys = cleaned_old_keys
                ctr4.num_old_keys = len(cleaned_old_keys)
            else:
                ctr4.old_keys = old_krb['ctr4'].keys
                ctr4.num_old_keys = old_krb['ctr4'].num_keys

            # s4_old_keys -> older_keys
            if ctr4.num_old_keys > ctr4.num_older_keys:
                cleaned_older_keys = []
                for key in s4_old_keys:
                    if key.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) to include the arc4 hash
                        log.debug("calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys filtering keytype %s from older_keys", key.keytype)
                        continue
                    else:  # TODO: can we do something better at this point to make old_keys == num_keys ?
                        cleaned_older_keys.append(key)

                ctr4.older_keys = cleaned_older_keys
                ctr4.num_older_keys = len(cleaned_older_keys)
            else:
                ctr4.older_keys = s4_old_keys
                ctr4.num_older_keys = s4_num_old_keys

        if ctr4.num_old_keys not in (0, ctr4.num_keys):
            # TODO: Recommended policy is to fill up old_keys to match num_keys, this will result in a traceback, can we do something better?
            log.warning("calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_keys = %s", ctr4.num_keys)
            for k in ctr4.keys:
                log.warning("calculate_supplementalCredentials: ctr4.key.keytype: %s", k.keytype)
            log.warning("calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_old_keys = %s", ctr4.num_old_keys)
            for k in ctr4.old_keys:
                log.warning("calculate_supplementalCredentials: ctr4.old_key.keytype: %s", k.keytype)

        if ctr4.num_older_keys not in (0, ctr4.num_old_keys):
            # TODO: Recommended policy is to fill up old_keys to match num_keys, this will result in a traceback, can we do something better?
            log.warning("calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_old_keys = %s", ctr4.num_old_keys)
            for k in ctr4.old_keys:
                log.warning("calculate_supplementalCredentials: ctr4.old_key.keytype: %s", k.keytype)
            log.warning("calculate_supplementalCredentials: Primary:Kerberos-Newer-Keys num_older_keys = %s", ctr4.num_older_keys)
            for k in ctr4.older_keys:
                log.warning("calculate_supplementalCredentials: ctr4.older_key.keytype: %s", k.keytype)

        krb_Primary_Kerberos_Newer = drsblobs.package_PrimaryKerberosBlob()
        krb_Primary_Kerberos_Newer.version = 4
        krb_Primary_Kerberos_Newer.ctr = ctr4

        krb_blob_Primary_Kerberos_Newer = ndr_pack(krb_Primary_Kerberos_Newer)
        creddata_Primary_Kerberos_Newer = binascii.hexlify(krb_blob_Primary_Kerberos_Newer)
        credname_Primary_Kerberos_Newer = "Primary:Kerberos-Newer-Keys"

        cred_Primary_Kerberos_Newer = drsblobs.supplementalCredentialsPackage()
        cred_Primary_Kerberos_Newer.name = credname_Primary_Kerberos_Newer
        cred_Primary_Kerberos_Newer.name_len = len(credname_Primary_Kerberos_Newer)
        cred_Primary_Kerberos_Newer.data = creddata_Primary_Kerberos_Newer
        cred_Primary_Kerberos_Newer.data_len = len(creddata_Primary_Kerberos_Newer)
        cred_Primary_Kerberos_Newer.reserved = 1
        cred_List.append(cred_Primary_Kerberos_Newer)
        package_names.append('Kerberos-Newer-Keys')
    # Primary:Kerberos : MD5 and CRC keys

    log.debug("calculate_supplementalCredentials: building Primary:Kerberos blob")
    kerberosKey3list = []

    if krb5_aes256 or krb5_aes128 or krb5_des_md5 or krb5_des_crc:
        if krb5_des_md5:
            next_key = drsblobs.package_PrimaryKerberosKey3()
            next_key.keytype = 3
            next_key.value = krb5_des_md5
            next_key.value_len = len(krb5_des_md5)
            kerberosKey3list.append(next_key)
        if not krb5_des_md5:
            next_key = drsblobs.package_PrimaryKerberosKey3()
            next_key.keytype = 4294967156
            next_key.value = nt_hash
            if nt_hash:
                next_key.value_len = len(nt_hash)
            else:
                next_key.value_len = 0
            kerberosKey3list.append(next_key)
        if krb5_des_crc:
            next_key = drsblobs.package_PrimaryKerberosKey3()
            next_key.keytype = 1
            next_key.value = krb5_des_crc
            next_key.value_len = len(krb5_des_crc)
            kerberosKey3list.append(next_key)
        # Windows Server 2012 does not always send the des encryption types.
        # Samba does not allow a key number != 2, which is why we add a "dummy" hash.
        if not krb5_des_crc:
            next_key = drsblobs.package_PrimaryKerberosKey3()
            next_key.keytype = 4294967156
            next_key.value = nt_hash
            if nt_hash:
                next_key.value_len = len(nt_hash)
            else:
                next_key.value_len = 0
            kerberosKey3list.append(next_key)

        salt = drsblobs.package_PrimaryKerberosString()
        salt.string = krb_ctr3_salt

        ctr3 = drsblobs.package_PrimaryKerberosCtr3()
        ctr3.salt = salt
        ctr3.num_keys = len(kerberosKey3list)
        ctr3.keys = kerberosKey3list

        if old_krb.get('ctr3'):
            # keys -> old_keys
            if len(old_krb['ctr3'].keys) > ctr3.num_keys:
                cleaned_ctr3_old_keys = []
                for key in old_krb['ctr3'].keys:
                    if key.keytype == 4294967156:  # in all known cases W2k8 AD uses keytype 4294967156 (=-140L) to include the arc4 hash
                        log.debug("calculate_supplementalCredentials: Primary:Kerberos filtering keytype %s from old_keys", key.keytype)
                        continue
                    else:  # TODO: can we do something better at this point to make old_keys == num_keys ?
                        cleaned_ctr3_old_keys.append(key)

                ctr3.old_keys = cleaned_ctr3_old_keys
                ctr3.num_old_keys = len(cleaned_ctr3_old_keys)
            else:
                ctr3.old_keys = old_krb['ctr3'].keys
                ctr3.num_old_keys = old_krb['ctr3'].num_keys

        if ctr3.num_old_keys not in (0, ctr3.num_keys):
            # TODO: Recommended policy is to fill up old_keys to match num_keys, this will result in a traceback, can we do something better?
            log.warning("calculate_supplementalCredentials: Primary:Kerberos num_keys = %s", ctr3.num_keys)
            for k in ctr3.keys:
                log.warning("calculate_supplementalCredentials: ctr3.key.keytype: %s", k.keytype)
            log.warning("calculate_supplementalCredentials: Primary:Kerberos num_old_keys = %s", ctr3.num_old_keys)
            for k in ctr3.old_keys:
                log.warning("calculate_supplementalCredentials: ctr3.old_key.keytype: %s", k.keytype)

        krb = drsblobs.package_PrimaryKerberosBlob()
        krb.version = 3
        krb.ctr = ctr3
        krb3_blob = ndr_pack(krb)

        creddata_Primary_Kerberos = binascii.hexlify(krb3_blob)
        credname_Primary_Kerberos = "Primary:Kerberos"

        cred_Primary_Kerberos = drsblobs.supplementalCredentialsPackage()
        cred_Primary_Kerberos.name = credname_Primary_Kerberos
        cred_Primary_Kerberos.name_len = len(credname_Primary_Kerberos)
        cred_Primary_Kerberos.data = creddata_Primary_Kerberos
        cred_Primary_Kerberos.data_len = len(creddata_Primary_Kerberos)
        cred_Primary_Kerberos.reserved = 1
        cred_List.append(cred_Primary_Kerberos)
        package_names.append('Kerberos')

    if package_names:
        krb_blob_Packages = '\0'.join(package_names).encode('utf-16le')
        cred_PackagesBlob_data = binascii.hexlify(krb_blob_Packages).upper()
        cred_PackagesBlob_name = "Packages"
        cred_PackagesBlob = drsblobs.supplementalCredentialsPackage()
        cred_PackagesBlob.name = cred_PackagesBlob_name
        cred_PackagesBlob.name_len = len(cred_PackagesBlob_name)
        cred_PackagesBlob.data = cred_PackagesBlob_data
        cred_PackagesBlob.data_len = len(cred_PackagesBlob_data)
        cred_PackagesBlob.reserved = 2
        cred_List.insert(-1, cred_PackagesBlob)

        sub = drsblobs.supplementalCredentialsSubBlob()
        sub.num_packages = len(cred_List)
        sub.packages = cred_List
        sub.signature = drsblobs.SUPPLEMENTAL_CREDENTIALS_SIGNATURE
        sub.prefix = drsblobs.SUPPLEMENTAL_CREDENTIALS_PREFIX

        sc = drsblobs.supplementalCredentialsBlob()
        sc.sub = sub
        sc_blob = ndr_pack(sc)
        log.trace("calculate_supplementalCredentials: sc: %s", ndr_print(sc))

    return sc_blob


def extract_NThash_from_krb5key(ucs_krb5key):

    NThash = None

    for k in ucs_krb5key:
        (keyblock, _salt, _kvno) = heimdal.asn1_decode_key(k)

        enctype = keyblock.keytype()
        enctype_id = enctype.toint()
        if enctype_id == 23:
            krb5_arcfour_hmac_md5 = keyblock.keyvalue()
            NThash = binascii.b2a_hex(krb5_arcfour_hmac_md5)
            break

    return NThash


def password_sync_ucs_to_s4(s4connector, key, object):
    log.debug("password_sync_ucs_to_s4 called")

    modify = False
    old_ucs_object = object.get('old_ucs_object', {})
    new_ucs_object = object.get('new_ucs_object', {})
    if old_ucs_object or new_ucs_object:
        for attr in ['sambaLMPassword', 'sambaNTPassword', 'sambaPwdLastSet', 'sambaPwdMustChange', 'krb5PrincipalName', 'krb5Key', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService']:
            old_values = set(old_ucs_object.get(attr, []))
            new_values = set(new_ucs_object.get(attr, []))
            if old_values != new_values:
                modify = True
                break
    else:
        # add mode
        modify = True

    if not modify:
        log.debug('password_sync_ucs_to_s4: the password for %s has not been changed. Skipping password sync.', object['dn'])
        return

    log.debug("Object DN=%r", object['dn'])

    ucs_object = s4connector._object_mapping(key, object, 'con')

    log.debug("   UCS DN = %r", ucs_object['dn'])

    try:
        ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaLMPassword', 'sambaNTPassword', 'sambaPwdLastSet', 'sambaPwdMustChange', 'krb5PrincipalName', 'krb5Key', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService'], required=True)
    except ldap.NO_SUCH_OBJECT:
        log.process("password_sync_ucs_to_s4: The UCS object (%s) was not found. The object was removed.", ucs_object['dn'])
        return

    services = ucs_object_attributes.get('univentionService', [])
    if b'Samba 4' in services:
        log.debug("password_sync_ucs_to_s4: %s is a S4 server, skip password sync", ucs_object['dn'])
        return

    sambaPwdLastSet = None
    if 'sambaPwdLastSet' in ucs_object_attributes:
        sambaPwdLastSet = int(ucs_object_attributes['sambaPwdLastSet'][0])
    log.debug("password_sync_ucs_to_s4: sambaPwdLastSet: %s", sambaPwdLastSet)

    if 'sambaPwdMustChange' in ucs_object_attributes:
        sambaPwdMustChange = int(ucs_object_attributes['sambaPwdMustChange'][0])
        log.warning("password_sync_ucs_to_s4: Ignoring sambaPwdMustChange: %s", sambaPwdMustChange)

    ucsLMhash = ucs_object_attributes.get('sambaLMPassword', [None])[0]
    ucsNThash = ucs_object_attributes.get('sambaNTPassword', [None])[0]
    krb5Principal = ucs_object_attributes.get('krb5PrincipalName', [None])[0]
    krb5Key = ucs_object_attributes.get('krb5Key', [])

    if not ucsNThash:
        log.debug("password_sync_ucs_to_s4: sambaNTPassword missing in UCS LDAP, trying krb5Key")
        ucsNThash = extract_NThash_from_krb5key(krb5Key)

    if not ucsNThash:
        log.warning("password_sync_ucs_to_s4: Failed to get NT Password-Hash from UCS LDAP")

    # log.debug("password_sync_ucs_to_s4: Password-Hash from UCS: %s" % ucsNThash)

    s4_object_attributes = s4connector.lo_s4.get(object['dn'], ['pwdLastSet', 'objectSid'])
    pwdLastSet = None
    if 'pwdLastSet' in s4_object_attributes:
        pwdLastSet = int(s4_object_attributes['pwdLastSet'][0])
    objectSid = univention.s4connector.s4.decode_sid(s4_object_attributes['objectSid'][0])
    log.debug("password_sync_ucs_to_s4: pwdLastSet from S4 : %s", pwdLastSet)

    pwd_set = False
    filter_expr = format_escaped('(objectSid={0!e})', objectSid)
    res = s4connector.lo_s4.search(filter=filter_expr, attr=['unicodePwd', 'userPrincipalName', 'supplementalCredentials', 'msDS-KeyVersionNumber', 'dBCSPwd', 'ntPwdHistory', 'msDS-ResultantPSO'])
    s4_search_attributes = res[0][1]

    unicodePwd_attr = s4_search_attributes.get('unicodePwd', [None])[0]
    dBCSPwd_attr = s4_search_attributes.get('dBCSPwd', [None])[0]
    userPrincipalName_attr = s4_search_attributes.get('userPrincipalName', [None])[0]
    supplementalCredentials = s4_search_attributes.get('supplementalCredentials', [None])[0]
    ntPwdHistory = s4_search_attributes.get('ntPwdHistory', [b''])[0]
    msDSResultantPSO = s4_search_attributes.get('msDS-ResultantPSO', [None])[0]

    # get pwdhistorylength
    pwdHistoryLength = 0
    if msDSResultantPSO:
        res = s4connector.lo_s4.get(msDSResultantPSO.decode('UTF-8'), attr=['msDS-PasswordHistoryLength'])
        pwdHistoryLength = int(res.get('msDS-PasswordHistoryLength', [0])[0])
    else:
        res = s4connector.lo_s4.search(filter='(objectClass=domain)', attr=['pwdHistoryLength'])
        pwdHistoryLength = int(res[0][1].get('pwdHistoryLength', [0])[0])
    s4NThash = None
    if unicodePwd_attr:
        s4NThash = binascii.b2a_hex(unicodePwd_attr).upper()
    else:
        log.warning("password_sync_ucs_to_s4: Failed to get NT Password-Hash from S4")

    s4LMhash = None
    if dBCSPwd_attr:
        s4LMhash = binascii.b2a_hex(dBCSPwd_attr).upper()
    else:
        log.info("password_sync_ucs_to_s4: Failed to get LM Password-Hash from S4")

    modlist = []
    if krb5Principal != userPrincipalName_attr:
        if krb5Principal:
            if not userPrincipalName_attr:  # new and not old
                modlist.append((ldap.MOD_ADD, 'userPrincipalName', krb5Principal))
            else:  # new and old differ
                if krb5Principal.lower() != userPrincipalName_attr.lower():
                    log.warning("password_sync_ucs_to_s4: userPrincipalName != krb5Principal: %r != %r", userPrincipalName_attr, krb5Principal)
                modlist.append((ldap.MOD_REPLACE, 'userPrincipalName', krb5Principal))
        else:
            if userPrincipalName_attr:  # old and not new
                modlist.append((ldap.MOD_DELETE, 'userPrincipalName', userPrincipalName_attr))
    unicodePwd_new = None
    if ucsNThash != s4NThash:
        log.debug("password_sync_ucs_to_s4: NT Hash S4: %r NT Hash UCS: %r", s4NThash, ucsNThash)
        # Now if ucsNThash is empty there should at least some timestamp in UCS,
        # otherwise it's probably not a good idea to remove the unicodePwd.
        # Usecase: LDB module on ucs_3.0-0-ucsschool slaves creates XP computers/windows in UDM without password
        if ucsNThash or sambaPwdLastSet:
            pwd_set = True
            if ucsNThash:
                try:
                    unicodePwd_new = binascii.a2b_hex(ucsNThash)
                except TypeError:
                    if ucsNThash.startswith(b"NO PASSWORD"):
                        pwd_set = False
                    else:
                        raise
            if pwd_set and unicodePwd_new:
                if pwdHistoryLength:
                    userobject = s4connector.get_ucs_object(key, ucs_object['dn'])
                    pwhistoryPolicy = userobject.loadPolicyObject('policies/pwhistory')
                    pwhistory_length = pwhistoryPolicy['length']
                    pwhistory_length = int(pwhistory_length) if pwhistory_length else 0
                    if pwhistory_length != pwdHistoryLength:
                        log.warning("password_sync_ucs_to_s4: Mismatch between UCS pwhistoryPolicy (%s) and S4 pwhistoryPolicy (%s). Using the larger one.", pwhistory_length, pwdHistoryLength)
                    des_len = max(pwdHistoryLength, pwhistory_length) * 16
                    ntPwdHistory_new = unicodePwd_new + ntPwdHistory
                    ntPwdHistory_new = ntPwdHistory_new[:des_len]
                    log.debug("password_sync_ucs_to_s4: Update ntPwdHistory.")
                    modlist.append((ldap.MOD_REPLACE, 'ntPwdHistory', ntPwdHistory_new))
                else:
                    log.debug("password_sync_ucs_to_s4: PwdHistoryLength is 0, do not update history.")
                modlist.append((ldap.MOD_REPLACE, 'unicodePwd', unicodePwd_new))
    if ucsLMhash != s4LMhash:
        log.debug("password_sync_ucs_to_s4: LM Hash S4: %r LM Hash UCS: %r", s4LMhash, ucsLMhash)
        pwd_set = True
        if ucsLMhash:
            dBCSPwd_new = binascii.a2b_hex(ucsLMhash)
            modlist.append((ldap.MOD_REPLACE, 'dBCSPwd', dBCSPwd_new))
        else:
            modlist.append((ldap.MOD_DELETE, 'dBCSPwd', None))

    if pwd_set or not supplementalCredentials:
        if krb5Principal:
            # encoding of Samba4 supplementalCredentials
            if krb5Key:
                supplementalCredentials_new = calculate_supplementalCredentials(krb5Key, supplementalCredentials, unicodePwd_new)
                if supplementalCredentials_new:
                    modlist.append((ldap.MOD_REPLACE, 'supplementalCredentials', supplementalCredentials_new))
                else:
                    log.debug("password_sync_ucs_to_s4: no supplementalCredentials_new")
                # if supplementalCredentials:
                #    modlist.append((ldap.MOD_REPLACE, 'msDS-KeyVersionNumber', krb5KeyVersionNumber))
                # else:
                #    modlist.append((ldap.MOD_ADD, 'msDS-KeyVersionNumber', krb5KeyVersionNumber))

        if sambaPwdLastSet is None:
            sambaPwdLastSet = int(time.time())
            newpwdlastset = str(univention.s4connector.s4.samba2s4_time(sambaPwdLastSet))
        elif sambaPwdLastSet in [0, 1]:
            log.debug("password_sync_ucs_to_s4: samba pwd expired, set newpwdLastSet to 0")
            newpwdlastset = 0
        else:
            newpwdlastset = univention.s4connector.s4.samba2s4_time(sambaPwdLastSet)
        log.debug("password_sync_ucs_to_s4: pwdLastSet in modlist: %r", newpwdlastset)
        modlist.append((ldap.MOD_REPLACE, 'pwdLastSet', str(newpwdlastset).encode('ASCII')))
        modlist.append((ldap.MOD_REPLACE, 'badPwdCount', b'0'))
        modlist.append((ldap.MOD_REPLACE, 'badPasswordTime', b'0'))
        modlist.append((ldap.MOD_REPLACE, 'lockoutTime', b'0'))

    else:
        log.debug("password_sync_ucs_to_s4: No password change to sync to S4 ")

        # check pwdLastSet
        if sambaPwdLastSet is not None:
            if sambaPwdLastSet in [0, 1]:
                newpwdlastset = 0
            else:
                newpwdlastset = univention.s4connector.s4.samba2s4_time(sambaPwdLastSet)
            log.debug("password_sync_ucs_to_s4: sambaPwdLastSet: %d", sambaPwdLastSet)
            log.debug("password_sync_ucs_to_s4: newpwdlastset  : %r", newpwdlastset)
            log.debug("password_sync_ucs_to_s4: pwdLastSet (AD): %r", pwdLastSet)
            if newpwdlastset != pwdLastSet and abs(newpwdlastset - pwdLastSet) >= 10000000:
                modlist.append((ldap.MOD_REPLACE, 'pwdLastSet', str(newpwdlastset).encode('ASCII')))

    ctrl_bypass_password_hash = LDAPControl('1.3.6.1.4.1.7165.4.3.12', criticality=0)
    log.trace("password_sync_ucs_to_s4: modlist: %r", modlist)
    if modlist:
        s4connector.lo_s4.lo.modify_ext_s(object['dn'], modlist, serverctrls=[ctrl_bypass_password_hash])


def password_sync_s4_to_ucs(s4connector, key, ucs_object, modifyUserPassword=True):
    log.debug("password_sync_s4_to_ucs called")

    if ucs_object['modtype'] == 'modify' and 'pwdLastSet' not in ucs_object.get('changed_attributes', []):
        log.debug('password_sync_s4_to_ucs: the password for %s has not been changed. Skipping password sync.', ucs_object['dn'])
        return

    object = s4connector._object_mapping(key, ucs_object, 'ucs')
    s4_object_attributes = s4connector.lo_s4.get(object['dn'], ['objectSid', 'pwdLastSet'])

    if s4connector.isInCreationList(object['dn']):
        s4connector.removeFromCreationList(object['dn'])
        log.debug("password_sync_s4_to_ucs: Synchronisation of password has been canceled. Object was just created.")
        return

    pwdLastSet = None
    if 'pwdLastSet' in s4_object_attributes:
        pwdLastSet = int(s4_object_attributes['pwdLastSet'][0])
    log.debug("password_sync_s4_to_ucs: pwdLastSet from S4: %s (%s)", pwdLastSet, s4_object_attributes)
    objectSid = univention.s4connector.s4.decode_sid(s4_object_attributes['objectSid'][0])

    filter_expr = format_escaped('(objectSid={0!e})', objectSid)
    res = s4connector.lo_s4.search(filter=filter_expr, attr=['unicodePwd', 'supplementalCredentials', 'msDS-KeyVersionNumber', 'dBCSPwd', 'msDS-ResultantPSO', 'ntPwdHistory'])
    s4_search_attributes = res[0][1]

    unicodePwd_attr = s4_search_attributes.get('unicodePwd', [None])[0]
    if unicodePwd_attr:
        ntPwd = binascii.b2a_hex(unicodePwd_attr).upper()

        lmPwd = b''
        dBCSPwd = s4_search_attributes.get('dBCSPwd', [None])[0]
        if dBCSPwd:
            lmPwd = binascii.b2a_hex(dBCSPwd).upper()

        supplementalCredentials = s4_search_attributes.get('supplementalCredentials', [None])[0]
        msDS_KeyVersionNumber = s4_search_attributes.get('msDS-KeyVersionNumber', [0])[0]

        ntPwd_ucs = b''
        lmPwd_ucs = b''
        krb5Principal = b''
        # userPassword = b''
        modlist = []
        ucs_object_attributes = s4connector.lo.get(ucs_object['dn'], ['sambaPwdMustChange', 'sambaPwdLastSet', 'sambaNTPassword', 'sambaLMPassword', 'krb5PrincipalName', 'krb5Key', 'krb5KeyVersionNumber', 'userPassword', 'shadowLastChange', 'shadowMax', 'krb5PasswordEnd', 'univentionService', 'pwhistory'])

        pwhistory_ucs = ucs_object_attributes.get('pwhistory', [b''])[0]

        services = ucs_object_attributes.get('univentionService', [])
        if 'S4 SlavePDC' in services:
            log.debug("password_sync_s4_to_ucs: %s is a S4 SlavePDC server, skip password sync", ucs_object['dn'])
            return

        if 'sambaNTPassword' in ucs_object_attributes:
            ntPwd_ucs = ucs_object_attributes['sambaNTPassword'][0]
        if 'sambaLMPassword' in ucs_object_attributes:
            lmPwd_ucs = ucs_object_attributes['sambaLMPassword'][0]
        if 'krb5PrincipalName' in ucs_object_attributes:
            krb5Principal = ucs_object_attributes['krb5PrincipalName'][0]
        # if 'userPassword' in ucs_object_attributes:
        #    userPassword = ucs_object_attributes['userPassword'][0]
        sambaPwdLastSet = None
        if 'sambaPwdLastSet' in ucs_object_attributes:
            sambaPwdLastSet = ucs_object_attributes['sambaPwdLastSet'][0]
        log.debug("password_sync_s4_to_ucs: sambaPwdLastSet: %r", sambaPwdLastSet)
        sambaPwdMustChange = ''
        if 'sambaPwdMustChange' in ucs_object_attributes:
            sambaPwdMustChange = ucs_object_attributes['sambaPwdMustChange'][0]
            log.debug("password_sync_s4_to_ucs: Found sambaPwdMustChange: %r", sambaPwdMustChange)
        krb5Key_ucs = ucs_object_attributes.get('krb5Key', [])
        userPassword_ucs = ucs_object_attributes.get('userPassword', [None])[0]
        krb5KeyVersionNumber = ucs_object_attributes.get('krb5KeyVersionNumber', [None])[0]

        pwd_changed = False
        if ntPwd != ntPwd_ucs:
            pwd_changed = True
            modlist.append(('sambaNTPassword', ntPwd_ucs, ntPwd))

        if lmPwd != lmPwd_ucs:
            pwd_changed = True
            modlist.append(('sambaLMPassword', lmPwd_ucs, lmPwd))

        if pwd_changed:
            if krb5Principal:
                # decoding of Samba4 supplementalCredentials
                krb5Key_new = calculate_krb5key(unicodePwd_attr, supplementalCredentials, int(msDS_KeyVersionNumber))

                modlist.append(('krb5Key', krb5Key_ucs, krb5Key_new))
                if int(msDS_KeyVersionNumber) != int(krb5KeyVersionNumber):
                    modlist.append(('krb5KeyVersionNumber', krb5KeyVersionNumber, msDS_KeyVersionNumber))

            # Append modification as well to modlist, to apply in one transaction
            if modifyUserPassword:
                userobject = s4connector.get_ucs_object(key, ucs_object['dn'])
                pwhistoryPolicy = None
                if userobject:
                    pwhistoryPolicy = userobject.loadPolicyObject('policies/pwhistory')
                    pwhistory_length = pwhistoryPolicy['length']
                    pwhistory_length = int(pwhistory_length) if pwhistory_length else 0
                    if pwhistory_length > 0:
                        msDSResultantPSO = s4_search_attributes.get('msDS-ResultantPSO', [None])[0]

                        # get pwdhistorylength from s4 object
                        s4_pwhistory_length = 0
                        if msDSResultantPSO:
                            res = s4connector.lo_s4.get(msDSResultantPSO.decode(), attr=['msDS-PasswordHistoryLength'])
                            s4_pwhistory_length = int(res.get('msDS-PasswordHistoryLength', [0])[0])
                        else:
                            res = s4connector.lo_s4.search(filter='(objectClass=domain)', attr=['pwdHistoryLength'])
                            s4_pwhistory_length = int(res[0][1].get('pwdHistoryLength', [0])[0])

                        if pwhistory_length != s4_pwhistory_length:
                            log.warning("password_sync_s4_to_ucs: Mismatch between UCS pwhistoryPolicy (%s) and S4 pwhistoryPolicy (%s). Using the larger one.", pwhistory_length, s4_pwhistory_length)
                        pwhistory_length = max(pwhistory_length, s4_pwhistory_length)

                        ntPwdHistory = s4_search_attributes.get('ntPwdHistory', [b''])[0]
                        ntPwdHistory_hex = binascii.hexlify(ntPwdHistory).upper()
                        ntPwdHistory_len = len(ntPwdHistory_hex) // 32

                        pwhistory_list = pwhistory_ucs.decode('ASCII').strip().split(' ')
                        pwhistory_len = len(pwhistory_list)
                        pwhistory_new = None

                        if ntPwdHistory_len and pwhistory_len == 1 and object.get('old_s4_object', {}).get('pwdLastSet', [None])[0] is None:
                            # In the first synchronization from S4->UCS the password history from the S4 User
                            # can have more than one entry.
                            pwhistory_new = b''
                            hist = [ntPwdHistory_hex[i: i + 32] for i in range(0, len(ntPwdHistory_hex), 32)]
                            for nt_hash in reversed(hist):
                                pwhistory_new = univention.admin.password.get_password_history('{NT}$' + nt_hash.decode('ASCII'), pwhistory_new.decode('ASCII'), pwhistory_length).encode('ASCII')
                        else:
                            pwhistory_new = univention.admin.password.get_password_history('{NT}$' + ntPwd.decode('ASCII'), pwhistory_ucs.decode('ASCII'), pwhistory_length).encode('ASCII')

                        modlist.append(('pwhistory', pwhistory_ucs, pwhistory_new))

                modlist.append(('userPassword', userPassword_ucs, b'{K5KEY}'))
        else:
            log.debug("password_sync_s4_to_ucs: No password change to sync to UCS")

        try:
            old_pwdLastSet = object['old_s4_object']['pwdLastSet'][0]
        except (KeyError, IndexError):
            old_pwdLastSet = None

        if pwdLastSet != old_pwdLastSet:
            log.trace("password_sync_s4_to_ucs: updating shadowLastChange")
            old_shadowLastChange = ucs_object_attributes.get('shadowLastChange', [None])[0]
            new_shadowLastChange = old_shadowLastChange

            # shadowMax (set to value of (univentionPWExpiryInterval - 1), otherwise delete)
            # krb5PasswordEnd (set to today + univentionPWExpiryInterval, otherwise delete)
            old_shadowMax = ucs_object_attributes.get('shadowMax', [None])[0]
            new_shadowMax = old_shadowMax
            old_krb5end = ucs_object_attributes.get('krb5PasswordEnd', [None])[0]
            new_krb5end = old_krb5end

            pwdLastSet_unix = univention.s4connector.s4.s42samba_time(pwdLastSet)
            newSambaPwdLastSet = str(pwdLastSet_unix).encode('ASCII')

            if pwdLastSet == 0:  # pwd change on next login
                new_shadowMax = b'0'
                expiry = int(time.time())
                new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime(expiry)).encode('ASCII')
                # we need to expire the password. Since shadowMax=0 is its minimum value, we need to set shadowLastChange = today-2days ## FIXME: -1day should be enough
                two_days_ago = int(time.time()) - 86400 * 2
                new_shadowLastChange = str(two_days_ago // 3600 // 24).encode('ASCII')
            else:                # not pwd change on next login
                new_shadowLastChange = str(pwdLastSet_unix // 3600 // 24).encode('ASCII')
                userobject = s4connector.get_ucs_object(key, ucs_object['dn'])
                if not userobject:
                    log.error("password_sync_s4_to_ucs: couldn't get user-object from UCS")
                    return False

                pwhistoryPolicy = userobject.loadPolicyObject('policies/pwhistory')
                try:
                    expiryInterval = int(pwhistoryPolicy['expiryInterval'])
                except (TypeError, ValueError):
                    # expiryInterval is empty or no legal int-string
                    pwhistoryPolicy['expiryInterval'] = ''
                    expiryInterval = -1

                log.debug("password_sync_s4_to_ucs: password expiryInterval for %s is %s", ucs_object['dn'], expiryInterval)
                if expiryInterval in (-1, 0):
                    new_shadowMax = b''
                    new_krb5end = b''
                else:
                    new_shadowMax = str(expiryInterval - 1).encode('ASCII')
                    new_krb5end = time.strftime("%Y%m%d000000Z", time.gmtime(pwdLastSet_unix + (int(expiryInterval) * 3600 * 24))).encode('ASCII')

            if new_shadowLastChange != old_shadowLastChange:
                log.debug("password_sync_s4_to_ucs: update shadowLastChange to %s for %s", new_shadowLastChange, ucs_object['dn'])
                modlist.append(('shadowLastChange', old_shadowLastChange, new_shadowLastChange))
            if new_shadowMax != old_shadowMax:
                log.debug("password_sync_s4_to_ucs: update shadowMax to %s for %s", new_shadowMax, ucs_object['dn'])
                modlist.append(('shadowMax', old_shadowMax, new_shadowMax))
            if new_krb5end != old_krb5end:
                log.debug("password_sync_s4_to_ucs: update krb5PasswordEnd to %s for %s", new_krb5end, ucs_object['dn'])
                modlist.append(('krb5PasswordEnd', old_krb5end, new_krb5end))

            if sambaPwdLastSet:
                if sambaPwdLastSet != newSambaPwdLastSet:
                    modlist.append(('sambaPwdLastSet', sambaPwdLastSet, newSambaPwdLastSet))
                    log.debug("password_sync_s4_to_ucs: sambaPwdLastSet in modlist (replace): %s", newSambaPwdLastSet)
            else:
                modlist.append(('sambaPwdLastSet', b'', newSambaPwdLastSet))
                log.debug("password_sync_s4_to_ucs: sambaPwdLastSet in modlist (set): %s", newSambaPwdLastSet)

            if sambaPwdMustChange:
                modlist.append(('sambaPwdMustChange', sambaPwdMustChange, b''))
                log.debug("password_sync_s4_to_ucs: Removing sambaPwdMustChange")

        if len(modlist) > 0:
            log.debug("password_sync_s4_to_ucs: modlist: %s", modlist)
            s4connector.lo.lo.modify(ucs_object['dn'], modlist)

    else:
        log.warning("password_sync_ucs_s4_to_ucs: Failed to get Password-Hash from S4")


def password_sync_s4_to_ucs_no_userpassword(s4connector, key, ucs_object):
    # The userPassword should not synchronized for computer accounts
    password_sync_s4_to_ucs(s4connector, key, ucs_object, modifyUserPassword=False)


def lockout_sync_to_ucs(connector, key, obj):
    """
    Sync account locking *state* from Samba/AD to UCS:
        sync AD (lockoutTime != 0)      ->  UCS locked = 1 and lockedTime = lockoutTime
                (lockoutTime == 0)      ->  UCS locked = 0 and lockedTime = 0 (lockedTime would be set automaticly by UCS)
    """
    if obj['modtype'] not in ('modify', 'add'):
        return

    if 'lockoutTime' not in obj['changed_attributes']:
        log.trace(
            'No lockout attribute in changed attributes.',
            changed_attributes=obj['changed_attributes'],
            dn=obj['dn'],
        )
        return

    try:
        ucs_admin_object = univention.admin.objects.get(
            connector.modules[key],
            co=None,
            lo=connector.lo,
            position='',
            dn=obj['dn'],
        )
    except uexceptions.noObject:
        log.warning('Object with DN %s not found!', obj['dn'])
        return

    ucs_admin_object.open()

    is_locked = ucs_admin_object['locked'] == '1'
    lockout_time = obj['attributes'].get('lockoutTime', [b'0'])[0]

    # Convert AD lockoutTime (Windows Filetime) to UCS lockedTime (GeneralizedTime)
    lockout_time_unix_ts = int(lockout_time.decode('ascii')) / 10000000 - 11644473600
    locked_time = datetime.fromtimestamp(lockout_time_unix_ts).strftime('%Y%m%d%H%M%SZ')

    should_be_locked = lockout_time != b'0'
    log.debug(
        'Locking user account',
        locked_time=locked_time,
        lockout_time=lockout_time,
        is_locked=is_locked,
        should_be_locked=should_be_locked,
        dn=obj['dn'],
    )

    if should_be_locked == is_locked:
        return

    old_states = (
        ucs_admin_object.descriptions['locked'].editable,
        ucs_admin_object.descriptions['locked'].may_change,
        ucs_admin_object.descriptions['lockedTime'].editable,
        ucs_admin_object.descriptions['lockedTime'].may_change,
    )
    (
        ucs_admin_object.descriptions['locked'].editable,
        ucs_admin_object.descriptions['locked'].may_change,
        ucs_admin_object.descriptions['lockedTime'].editable,
        ucs_admin_object.descriptions['lockedTime'].may_change,
    ) = (True, True, True, True)

    try:
        if should_be_locked:
            log.process('Lock user in UCS.', dn=obj['dn'])
            ucs_admin_object['locked'] = '1'
            ucs_admin_object['lockedTime'] = locked_time
        else:
            log.process('Unlock user in UCS.', dn=obj['dn'])
            ucs_admin_object['locked'] = '0'

        ucs_admin_object.modify()
    finally:
        (
            ucs_admin_object.descriptions['locked'].editable,
            ucs_admin_object.descriptions['locked'].may_change,
            ucs_admin_object.descriptions['lockedTime'].editable,
            ucs_admin_object.descriptions['lockedTime'].may_change,
        ) = old_states


def lockout_sync_from_ucs(connector, key, obj):
    """
    Sync unlock *modification* from OpenLDAP to AD:
        sync OpenLDAP ("L" not in sambaAcctFlags) ->  AD lockoutTime = 0

        sync OpenLDAP ("L" in sambaAcctFlags) ->  AD lockoutTime = sambaBadPasswordTime
        and  OpenLDAP sambaBadPasswordTime    ->  AD badPasswordTime
    """
    if obj['modtype'] not in ('modify', 'add'):
        return

    if obj.get('new_ucs_object') and obj.get('old_ucs_object'):
        is_locked = b'L' in obj['new_ucs_object'].get('sambaAcctFlags', [b''])[0]
        was_locked = b'L' in obj['old_ucs_object'].get('sambaAcctFlags', [b''])[0]
        if is_locked == was_locked:
            return

    ucs_object = connector._object_mapping(key, obj, 'con')

    try:
        ucs_object_attributes = connector.lo.get(ucs_object['dn'], ['sambaAcctFlags', 'sambaBadPasswordTime'], required=True)
    except ldap.NO_SUCH_OBJECT:
        log.warning('The UCS object (%s) was not found. The object was removed.', ucs_object['dn'])
        return

    try:
        ad_object_attributes = connector.lo_s4.get(obj['dn'], ['lockoutTime'], required=True)
    except ldap.NO_SUCH_OBJECT:
        log.warning('The AD object (%s) was not found. The object was removed.', obj['dn'])
        return

    samba_acct_flags = ucs_object_attributes.get('sambaAcctFlags', [b''])[0]
    is_locked = b'L' in samba_acct_flags

    samba_bad_password_time = ucs_object_attributes.get('sambaBadPasswordTime', [b'0'])[0]
    lockout_time = ad_object_attributes.get('lockoutTime', [b'0'])[0]
    should_be_locked = lockout_time != b'0'

    log.debug(
        'Lockout states.',
        samba_acct_flags=samba_acct_flags,
        samba_bad_password_time=samba_bad_password_time,
        lockout_time=lockout_time,
        is_locked=is_locked,
        should_be_locked=should_be_locked,
        ucs_object_dn=ucs_object['dn'],
        ad_object_dn=obj['dn'],
    )

    if should_be_locked == is_locked:
        return

    modlist = []
    if not is_locked:
        if samba_bad_password_time and samba_bad_password_time != b'0':
            log.error('The UCS object (%s) is unlocked, but sambaBadPasswordTime is set.', ucs_object['dn'])
            return

        # Ok here we have:
        # 1. Account currently not locked in OpenLDAP but in AD
        # 2. Lockout state has changed to unlocked at some pickled point in the past
        modlist.append((ldap.MOD_REPLACE, 'lockoutTime', b'0'))
        modlist.append((ldap.MOD_REPLACE, 'badPasswordTime', b'0'))
        log.process('Unlock user in AD.', dn=obj['dn'])
    else:
        if not samba_bad_password_time:
            log.error('The UCS object (%s) is locked, but sambaBadPasswordTime is missing.', ucs_object['dn'])
            return
        if samba_bad_password_time == b'0':
            log.error('The UCS object (%s) is locked, but sambaBadPasswordTime is 0.', ucs_object['dn'])
            return
        if samba_bad_password_time == lockout_time:
            # already locked
            return

        # Ok here we have:
        # 1. Account currently locked in OpenLDAP but not in AD
        # 2. Lockout state has changed to locked at some pickled point in the past
        modlist.append((ldap.MOD_REPLACE, 'lockoutTime', samba_bad_password_time))
        modlist.append((ldap.MOD_REPLACE, 'badPasswordTime', samba_bad_password_time))
        log.process('Lock user in AD.', dn=obj['dn'])
        log.debug('Setting lockoutTime to the value of sambaBadPasswordTime: %s', samba_bad_password_time)

    if modlist:
        log.trace('modlist: %s', modlist)
        connector.lo_s4.lo.modify_ext_s(obj['dn'], modlist)
