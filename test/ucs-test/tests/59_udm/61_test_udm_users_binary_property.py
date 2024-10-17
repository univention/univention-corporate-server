#!/usr/share/ucs-test/runner pytest-3
## desc: Test UDM API for users/user module
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api]
## packages: [python3-univention-directory-manager]
## bugs: [47316]

import base64
import os
from collections import namedtuple
from unittest import TestCase, main

import univention.debug as ud
import univention.logging
from univention.admin.syntax import jpegPhoto
from univention.testing.strings import random_string, random_username
from univention.udm import UDM


univention.logging.basicConfig(filename='/var/log/univention/directory-manager-cmd.log', univention_debug_level=ud.ALL)

CWD = os.path.dirname(os.path.abspath(__file__))

PostalAddress = namedtuple('PostalAddress', ['street', 'zipcode', 'city'])


class TestUdmUsersBasic(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.udm = UDM.admin().version(1)
        cls.udm._module_object_cache.clear()

    def test_create_user_with_photo(self):
        user_mod = self.udm.get('users/user')
        obj = user_mod.new()
        username = random_username()
        obj.props.lastname = username
        obj.props.username = obj.props.lastname
        obj.props.password = random_string()

        jpg_content = open(f'{CWD}/example_user_jpeg_photo.jpg', 'rb').read()
        obj.props.jpegPhoto = jpg_content
        obj.save()

        encoded_jpg_photo = base64.b64decode(jpegPhoto.parse(base64.b64encode(jpg_content).decode('ascii')))
        try:
            obj = user_mod.get(obj.dn)
            assert obj.props.jpegPhoto.raw == encoded_jpg_photo
            assert obj.props.jpegPhoto.content_type.mime_type == 'image/jpeg'
            assert obj.props.jpegPhoto.content_type.encoding == 'binary'

            obj_ = user_mod.get(obj.dn)
            obj_.props.jpegPhoto = obj.props.jpegPhoto
            obj_.save()
            obj_ = user_mod.get(obj.dn)
            assert obj_.props.jpegPhoto.raw == encoded_jpg_photo
            assert obj_.props.jpegPhoto.content_type.mime_type == 'image/jpeg'
            assert obj_.props.jpegPhoto.content_type.encoding == 'binary'
        finally:
            obj.delete()

    def test_create_data_with_data(self):
        pass
        # data_mod = self.udm.get('settings/data')
        # obj = data_mod.new()


if __name__ == '__main__':
    main(verbosity=2)
