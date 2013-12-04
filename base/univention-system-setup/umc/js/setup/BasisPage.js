/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordInputBox",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, dialog, Page, Form, TextBox, PasswordInputBox, _) {

	return declare("umc.modules.setup.BasisPage", [ Page ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit UDM objects.

		// system-setup-boot
		wizard_mode: false,

		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		umcpCommand: tools.umcpCommand,

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		// internal flag whether setValues() has been called at least once or not
		_firstSetValues: true,

		// internal flag to not show the FQDN warning twice. See Bug #33437
		_fqdnWarningAdded: false,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('General');
			this.headerText = _('Basic settings');
			this.helpText = _('The <i>basic settings</i> define essential properties, such as host and domain name, LDAP base, Windows domain name as well as the system administrators (root) password.');
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: TextBox,
				name: 'fqdn',
				label: _('Fully qualified domain name (e.g. master.example.com)'),
				required: true
			}, {
				type: TextBox,
				name: 'ldap/base',
				label: _('LDAP base'),
				depends: 'fqdn',
				required: true
			}, {
				type: TextBox,
				name: 'windows/domain',
				label: _('Windows domain'),
				depends: 'fqdn',
				required: true
			}, {
				type: PasswordInputBox,
				name: 'root_password',
				label: _('Root password')
			}];

			var layout = [{
				label: _('Host and domain settings'),
				layout: ['fqdn', 'ldap/base', 'windows/domain']
			}, {
				label: _('Access settings'),
				layout: ['root_password']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			this.own(this._form.getWidget('fqdn').watch('value', lang.hitch(this, 'onValuesChanged')));
			var fc = this._form.getWidget('fqdn').watch('value', lang.hitch(this, function(name, oldVal, newVal) {
				function count(s) { 
					var n = 0;
					var i = 0;
					while ((i = array.indexOf(s, '.', i)) >= 0) { 
						++n; 
						++i; 
					}
					return n;
				}

				if (count(newVal) < 2 && !this._fqdnWarningAdded) {
					this._fqdnWarningAdded = true;
					this.addWarning(_("For Active Directory domains the fully qualified domain name must have at least two dots (e.g. host.example.com). This warning is shown only once, the installation can be continued with the name currently given."));
					fc.remove();
				}
			}));
			this.own(fc);

			this.addChild(this._form);
		},

		setValues: function(_vals) {
			var vals = lang.mixin({}, _vals);
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
			var _set = lang.hitch(this, function(iname, disabled, required, empty, visible) {
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
			_set('windows/domain', !this.wizard_mode && role != 'basesystem', role != 'basesystem', this.wizard_mode && this._firstSetValues, role == 'domaincontroller_master' || role == 'basesystem');
			_set('ldap/base', !this.wizard_mode && role != 'basesystem', role != 'basesystem', this.wizard_mode && this._firstSetValues, role == 'domaincontroller_master' || role == 'basesystem');
			_set('root_password', false, this.wizard_mode && this.local_mode);

			if (role == 'domaincontroller_master' && this.wizard_mode) {
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
					return array.map(l.slice(1), function(part) {
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
			vals.hostname = typeof parts[0] == "string" ? parts[0] : '';
			vals.domainname = parts.slice(1).join('.');
			delete vals.fqdn;

			if (!this._form.getWidget('ldap/base').get('visible')) {
				// remove the ldap/base entry
				delete vals['ldap/base'];
			}

			if (!this._form.getWidget('windows/domain').get('visible')) {
				// remove the windows/domain entry
				delete vals['windows/domain'];
			}

			return vals;
		},

		getSummary: function() {
			var vals = this.getValues();
			return [{
				variables: ['domainname', 'hostname'],
				description: _('Fully qualified domain name'),
				values: vals['hostname'] + '.' + vals['domainname']
			}, {
				variables: ['ldap/base'],
				description: _('LDAP base'),
				values: vals['ldap/base']
			}, {
				variables: ['windows/domain'],
				description: _('Windows domain'),
				values: vals['windows/domain']
			}, {
				variables: ['root_password'],
				description: _('New root password'),
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
			if (values['server/role'] == 'domaincontroller_master' ) {
				if (values.hostname.toLowerCase() == values['windows/domain'].toLowerCase()) {
					dialog.alert(_('Hostname and windows domain may not be equal.'));
					return false;
				}
			}
			var warnings = [];
			if (values.hostname.length > 13) {
				warnings.push(_('If Samba is used on this system, the length of the hostname may be at most 13 characters.'));
			}
			if (!values.root_password) {
				var widget = this._form.getWidget('root_password');
				if (!widget.required) {
					warnings.push(_('Root password empty. Continue?'));
				} // else it is invalid and will be caught in save()
			}
			if (warnings.length) {
				return dialog.confirm(warnings.join('<br />'),
					[{
						label: _('Cancel'),
						'default': true,
						name: 'cancel'
					}, {
						label: _('Continue'),
						name: 'continue'
					}]
				).then(function(response) {
					return 'continue' == response;
				});
			}
			return true;
		}

	});
});
