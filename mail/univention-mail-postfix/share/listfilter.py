#!/usr/bin/python3 -u
#
# Univention mail Postfix Policy
#  check allowed email senders for groups and distlist
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2005-2024 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.


import argparse
import re
import sys
import syslog
import traceback
from typing import Dict

from ldap.filter import filter_format

import univention.admin.modules
from univention.config_registry import ConfigRegistry
from univention.uldap import getMachineConnection


LIST_FILTER_PW_FILE = "/etc/listfilter.secret"

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--ldap_base", help="ldap base")
parser.add_argument("-s", "--sender", help="sender address (for use with -t)")
parser.add_argument("-r", "--recipient", help="sender address (for use with -t)")
parser.add_argument("-t", "--test", help="test run", action="store_true", default=False)
options = parser.parse_args()

syslog.openlog(ident="listfilter", logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)
ucr = ConfigRegistry()
ucr.load()
univention.admin.modules.update()
usersmod = univention.admin.modules.get("users/user")
check_sasl_username = ucr.is_true("mail/postfix/policy/listfilter/use_sasl_username", True)
_do_debug = ucr.is_true("mail/postfix/policy/listfilter/debug", False)
use_dovecot_sasl = ucr.is_true("mail/postfix/dovecot_sasl", False)


def debug(msg, *args):
    if _do_debug:
        msg = f"listfilter: {msg % args}"
        if options.test:
            print(msg, file=sys.stderr)
        else:
            syslog.syslog(syslog.LOG_DEBUG, msg)


def listfilter(attrib: Dict[str, str]) -> str:
    sender = attrib.get("sasl_username") if check_sasl_username else attrib.get("sender")
    recipient = attrib.get("recipient")

    debug("sender=%r recipient=%r check_sasl_username=%r use_dovecot_sasl=%r", sender, recipient, check_sasl_username, use_dovecot_sasl)
    debug("attrib=%r", attrib)

    if not options.ldap_base:
        return "443 LDAP base not set."
    elif not recipient:
        # We will never get here, because an empty recipient will have been rejected
        # earlier by Postfix with "554 5.5.1 Error: no valid recipients".
        return "REJECT Access denied for empty recipient."

    # try the ldap stuff, if that fails send email anyway
    try:
        return check_ldap_users_and_groups(sender, recipient)
    except Exception:
        return "WARN Error with sender={} recipient={} attrib={}, check_sasl_username={}, traceback={}".format(
            sender, recipient, attrib, check_sasl_username, traceback.format_exc().replace("\n", " "))


