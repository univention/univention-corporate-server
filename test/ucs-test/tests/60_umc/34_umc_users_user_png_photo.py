#!/usr/share/ucs-test/runner python3
## desc: Test setting of user photo via UMC
## bugs: [36273]
## roles:
##  - domaincontroller_master
## exposure: dangerous

import base64
import subprocess
import sys
from tempfile import NamedTemporaryFile

from univention.admin.syntax import jpegPhoto as jpegPhotoSyntaxClass
from univention.testing import utils
from univention.testing.strings import random_username
from univention.testing.udm import UCSTestUDM

from umc import UMCBase


def reencode_image(original_bytes: bytes) -> bytes:
    # for some reason when uploading through UMC the image get's decoded (passed through the syntax class pase method) twice
    b64_string = base64.b64encode(original_bytes).decode('ASCII')
    once = jpegPhotoSyntaxClass.parse(b64_string)
    return base64.b64decode(jpegPhotoSyntaxClass.parse(once))


class TestUMCUserAuthentication(UMCBase):

    def __init__(self):
        """Test Class constructor"""
        super().__init__()

        self.UDM = None

        self.test_user_dn = ''
        self.test_username = ''
        self.test_password = ''

    def create_user(self):
        self.test_user_dn = self.UDM.create_user(
            password=self.test_password,
            username=self.test_username,
            policy_reference='cn=default-umc-all,cn=UMC,cn=policies,%s' % self.ucr['ldap/base'],
        )[0]
        utils.verify_ldap_object(self.test_user_dn)

    def set_image_jpeg(self):
        with open('./34_userphoto.jpeg', 'rb') as fd:
            image = fd.read()
        assert reencode_image(image) == base64.b64decode(self.set_image(image)), "Failed to set JPEG user photo"

    def set_image_jpg(self):
        with open('./34_userphoto.jpg', 'rb') as fd:
            image = fd.read()
        assert reencode_image(image) == base64.b64decode(self.set_image(image)), "Failed to set JPG user photo"

    def set_image_png(self):
        with open('./34_userphoto.png', 'rb') as fd:
            image = fd.read()
        image = base64.b64decode(self.set_image(image))
        with NamedTemporaryFile(mode='wb') as tempfile:
            tempfile.write(image)
            tempfile.flush()
            p = subprocess.Popen(['/usr/bin/file', '-i', tempfile.name], stdout=subprocess.PIPE)
            stdout, _stderr = p.communicate()
            assert b'image/jpeg' in stdout, f"Failed to set PNG user photo (not converted to JPEG): {stdout!r}"

    def unset_image(self):
        assert not self.set_image(""), "Failed to unset user photo"

    def set_image(self, jpegPhoto):
        if jpegPhoto:
            jpegPhoto = base64.b64encode(jpegPhoto).decode('ASCII')  # TODO: make umcp/upload request
        self.modify_object([{"object": {"jpegPhoto": jpegPhoto, "$dn$": self.test_user_dn}}], 'users/user')
        response = self.get_object([self.test_user_dn], 'users/user')
        return response[0].get('jpegPhoto')

    def main(self):
        """Tests the UMC user authentication and various password change cases."""
        self.test_username = 'umc_test_user_' + random_username(6)
        self.test_password = 'univention'

        with UCSTestUDM() as self.UDM:
            self.create_user()
            self.create_connection_authenticate()

            self.set_image_jpeg()
            self.set_image_jpg()
            self.set_image_png()
            self.unset_image()


if __name__ == '__main__':
    TestUMC = TestUMCUserAuthentication()
    sys.exit(TestUMC.main())
