#
# UCS test
#
# Copyright 2013-2015 Univention GmbH
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

import dns.resolver as resolver
import dns.query as query_udp
import dns.message as message
import dns.rdatatype
import time

from dns.exception import Timeout
from dns.exception import DNSException
from dns.exception import FormError
from dns.resolver import NXDOMAIN
from dns.resolver import NoAnswer
from dns.resolver import NoNameservers

def resolveDnsEntry(duration, zoneName, resourceRecord, resourceRecord_Number):

	start = time.time()
	timeout = 3
	flag = False

	while flag == False:
		try:
			wait = time.time()
			wait_flag = False
			while wait_flag == False:
				if(time.time() - wait > 1):
					wait_flag = True

			answer = resolver.query(zoneName, resourceRecord)
			flag = True
			return answer

		except Timeout:
			timeout = timeout - 1
			if timeout < 1:
				raise Timeout(
					'no answers could be found in the specified lifetime '
					+ 'NameToResolve: '
					+ zoneName
					+ ' ResourceRecord: '
					+ resourceRecord)
		except NXDOMAIN:
			diff = time.time() - start
			if(diff > duration):
				raise NXDOMAIN(
					'the query name does not exist '
					+ 'NameToResolve: '
					+ zoneName
					+ ' ResourceRecord: '
					+ resourceRecord
					+ ' Time waited: '
					+ str(diff) )
		except NoAnswer:
			query = message.make_query(zoneName, resourceRecord_Number)
			try:
				answer = query_udp.udp(query, zoneName)
				flag = True
				return answer
			except DNSException:
				raise DNSException(
					'query response comes from unexpected address or port '
					+ 'NameToResolve: '
					+ zoneName
					+ ' ResourceRecord: '
					+ resourceRecord)
			except FormError:
				raise FormError(
					'query response does not respond to the question asked '
					+ 'NameToResolve: '
					+ zoneName
					+ ' ResourceRecord: ' +
					resourceRecord)
			print 'the response did not contain an answer to the question '
			+ 'NameToResolve: '
			+ zoneName
			+ ' ResourceRecord: '
			+ resourceRecord
		except NoNameservers:
			raise NoNameservers(
				'no non-broken nameservers are available to answer the query '
				+ 'NameToResolve: '
				+ zoneName
				+ ' ResourceRecord: '
				+ resourceRecord )
		except Exception as e:
			if e is dns.resolver.YXDOMAIN:
				raise dns.resolver.YXDOMAIN(
					'the query name does not exist ' + 'NameToResolve: '
					+ zoneName +
					' ResourceRecord: '
					+ resourceRecord
					+ ' Time waited: '
					+ str(diff) )
			else:
				raise Exception(
					'the query name does not exist '
					+ 'NameToResolve: '
					+ zoneName
					+ ' ResourceRecord: '
					+ resourceRecord
					+ ' Time waited: '
					+ str(diff) )


if __name__ == '__main__':
    pass

