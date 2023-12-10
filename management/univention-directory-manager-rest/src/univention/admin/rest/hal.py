#!/usr/bin/python3
#
# Univention Directory Manager
#  Hypertext Application Language JSON
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2023 Univention GmbH
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


class HAL:

    def content_negotiation_hal_json(self, response, data):
        data = self.content_negotiation_json(response, data)
        self.set_header('Content-Type', 'application/hal+json')
        return data

    def get_hal_json(self, response):
        response.setdefault('_links', {})
        response.setdefault('_embedded', {})
        return self.get_json(response)

    def add_link(self, obj, relation, href, **kwargs):
        dont_set_http_header = kwargs.pop('dont_set_http_header', False)
        links = obj.setdefault('_links', {})
        links.setdefault(relation, []).append(dict(kwargs, href=href))
        if dont_set_http_header:
            return

        def quote_param(s):
            for char in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f':  # remove non printable characters
                s = s.replace(char, '')
            return s.encode('ISO8859-1', 'replace').decode('ISO8859-1').replace('\\', '\\\\').replace('"', '\\"')
        kwargs['rel'] = relation
        params = [
            '%s="%s"' % (param, quote_param(kwargs.get(param, '')))
            for param in ('rel', 'name', 'title', 'media')
            if param in kwargs
        ]
        del kwargs['rel']
        header_name = 'Link-Template' if kwargs.get('templated') else 'Link'
        self.add_header(header_name, '<%s>; %s' % (href, '; '.join(params)))

    def add_resource(self, obj, relation, ressource):
        obj.setdefault('_embedded', {}).setdefault(relation, []).append(ressource)

    def get_resource(self, obj, relation, **query):
        for resource in obj.get('_embedded', {}).get(relation, []):
            if not query:
                return resource
            data = resource.get('_links', {}).get('self', [{}])[0]
            if all(data.get(key) == val for key, val in query.items()):
                return resource

    def get_resources(self, obj, relation):
        return obj.get('_embedded', {}).get(relation, [])

    def get_links(self, obj, relation=None):
        if relation is None:
            return obj.get('_links', {})
        return obj.get('_links', {}).get(relation, [])
