#!/usr/bin/python3
#
# Univention Directory Manager
#  HTML
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

import json
import xml.etree.ElementTree as ET

import defusedxml.minidom
from genshi import XML

from univention.lib.i18n import Translation


#from genshi.output import HTMLSerializer


_ = Translation('univention-directory-manager-rest').translate


class HTML:

    def content_negotiation_html(self, response):
        self.set_header('Content-Type', 'text/html; charset=UTF-8')
        ajax = self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'

        root = ET.Element("html")
        head = ET.SubElement(root, "head")
        titleelement = ET.SubElement(head, "title")
        titleelement.text = 'FIXME: fallback title'  # FIXME: set title
        ET.SubElement(head, 'meta', content='text/html; charset=utf-8', **{'http-equiv': 'content-type'})
        # if not ajax:
        #    ET.SubElement(head, 'script', type='text/javascript', src=self.abspath('../js/config.js'))
        #    ET.SubElement(head, 'script', type='text/javascript', src=self.abspath('js/udm.js'))
        #    ET.SubElement(head, 'script', type='text/javascript', async='', src=self.abspath('../js/dojo/dojo.js'))

        body = ET.SubElement(root, "body", dir='ltr')
        header = ET.SubElement(body, 'header')
        topnav = ET.SubElement(header, 'nav')
        logo = ET.SubElement(topnav, 'svg')
        ET.SubElement(logo, 'use', **{'xlink:href': "/univention/js/dijit/themes/umc/images/univention_u.svg#id", 'xmlns:xlink': "http://www.w3.org/1999/xlink"})
        h1 = ET.SubElement(topnav, 'h2', id='logo')
        home = ET.SubElement(h1, 'a', rel='home', href=self.abspath('/'))
        home.text = ' '
        nav = ET.SubElement(body, 'nav')
        links = ET.SubElement(nav, 'ul')
        main = ET.SubElement(body, 'main')
        _links = {}
        navigation_relations = self.bread_crumps_navigation()
        for link in self._headers.get_list('Link'):
            link, foo, _params = link.partition(';')
            link = link.strip().lstrip('<').rstrip('>')
            params = {}
            if _params.strip():
                params = {x.strip(): y.strip().strip('"').replace('\\"', '"').replace('\\\\', '\\') for x, y in ((param.split('=', 1) + [''])[:2] for param in _params.split(';'))}
            ET.SubElement(head, "link", href=link, **params)
            _links[params.get('rel')] = dict(params, href=link)
            if params.get('rel') == 'self':
                titleelement.text = params.get('title') or link or 'FIXME:notitle'
            if params.get('rel') in ('stylesheet', 'icon', 'self', 'up', 'udm:object/remove', 'udm:object/edit', 'udm:report'):
                continue
            if params.get('rel') in navigation_relations:
                continue
            if params.get('rel') in ('udm:user-photo',):
                ET.SubElement(nav, 'img', src=link, style='max-width: 200px')
                continue
            elif params.get('rel') in ('create-form', 'edit-form'):
                ET.SubElement(ET.SubElement(nav, 'form'), 'button', formaction=link, **params).text = params.get('title', link)
                continue
            # if params.get('rel') in ('udm:tree',):
            #    self.set_header('X-Frame-Options', 'SAMEORIGIN')
            #    body.insert(1, ET.Element('iframe', src=link, name='tree'))
            #    continue
            li = ET.SubElement(links, "li")
            ET.SubElement(li, "a", href=link, **params).text = params.get('title', link) or link

        for name in navigation_relations:
            params = _links.get(name)
            if params:
                ET.SubElement(topnav, 'a', **params).text = '›› %s' % (params.get('title') or params['href'],)

        if isinstance(response, (list, tuple)):
            main.extend(response)
        elif response is not None:
            main.append(response)

        if not ajax:
            stream = ET.tostring(root, encoding='utf-8', method='xml')
            stream = defusedxml.minidom.parseString(stream)
            stream = stream.toprettyxml()
            stream = XML(stream)
            self.write(stream.render('xhtml'))
            # FIXME: transforms the <use xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="/univention/js/dijit/themes/umc/images/univention_u.svg#id"></use> to <use></use>
            # self.write(''.join(HTMLSerializer('html5')(stream)))
        else:
            self.write('<!DOCTYPE html>\n')
            tree = ET.ElementTree(main if ajax else root)
            tree.write(self)

    def get_html(self, response: dict):
        root = []
        self.add_link(response, 'stylesheet', self.abspath('css/style.css'))

        # TODO: nav-layout?!

        # main layout
        forms = self.get_resources(response, 'udm:form')
        main_layout = self.get_resource(response, 'udm:layout', name='main-layout')
        if main_layout:
            main = ET.Element('div')  # TODO: get rid of the div
            root.append(main)
            self.get_html_layout(main, response, main_layout['layout'], [])
        else:
            # leftover forms
            for _form in forms:
                root.insert(0, self.get_html_form(_form, response))
                root[0].append(ET.Element('hr'))

        # errors
        if isinstance(response.get('error'), dict) and response['error'].get('code', 0) >= 400:
            error_response = response['error']
            error = ET.Element('div', **{'class': 'error'})
            root.append(error)
            ET.SubElement(error, 'h1').text = _('HTTP-Error %d: %s') % (error_response['code'], error_response['title'])
            ET.SubElement(error, 'p', style='white-space: pre').text = error_response['message']
            for error_detail in self.get_resources(response, 'udm:error'):
                ET.SubElement(error, 'p', style='white-space: pre').text = '%s(%s): %s' % ('.'.join(error_detail['location']), error_detail['type'], error_detail['message'])
            if error_response.get('traceback'):
                ET.SubElement(error, 'pre').text = error_response['traceback']
            response = {}

        # redirections
        if 400 > self._status_code >= 300 and self._status_code != 304:
            warning = ET.Element('div', **{'class': 'warning'})
            root.append(warning)
            href = self._headers.get("Location")
            ET.SubElement(warning, 'h1').text = _('HTTP redirection')
            ET.SubElement(warning, 'p', style='white-space: pre').text = 'You are being redirected to:'
            ET.SubElement(warning, 'a', href=href).text = href

        # print any leftover elements
        r = response.copy()
        r.pop('_links', None)
        r.pop('_embedded', None)
        if r:
            pre = ET.Element("pre")
            pre.text = json.dumps(r, indent=4)
            root.append(pre)

        return root

    def get_html_layout(self, root, response, layout, properties):
        for sec in layout:
            from univention.admin.rest.module import Layout
            section = ET.SubElement(root, 'section', id=Layout.get_section_id(sec['label']))
            ET.SubElement(section, 'h1').text = sec['label']
            if sec.get('help'):
                ET.SubElement(section, 'span').text = sec['help']
            fieldset = ET.SubElement(section, 'fieldset')
            ET.SubElement(fieldset, 'legend').text = sec['description']
            if sec['layout']:
                self.render_layout(sec['layout'], fieldset, properties, response)
        return root

    def render_layout(self, layout, fieldset, properties, response):
        for elem in layout:
            if isinstance(elem, dict) and isinstance(elem.get('$form-ref'), list):
                for _form in elem['$form-ref']:
                    form = self.get_resource(response, 'udm:form', name=_form)
                    if form:
                        fieldset.append(self.get_html_form(form, response))
                continue
            elif isinstance(elem, dict):
                if not elem.get('label') and not elem.get('description'):
                    ET.SubElement(fieldset, 'br')
                    sub_fieldset = ET.SubElement(fieldset, 'div', style='display: flex')
                else:
                    sub_fieldset = ET.SubElement(fieldset, 'details', open='open')
                    ET.SubElement(sub_fieldset, 'summary').text = elem['label']
                    if elem['description']:
                        ET.SubElement(sub_fieldset, 'h2').text = elem['description']
                self.render_layout(elem['layout'], sub_fieldset, properties, response)
                continue
            elements = [elem] if isinstance(elem, str) else elem
            for elem in elements:
                for field in properties:
                    if field['name'] in (elem, 'properties.%s' % elem):
                        self.render_form_field(fieldset, field)
            if elements:
                ET.SubElement(fieldset, 'br')

    def get_html_form(self, _form, response):
        form = ET.Element('form', **{p: _form[p] for p in ('id', 'class', 'name', 'method', 'action', 'rel', 'enctype', 'accept-charset', 'novalidate') if _form.get(p)})
        if _form.get('layout'):
            layout = self.get_resource(response, 'udm:layout', name=_form['layout'])
            self.get_html_layout(form, response, layout['layout'], _form.get('fields'))
            return form

        for field in _form.get('fields', []):
            self.render_form_field(form, field)
            form.append(ET.Element('br'))

        return form

    def render_form_field(self, form, field):
        datalist = None
        name = field['name']

        if field.get('type') == 'submit' and field.get('add_noscript_warning'):
            ET.SubElement(ET.SubElement(form, 'noscript'), 'p').text = _('This form requires JavaScript enabled!')

        label = None
        if name:
            label = ET.Element('label', **{'for': name})
            label.text = field.get('label', name)

        multivalue = field.get('data-multivalue') == '1'
        values = field['value'] or [''] if multivalue else [field['value']]
        for value in values:
            elemattrs = {p: field[p] for p in ('id', 'disabled', 'form', 'multiple', 'required', 'size', 'type', 'placeholder', 'accept', 'alt', 'autocomplete', 'checked', 'max', 'min', 'minlength', 'pattern', 'readonly', 'src', 'step', 'style', 'alt', 'autofocus', 'class', 'cols', 'href', 'rel', 'title', 'list') if field.get(p)}
            elemattrs.setdefault('type', 'text')
            elemattrs.setdefault('placeholder', name)
            if field.get('type') == 'checkbox' and field.get('checked'):
                elemattrs['checked'] = 'checked'
            element = ET.Element(field.get('element', 'input'), name=name, value=str(value), **elemattrs)

            if field['element'] == 'select':
                for option in field.get('options', []):
                    kwargs = {}
                    if field['value'] == option['value'] or (isinstance(field['value'], list) and option['value'] in field['value']):
                        kwargs['selected'] = 'selected'
                    ET.SubElement(element, 'option', value=option['value'], **kwargs).text = option.get('label', option['value'])
            elif field.get('element') == 'a':
                element.text = field['label']
                label = None
            elif field.get('list') and field.get('datalist'):
                datalist = ET.Element('datalist', id=field['list'])
                for option in field.get('datalist', []):
                    kwargs = {}
                    if field['value'] == option['value'] or (isinstance(field['value'], list) and option['value'] in field['value']):
                        kwargs['selected'] = 'selected'
                    ET.SubElement(datalist, 'option', value=option['value'], **kwargs).text = option.get('label', option['value'])
            if label is not None:
                form.append(label)
                label = None
            if datalist is not None:
                form.append(datalist)
            form.append(element)
            if multivalue:
                btn = ET.Element('button')
                btn.text = '-'
                form.append(btn)
        if multivalue:
            btn = ET.Element('button')
            btn.text = '+'
            form.append(btn)

    def add_form(self, obj, action, method, **kwargs):
        form = {
            'action': action,
            'method': method,
        }
        form.setdefault('enctype', 'application/x-www-form-urlencoded')
        form.update(kwargs)
        if form.get('name'):
            self.add_link(form, 'self', href='', name=form['name'], dont_set_http_header=True)
        self.add_resource(obj, 'udm:form', form)
        return form

    def add_form_element(self, form, name, value, type='text', element='input', **kwargs):
        field = {
            'name': name,
            'value': value,
            'type': type,
            'element': element,
        }
        field.update(kwargs)
        form.setdefault('fields', []).append(field)
        if field['type'] == 'submit':
            field['add_noscript_warning'] = form.get('method') not in ('GET', 'POST', None)
        return field

    def add_layout(self, obj, layout, name=None, href=None):
        layout = {'layout': layout}
        if name:
            self.add_link(layout, 'self', href='', name=name, dont_set_http_header=True)
        self.add_resource(obj, 'udm:layout', layout)
        if href:
            self.add_link(obj, 'udm:layout', href=href, name=name)

    def bread_crumps_navigation(self):
        return ('udm:object-modules', 'udm:object-module', 'type', 'up', 'self')
