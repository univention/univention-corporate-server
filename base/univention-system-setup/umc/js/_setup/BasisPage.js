/*
 * Copyright 2011-2012 Univention GmbH
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
dojo.require("umc.dialog");
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

	// system-setup-boot
	wizard_mode: false,

	// __systemsetup__ user is logged in at local firefox session
	local_mode: false,

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// internal flag whether setValues() has been called at least once or not
	_firstSetValues: true,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('General');
		this.headerText = this._('Basic settings');
		this.helpText = this._('The <i>basic settings</i> define essential properties, such as host and domain name, LDAP base, Windows domain name as well as the system administrators (root) password.');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'fqdn',
			label: this._('Fully qualified domain name (e.g. master.example.com)'),
			required: true
		}, {
			type: 'TextBox',
			name: 'ldap/base',
			label: this._('LDAP base'),
			depends: 'fqdn',
			required: true
		}, {
			type: 'TextBox',
			name: 'windows/domain',
			label: this._('Windows domain'),
			depends: 'fqdn',
			required: true
		}, {
			type: 'PasswordInputBox',
			name: 'root_password',
			label: this._('Root password')
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

		this.connect(this._form.getWidget('fqdn'), 'onChange', 'onValuesChanged');
		var fc = this.connect(this._form.getWidget('fqdn'), 'onChange', function(newVal) {
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
			this.disconnect(fc);
		});

		this.addChild(this._form);
	},

	setValues: function(_vals) {
		var vals = dojo.mixin({}, _vals);
		vals.fqdn = vals.hostname + '.' + vals.domainname;
		if (vals.fqdn == '.') {
			// hostname == "" and domainname == ""
			vals.fqdn = "";
		}
		vals.root_password = '';

		// block for setting the values onChange events for FQDN widget
		this._form.getWidget('fqdn').set('blockOnChange', true);

		// decide which files are visible/required/empty/disabled in which scenario
		var role = _vals['server/role'];
		var _set = dojo.hitch(this, function(iname, disabled, required, empty, visible) {
			var widget = this._form.getWidget(iname);
			widget.set('disabled', disabled);
			if (required === false || required === true) {
				widget.set('required', required);
			}
			vals[iname] = empty === true ? '' : vals[iname];
			widget.set('visible', visible !== false);
			if (visible === false) {
				// make sure that invisible fields are not required
				widget.set('required', false);
			}
		});

		_set('fqdn', !this.wizard_mode && role != 'basesystem', true, this.wizard_mode && this._firstSetValues);
		_set('windows/domain', !this.wizard_mode && role != 'basesystem', role != 'basesystem', this.wizard_mode && this._firstSetValues);
		_set('ldap/base', !this.wizard_mode && role != 'basesystem', role != 'basesystem', this.wizard_mode && this._firstSetValues, role == 'domaincontroller_master' || role == 'basesystem');
		_set('root_password', false, this.wizard_mode && !this.local_mode);

		if (role != 'basesystem' && this.wizard_mode) {
			// add dynamic value computation from FQDN for windows domain
			this._form.getWidget('windows/domain').set('dynamicValue', function(deps) {
				var l = (deps.fqdn || '').split('.');
				if (l.length && l[1]) {
					return String(l[1]).toUpperCase();
				}
				return ' ';
			});
		}
		if (role == 'domaincontroller_master' && this.wizard_mode) {
			// add dynamic value computation from FQDN for LDAP base
			this._form.getWidget('ldap/base').set('dynamicValue', function(deps) {
				var l = (deps.fqdn || '').split('.');
				return dojo.map(l.slice(1), function(part) {
					return 'dc=' + part;
				}).join(',');
			});

		}

		this._form.setFormValues(vals);
		this._form.getWidget('fqdn').set('blockOnChange', false);
		this._firstSetValues = false;
	},

	getValues: function() {
		var vals = this._form.gatherFormValues();
		var parts = vals.fqdn.split('.');
		vals.hostname = dojo.isString(parts[0]) ? parts[0] : '';
		vals.domainname = parts.slice(1).join('.');
		delete vals.fqdn;

		if (!this._form.getWidget('ldap/base').get('visible')) {
			// remove the ldap/base entry
			delete vals['ldap/base'];
		}

		return vals;
	},

	getSummary: function() {
		var vals = this.getValues();
		return [{
			variables: ['domainname', 'hostname'],
			description: this._('Fully qualified domain name'),
			values: vals['hostname'] + '.' + vals['domainname']
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
	},

	onValuesChanged: function() {
		// event stub
	},

	validate: function() {
		var values = this.getValues();
		if (values.hostname.toLowerCase() == values['windows/domain'].toLowerCase()) {
			umc.dialog.alert(this._('Hostname and windows domain may not be equal.'));
			return false;
		}
		var warnings = [];
		if (values.hostname.length > 13) {
			warnings.push(this._('If at any time samba should be used on this system, the length of the hostname may be at most 13 characters.'));
		}
		if (!values.root_password) {
			warnings.push(this._('Root password empty. Continue?'));
		}
		if (warnings.length) {
			return umc.dialog.confirm(warnings.join('<br />'),
				[{
					label: this._('Cancel'),
					'default': true,
					name: 'cancel'
				}, {
					label: this._('Continue'),
					name: 'continue'
				}]
			).then(function(response) {
				return 'continue' == response;
			});
		}
		return true;
	}

});



