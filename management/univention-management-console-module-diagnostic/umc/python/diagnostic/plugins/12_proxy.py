#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2016-2024 Univention GmbH
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

import io
import traceback
from urllib.parse import urlparse

import pycurl

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, Warning


_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Proxy server failure')
description = _('There was an error using the proxy server. The {setup:network} can be used to change the proxy configuration.\n')
umc_modules = [{
    'module': 'setup',
    'flavor': 'network',
}]
run_descr = ['Checks if the proxy server runs correctly']


def run(_umc_instance: Instance, url: str = 'http://www.univention.de/', connecttimeout: int = 30, timeout: int = 30) -> None:
    proxy = ucr.get('proxy/http')
    if not proxy:
        return

    proxy = urlparse(proxy)
    MODULE.info('The proxy is configured, using host=%r, port=%r' % (proxy.hostname, proxy.port))
    curl = pycurl.Curl()
    curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)
    if proxy.hostname:
        curl.setopt(pycurl.PROXY, proxy.hostname)
    if proxy.port:
        curl.setopt(pycurl.PROXYPORT, proxy.port)
    curl.setopt(pycurl.FOLLOWLOCATION, True)
    curl.setopt(pycurl.MAXREDIRS, 5)
    curl.setopt(pycurl.CONNECTTIMEOUT, connecttimeout)
    curl.setopt(pycurl.TIMEOUT, 30)
    if proxy.username:
        curl.setopt(pycurl.PROXYAUTH, pycurl.HTTPAUTH_ANY)
        credentials = '%s' % (proxy.username,)
        if proxy.password:
            credentials = '%s:%s' % (proxy.username, proxy.password)
        curl.setopt(pycurl.PROXYUSERPWD, credentials)

    curl.setopt(pycurl.URL, url)
    # curl.setopt(pycurl.VERBOSE, bVerbose)

    buf = io.BytesIO()
    curl.setopt(pycurl.WRITEFUNCTION, buf.write)
    MODULE.process(''.join("Trying to connect to %s via HTTP proxy %s" % (url, proxy)))

    try:
        curl.perform()
    except pycurl.error as exc:
        try:
            code, msg = exc.args
            msg = '%s (code=%s)' % (msg, code)
            MODULE.info(msg)
        except ValueError:
            MODULE.error(traceback.format_exc())
            code = 0
            msg = str(exc)
        if code == pycurl.E_COULDNT_CONNECT:
            msg = _('The proxy host could not be reached. Make sure that hostname (%(hostname)r) and port (%(port)r) are correctly set up.') % {'hostname': proxy.hostname, 'port': proxy.port}
        elif code == pycurl.E_COULDNT_RESOLVE_PROXY:
            msg = _('The hostname of the proxy could not be resolved. May check your DNS configuration.')
        elif code == pycurl.E_OPERATION_TIMEOUTED:
            msg = _('The server did not respond within %d seconds. Please check your network configuration.') % (timeout,)
        elif code == 0:
            MODULE.error(traceback.format_exc())

        MODULE.error('\n'.join([description, msg]))
        raise Critical('\n'.join([description, msg]))
    else:
        # page = buf.getvalue()
        # MODULE.info(page[:100])
        buf.close()
        http_status = curl.getinfo(pycurl.HTTP_CODE)
        if http_status >= 400:
            warning = '\n'.join([
                description,
                _('The proxy server is reachable but the HTTP response status code (%d) does not indicate success.') % (http_status,),
                _('This warning might be harmless. Nevertheless make sure the authentication credentials (if any) are correct and the proxy server ACLs do not forbid requests to %s.') % (url,),
            ])
            MODULE.warn(warning)
            raise Warning(warning)
    finally:
        curl.close()


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main
    main()
