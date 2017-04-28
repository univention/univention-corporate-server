#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import argparse
import datetime
import ldif
import sys
from time import time, localtime, strftime
from os import path
from univention.testing.codes import TestCodes
from univention.testing.license_client import TestLicenseClient, CredentialsMissing


def parse_args():
    parser = argparse.ArgumentParser(description='Create an UCS license file.')
    parser.add_argument('ldap_base', help='The LDAP-base which the license file is generated for.')
    parser.add_argument('--license-file', dest='license_file', required=True, help='Path to place the generated license file at.')
    parser.add_argument('--secret-file', dest='secret_file', help='Path to the file containing the password.')
    parser.add_argument('--force-renewal', dest='force_renewal', action='store_true', help='Generate a new license file, even if there is already a valid one.')
    return parser.parse_args()


class JenkinsTestLicenseClient(TestLicenseClient, object):
    def __init__(self, secret_file, ArgParser=None):
        super(JenkinsTestLicenseClient, self).__init__(ArgParser)
        self.secret_file = secret_file

    def get_server_password(self, secret_file='legacy'):
        self.log.debug("In 'get_server_password': secret_file='%s'"
                       % self.secret_file)
        if not path.exists(self.secret_file):
            self.log.critical("The '%s' secret file does not exist, cannot "
                              "proceed without password" % secret_file)
            raise CredentialsMissing("The '%s' secret file does not exist"
                                     % self.secret_file)
        try:
            with open(self.secret_file, 'r') as password:
                self.server_password = password.read()
        except (IOError, ValueError) as exc:
            self.log.exception("Failed to get the password from the '%s', "
                               "an error occured: %r"
                               % (self.secret_file, exc))
            exit(1)
        if not self.server_password:
            self.log.critical("The password to access the license service "
                              "cannot be empty")
            exit(1)


class LicenseCreator(object):
    def __init__(
            self,
            ldap_base,
            license_file,
            secret_file='/var/lib/jenkins/ec2/license/license.secret',
            force_renewal=False):
        self.ldap_base = ldap_base
        self.license_file = license_file
        self.secret_file = secret_file
        self.force_renewal = force_renewal

    def provide_valid_license(self):
        if self.force_renewal or not self.valid_license_exists():
            print("Obtaining a valid license for the ldap base '%s'."
                  % (self.ldap_base,))
            self.get_license()
            print("Wrote new license to '%s'." % (self.license_file,))
        else:
            print("A valid license file already exists at '%s'. "
                  "Not obtaining a new one." % (self.license_file,))

    def valid_license_exists(self):
        try:
            with open(self.license_file, 'r') as license_file:
                parser = ldif.LDIFRecordList(license_file)
                parser.parse()
            end_date_string = parser.all_records[0][1]["univentionLicenseEndDate"][0]
            end_date = datetime.datetime.strptime(end_date_string, "%d.%m.%Y").date()

            valid_license_exists = end_date > datetime.date.today()
        except IOError:
            valid_license_exists = False

        return valid_license_exists

    def get_license(self):
        end_date = time()
        end_date += 2630000  # approx. amount of seconds in 1 month
        end_date = strftime('%d.%m.%Y', localtime(end_date))

        LicenseClient = JenkinsTestLicenseClient(self.secret_file)
        try:
            LicenseClient.main(base_dn=self.ldap_base,
                               end_date=end_date,
                               license_file=self.license_file)
        except CredentialsMissing as exc:
            print("\nMissing a secret file with password to order a license: "
                  "%r" % exc)
            sys.exit(TestCodes.REASON_INSTALL)

if __name__ == '__main__':
    args = parse_args()
    license_creator = LicenseCreator(
        args.ldap_base, args.license_file, args.secret_file, args.force_renewal
    )
    license_creator.provide_valid_license()
