#!/usr/bin/python3
#
# Univention Directory Manager
#  HTML
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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
import re
import xml.etree.ElementTree as ET  # noqa: S405

import defusedxml.minidom
from genshi import XML
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from univention.lib.i18n import Translation


_ = Translation('univention-directory-manager-rest').translate


class HTML:

    @property
    def head_template(self):
        return self.get_template

    def template_vars(self):
        return {}

    def content_negotiation_html(self, response, data):
        self.set_header('Content-Type', 'text/html; charset=UTF-8')
        target = self.request.headers.get('HX-Target')
        hx_request = self.request.headers.get('HX-Request') == 'true'
        ajax = (hx_request or self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest') and target
        head = ET.Element("head")
        title = 'FIXME: fallback title'  # FIXME: set title

        nav = ET.Element('nav')
        links = ET.SubElement(nav, 'ul')
        main = ET.Element('main')

        _links = {}
        navigation_relations = self.bread_crumbs_navigation()
        hal_links = [
            dict(_hlink.copy(), rel=rel)
            for rel, _hlinks in self.get_links(data).items()
            for _hlink in _hlinks
            if 'href' in _hlink
        ]
        for params in hal_links:
            if params.pop('templated', None):
                continue
            link = params.pop('href')
            if params.get('rel') not in ('udm:tab-switch'):
                ET.SubElement(head, "link", href=link, **params)
            _links[params.get('rel')] = dict(params, href=link)
            if params.get('rel') == 'self':
                title = params.get('title') or link or 'FIXME:notitle'
            if params.get('rel') in ('stylesheet', 'icon', 'self', 'up', 'udm:object/remove', 'udm:object/edit', 'udm:report'):
                continue
            if not self.debug_mode_enabled and params.get('rel') in ('udm:report', 'udm:tree', 'udm:layout', 'udm:properties', 'describedby'):
                continue
            if params.get('rel') in navigation_relations:
                continue
            if params.get('rel') in ('udm:user-photo',):
                ET.SubElement(nav, 'img', src=link, style='max-height: 250px; max-width: 100%; padding: 1em;')
                continue
            elif params.get('rel') in ('create-form', 'edit-form'):  # TODO: move into main grid header
                ET.SubElement(ET.SubElement(main, 'form', **{'hx-boost': 'true'}), 'button', formaction=link, **params).text = params.get('title', link)
                continue
            li = ET.SubElement(links, "li")
            params.setdefault('hx-boost', 'true')
            params.setdefault('hx-push-url', 'true')
            ET.SubElement(li, "a", href=link, **params).text = params.get('title', link) or link

        if isinstance(response, (list, tuple)):
            main.extend(response)
        elif response is not None:
            main.append(response)

        def get_inner_html(node):
            return '\n'.join(ET.tostring(child, encoding='unicode', method='xml') for child in node)

        tpldata = {
            'language': self.locale.code,
            'response': response,
            'data': data,
            'title': title,
            'ajax': ajax,
            'hx_request': hx_request,
            'target': target,
            'head_links': get_inner_html(head),
            'nav': get_inner_html(nav),
            'main': get_inner_html(main),
            'display_nav': True,
            'bread_crumbs': [_links.get(name) for name in navigation_relations if _links.get(name)],
        }
        tpldata.update(self.template_vars())
        tpl = getattr(self, f'{self.request.method.lower()}_template', 'template.html')
        stream = self.render_template(tpl, tpldata)
        stream = defusedxml.minidom.parseString(stream).toprettyxml()
        stream = XML(stream).render('xhtml')
        self.write(stream)

    def get_html(self, response: dict):
        root = []
        # TODO: nav-layout?!

        # main layout
        main_layout = self.get_resource(response, 'udm:layout', name='main-layout')
        if main_layout:
            main = ET.Element('div')
            self.get_html_layout(main, response, main_layout['layout'], [])
            root.extend(main.getchildren())
        else:  # leftover forms
            buttons = self.get_resources(response, 'udm:button')
            for _button in buttons:
                root.insert(0, self.get_html_button(_button, response))
            forms = self.get_resources(response, 'udm:form')
            for _form in forms:
                root.insert(0, self.get_html_form(_form, response))
                # root[0].append(ET.Element('hr'))

        root.extend(self.get_error_html(response))

        # print any leftover elements
        if self.debug_mode_enabled:
            r = response.copy()
            r.pop('_links', None)
            r.pop('_embedded', None)
            if r:
                pre = ET.Element("script", type='application/json')
                pre.text = json.dumps(r, indent=4)
                root.append(pre)

        return root

    def get_error_html(self, response: dict):
        root = []
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

        return root

    def get_html_layout(self, root, response, layout, properties):
        for sec in layout:
            section = ET.SubElement(root, 'section', id=self.sanitize_html_id(sec['label']))
            if sec.get('help'):
                ET.SubElement(section, 'span').text = sec['help']
            fieldset = ET.SubElement(section, 'fieldset')
            ET.SubElement(fieldset, 'legend').text = sec['label']
            ET.SubElement(fieldset, 'h1').text = sec['description']
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
            elif isinstance(elem, dict) and isinstance(elem.get('$button-ref'), list):
                for _button in elem['$button-ref']:
                    button = self.get_resource(response, 'udm:button', name=_button)
                    if button:
                        fieldset.append(self.get_html_button(button, response))
                continue
            elif isinstance(elem, dict):
                if not elem.get('label') and not elem.get('description'):
                    ET.SubElement(fieldset, 'br')
                    sub_fieldset = ET.SubElement(fieldset, 'div', style='display: flex')
                else:
                    opened = {'open': 'open'} if elem.get('opened', True) else {}
                    sub_fieldset = ET.SubElement(fieldset, 'details', **opened)
                    ET.SubElement(sub_fieldset, 'summary').text = elem['label']
                    if elem['description']:
                        ET.SubElement(sub_fieldset, 'h2').text = elem['description']
                self.render_layout(elem['layout'], sub_fieldset, properties, response)
                continue
            elements = [elem] if isinstance(elem, str) else elem
            row = ET.SubElement(fieldset, 'div', **{'class': 'row'})
            for elem in elements:
                for field in properties:
                    if field['name'] in (elem, 'properties.%s' % elem):
                        self.render_form_field(row, field)

    def get_html_form(self, _form, response):
        formattrs = {p: _form[p] for p in ('id', 'class', 'name', 'method', 'action', 'rel', 'enctype', 'accept-charset', 'novalidate', 'hx-confirm', 'hx-ext') if _form.get(p)}
        formattrs.setdefault('hx-boost', 'true')
        form = ET.Element('form', **formattrs)
        if _form.get('layout'):
            layout = self.get_resource(response, 'udm:layout', name=_form['layout'])
            self.get_html_layout(form, response, layout['layout'], _form.get('fields'))
            return form

        for field in _form.get('fields', []):
            self.render_form_field(form, field)
            form.append(ET.Element('br'))

        return form

    def render_form_field(self, parent_element, field):
        datalist = None
        name = field['name']

        if field.get('type') == 'submit' and field.get('add_noscript_warning'):
            ET.SubElement(ET.SubElement(parent_element, 'noscript'), 'p').text = _('This form requires JavaScript enabled!')

        label = None
        if name:
            label = ET.Element('label', **{'for': name})
            label.text = field.get('label', name)

        cls = 'udmSize-%s' % (field.get('data-size', 'One'),)
        wrapper = ET.Element('div', **{'class': 'label-wrapper %s' % cls})

        multivalue = field.get('data-multivalue') == '1'
        values = field['value'] or [''] if multivalue else [field['value']]
        for value in values:
            elemattrs = {p: field[p] for p in ('id', 'disabled', 'form', 'multiple', 'required', 'size', 'type', 'placeholder', 'accept', 'alt', 'autocomplete', 'checked', 'max', 'min', 'minlength', 'pattern', 'readonly', 'src', 'step', 'style', 'alt', 'autofocus', 'class', 'cols', 'href', 'rel', 'title', 'list') if field.get(p)}
            elemattrs.setdefault('type', 'text')
            elemattrs.setdefault('placeholder', name)
            if field.get('type') == 'checkbox' and field.get('checked'):
                elemattrs['checked'] = 'checked'
            if field.get('data-dynamic'):
                field['element'] = 'select'
                elemattrs.update({
                    'hx-push-url': 'false',
                    # 'hx-trigger': 'revealed',  # faster but more traffic
                    'hx-trigger': 'intersect once',
                    # 'hx-select': 'select > option',  # bug: no re-rendering in browser, wrong value is displayed
                    # 'hx-swap': 'innerHTML',
                    'hx-select': 'select',  # bug: no attributes like required are taken
                    'hx-swap': 'outerHTML',
                    # 'hx-get': self._append_query(field['data-dynamic'], f'selected={quote(value)}'),
                    'hx-get': field['data-dynamic'],
                    'hx-vals': json.dumps({'selected': value, 'required': field.get('required', ''), 'name': field.get('name', '')})  # caution: allowing freely added values like name=javascript: is a security risk
                })

            element = ET.Element(field.get('element', 'input'), name=name, value=str(value), **elemattrs)

            if field['element'] == 'select':
                if field.get('data-dynamic'):
                    ET.SubElement(wrapper, 'img', **{'class': 'htmx-indicator spinner', 'src': '/univention/udm/img/spinning-circles.svg'})
                    ET.SubElement(element, 'option', selected='selected', value=value).text = value  # fallback during loading
                else:
                    for option in field.get('options', []):
                        kwargs = {}
                        if field['value'] == option['value'] or (isinstance(field['value'], list) and option['value'] in field['value']):
                            kwargs['selected'] = 'selected'
                        ET.SubElement(element, 'option', value=option['value'], **kwargs).text = option.get('label', option['value'])
            elif field.get('element') == 'a':
                element.text = field['label']
                label = None
            elif field.get('type') == 'hidden':
                label = None
            elif field.get('list') and field.get('datalist'):
                datalist = ET.Element('datalist', id=field['list'])
                for option in field.get('datalist', []):
                    kwargs = {}
                    if field['value'] == option['value'] or (isinstance(field['value'], list) and option['value'] in field['value']):
                        kwargs['selected'] = 'selected'
                    ET.SubElement(datalist, 'option', value=option['value'], **kwargs).text = option.get('label', option['value'])
            if label is not None:
                wrapper.append(label)
                label = None
            if datalist is not None:
                wrapper.append(datalist)

            wrapper.append(element)
            if multivalue:
                btn = ET.Element('button')
                btn.text = '-'
                wrapper.append(btn)
        if multivalue:
            btn = ET.Element('button')
            btn.text = '+'
            wrapper.append(btn)

        parent_element.append(wrapper)

    def get_html_button(self, _button, response):
        # buttonattrs = {p: _button[p] for p in ('id', 'class', 'name', 'method', 'action', 'rel', 'enctype', 'accept-charset', 'novalidate') if _button.get(p)}
        label = _button.pop('label', '')
        buttonattrs = _button
        buttonattrs.setdefault('hx-boost', 'true')
        button = ET.Element('button', **buttonattrs)
        button.text = label
        return button

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
            field['add_noscript_warning'] = form.get('method', '').upper() not in ('GET', 'POST', '')
        return field

    def add_button(self, obj, action, method, **kwargs):
        button = {'hx-%s' % method.lower(): action, 'formaction': action, 'hx-boost': 'true'}
        button.update(kwargs)
        # title = kwargs.pop('title', '')
        # form = self.add_form(obj, action, method, **kwargs)
        # self.add_form_element(form, '', title, type='submit')

        self.add_resource(obj, 'udm:button', button)

    def add_layout(self, obj, layout, name=None, href=None):
        layout = {'layout': layout}
        if name:
            self.add_link(layout, 'self', href='', name=name, dont_set_http_header=True)
        self.add_resource(obj, 'udm:layout', layout)
        if href:
            self.add_link(obj, 'udm:layout', href=href, name=name)

    @classmethod
    def sanitize_html_id(cls, label):
        label = re.sub(r'[^a-z0-9_:-]', '_', label.lower())
        return re.sub(r'^[^a-z]+', 'id_', label)

    def bread_crumbs_navigation(self):
        return ('udm:object-modules', 'udm:object-module', 'type', 'up', 'self')

    def render_template(self, template_path, data):
        env = Environment(loader=FileSystemLoader('/usr/share/univention-directory-manager-rest/templates/'), autoescape=True, undefined=StrictUndefined)
        template = env.get_template(template_path)
        env.filters['translate'] = self.locale.translate
        env.globals['self'] = self
        return template.render(**data)