def check_ldap_users_and_groups(sender: str, recipient: str) -> str:
    ldap = getMachineConnection(ldap_master=False, secret_file=LIST_FILTER_PW_FILE)

    # get recipient restriction
    ldap_attr = ["univentionAllowedEmailGroups", "univentionAllowedEmailUsers"]
    ldap_filter = filter_format(
        "(&(mailPrimaryAddress=%s)(|(objectclass=univentionMailList)(objectclass=posixGroup)))",
        (recipient,))
    result = ldap.search(base=options.ldap_base, filter=ldap_filter, attr=ldap_attr)

    if not result:
        return f"DUNNO no group found for {recipient!r}"

    # get allowed user and group dns
    allowed_group_dns = {g.decode("UTF-8") for g in result[0][1].get("univentionAllowedEmailGroups", [])}
    allowed_user_dns = {u.decode("UTF-8") for u in result[0][1].get("univentionAllowedEmailUsers", [])}

    if not allowed_user_dns and not allowed_group_dns:
        return "DUNNO no restrictions"

    # check if there are restrictions, check sender first
    debug("allowed_user_dns=%r allowed_group_dns=%r", allowed_user_dns, allowed_group_dns)
    if not sender:
        if check_sasl_username:
            return f"REJECT Access denied for not authenticated sender to restricted list {recipient}"
        else:
            return f"REJECT Access denied for empty sender to restricted list {recipient!r}"

    # get dn and groups of sender
    if check_sasl_username:
        if use_dovecot_sasl:
            user_filter = filter_format("(uid=%s)", (sender,))
        else:
            user_filter = filter_format("(|(uid=%s)(mailPrimaryAddress=%s))", (sender, sender))
    else:
        user_filter = filter_format(
            "(|(mailPrimaryAddress=%s)(mailAlternativeAddress=%s)(mail=%s))",
            (sender, sender, sender),
        )
    ldap_filter = usersmod.lookup_filter(user_filter)
    user_result = ldap.search(base=options.ldap_base, filter=str(ldap_filter), attr=["dn"])
    users_groups = set()
    if user_result:
        user_dn = user_result[0][0]
        debug("user_dn=%r", user_dn)

        # check user_dn in univentionAllowedEmailUsers
        if allowed_user_dns and user_dn and user_dn in allowed_user_dns:
            return "DUNNO allowed per user dn"

        ldap_filter = filter_format("(uniqueMember=%s)", (user_dn,))
        group_result = ldap.search(base=options.ldap_base, filter=ldap_filter, attr=["dn"])
        users_groups.update(i[0] for i in group_result)

    # check groups
    if allowed_group_dns and users_groups:
        debug("users_groups=%r", users_groups)
        # check user groups in univentionAllowedEmailGroups
        for j in users_groups:
            if j in allowed_group_dns:
                return "DUNNO allowed per group membership"
        # check nested group in univentionAllowedEmailGroups, depth 1!
        for a in allowed_group_dns:
            nested = ldap.getAttr(a, "uniqueMember")
            debug("nested=%r", nested)
            for b in users_groups:
                if b.encode("UTF-8") in nested:
                    return "DUNNO allowed per nested group"

    return f"REJECT Access denied for {sender!r} to restricted list {recipient!r}"


def mail2username(mail: str) -> str:
    try:
        ldap = getMachineConnection(ldap_master=False)
        user_filter = filter_format(
            "(|(mailPrimaryAddress=%s)(mailAlternativeAddress=%s)(mail=%s))", (mail, mail, mail),
        )
        ldap_filter = usersmod.lookup_filter(user_filter)
        user_result = ldap.search(base=options.ldap_base, filter=str(ldap_filter), attr=["uid"])
        return user_result[0][1]["uid"][0].decode("UTF-8")
    except Exception as exc:
        print(f"Could not parse sasl_username from mail address {mail!r}: {exc!s}\n")
        sys.exit(1)


if __name__ == "__main__":
    attr: Dict[str, str] = {}

    # testing
    if options.test:
        _do_debug = True
        if not options.sender or not options.recipient:
            print("sender and recipient are required", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        attr["sender"] = options.sender
        attr["sasl_username"] = mail2username(options.sender)
        attr["recipient"] = options.recipient
        action = listfilter(attr)
        print(f"action={action}\n")
    else:
        # read from stdin python -u is required for unbuffered streams
        while True:
            data = sys.stdin.readline()
            m = re.match(r"([^=]+)=(.*)\n", data)
            if m:
                attr[m[1].strip()] = m[2].strip()

            elif data == "\n":
                if attr.get("request") == "smtpd_access_policy":
                    action = listfilter(attr)
                    debug("action=%r", action)
                    print(f"action={action}\n")
                else:
                    print(f"unknown action in {attr!r}", file=sys.stderr)
                    print("defer_if_permit Service temporarily unavailable")
                    syslog.syslog(syslog.LOG_ERR, f"unknown action in {attr!r}, exiting.")
                    sys.exit(1)
                attr = {}
            elif data == "":
                # Postfix telling us to shut down (max_idle).
                debug("shutting down (max_idle)")
                sys.exit(0)
            else:
                syslog.syslog(syslog.LOG_ERR, f"received bad data: {data!r}, exiting.")
                sys.exit(1)
