/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._setup.BasisPage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.BasisPage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('General');
		this.headerText = this._('Basic settings');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'fqdn',
			label: this._('Fully qualified domain name (e.g., master.example.com)'),
		}, {
			type: 'TextBox',
			name: 'ldap/base',
			label: this._('LDAP base'),
			depends: 'fqdn'
		}, {
			type: 'TextBox',
			name: 'windows/domain',
			label: this._('Windows domain'),
			depends: 'fqdn'
		}, {
			type: 'PasswordInputBox',
			name: 'root_password',
			label: this._('Root password'),
			required: true
		}];

		var layout = [{
			label: this._('Host and domain settings'),
			layout: ['fqdn', 'ldap/base', 'windows/domain']
		}, {
			label: this._('Access settings'),
			layout: ['root_password']
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave'),
			scrollable: true
		});

		this.connect(this._form.getWidget('fqdn'), 'onChange', function(newVal) {
			function count(s) { 
				var n = 0;
				var i = 0;
				while ((i = s.indexOf('.', i)) >= 0) { 
					++n; 
					++i; 
				}
				return n;
			}

			if (count(newVal) < 2) {
				this.addNote(this._("For Active Directory domains the fully qualified domain name must have at least two dots (e.g. host.example.com). This warning is shown only once, the installation can be continued with the name currently given."));
			}
		});

		this.addChild(this._form);
	},

	setValues: function(_vals) {
		var vals = dojo.mixin({}, _vals);
		vals.fqdn = vals.hostname + '.' + vals.domainname;
		vals.root_password = '';

		// block for setting the values onChange events for FQDN widget
		this._form.getWidget('fqdn').set('blockOnChange', true);

		// in appliance mode, clear the fields for FQDN, LDAP base and Windows domain
		var role = _vals['server/role'];
		var joined = _vals['joined'];
		var applianceMode = umc.tools.status('username') == '__systemsetup__';
		joined = Math.random() > 0.5;
		if (applianceMode && !(joined || role == 'basesystem')) {
			// in appliance mode, we need empty fields for fqdn, LDAP base, and Windows domain
			// that are required
			dojo.forEach(['fqdn', 'ldap/base', 'windows/domain', 'root_password'], function(iname) {
				vals[iname] = '';
				this._form.getWidget(iname).set('disabled', false);
				this._form.getWidget(iname).set('required', true);
			}, this);

			// add dynamic value computation from FQDN fro windows domain and LDAP base
			this._form.getWidget('windows/domain').set('dynamicValue', function(deps) {
				var l = (deps.fqdn || '').split('.');
				if (l.length) {
					return String(l[1]).toUpperCase();
				}
				return '';
			});
			this._form.getWidget('ldap/base').set('dynamicValue', function(deps) {
				var l = (deps.fqdn || '').split('.');
				return dojo.map(l.slice(1), function(part) {
					return 'cn=' + part;
				}).join(',');
			});

		}
		else {
			// in appliance mode, we need empty fields for fqdn, LDAP base, and Windows domain
			// that are required
			dojo.forEach(['fqdn', 'ldap/base', 'windows/domain', 'root_password'], function(iname) {
				this._form.getWidget(iname).set('disabled', true);
				this._form.getWidget(iname).set('required', false);
			}, this);

			// add dynamic value computation from FQDN fro windows domain and LDAP base
			this._form.getWidget('windows/domain').set('dynamicValue', null);
			this._form.getWidget('ldap/base').set('dynamicValue', null);
		}

		this._form.setFormValues(vals);
		this._form.getWidget('fqdn').set('blockOnChange', false);
	},

	getValues: function() {
		var vals = this._form.gatherFormValues();
		var parts = vals.fqdn.split('.');
		vals.hostname = dojo.isString(parts[0]) ? parts[0] : '';
		vals.domainname = parts.slice(1).join('.');
		delete vals.fqdn;
		return vals;
	},

	getSummary: function() {
		var vals = this.getValues();
		return [{
			variables: ['domainname', 'hostname'],
			description: this._('Fully qualified domain name'),
			values: vals['fqdn']
		}, {
			variables: ['ldap/base'],
			description: this._('LDAP base'),
			values: vals['ldap/base']
		}, {
			variables: ['windows/domain'],
			description: this._('Windows domain'),
			values: vals['windows/domain']
		}, {
			variables: ['root_password'],
			description: this._('New root password'),
			values: '********'
		}];
	},

	onSave: function() {
		// event stub
	}
});



