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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/MultiSelect",
	"umc/widgets/Form",
	"umc/widgets/Button",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, dialog, Page, StandbyMixin, TextBox, ComboBox, MultiInput, MultiSelect, Form, Button, _) {
	return declare("umc.modules.setup.DNSPage", [ Page, StandbyMixin ], {
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

		// dicts of the original IPv4/v6 values
		_orgValues: null,

		_noteShowed: false,

		_currentRole: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('DNS settings');
			this.headerText = _('DNS settings');
			this.helpText = _('In the <i>DNS settings</i> name servers and HTTP proxies may be specified.');
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: MultiInput,
				subtypes: [{ type: TextBox }],
				name: 'nameserver',
				label: _('Domain name server (max. 3)'),
				max: 3
			}, {
				type: MultiInput,
				subtypes: [{ type: TextBox }],
				name: 'dns/forwarder',
				label: _('External name server (max. 3)'),
				max: 3
			}, {
				type: TextBox,
				name: 'proxy/http',
				label: _('HTTP proxy')
			}];

			var layout = [{
				label: _('DNS Nameserver'),
				layout: [ 'nameserver', 'dns/forwarder']
			}, {
				label: _('Proxy Settings'),
				layout: ['proxy/http']
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			this.addChild(this._form);
		},

		setValues: function(_vals) {
			var vals = {};

			// save a copy of all original values that may be lists
			var r = /^(nameserver[1-3]|dns\/forwarder[1-3])$/;
			this._orgValues = {};
			tools.forIn(_vals, function(ikey, ival) {
				if (r.test(ikey)) {
					this._orgValues[ikey] = ival;
				}
			}, this);

			// copy values that do not change in their name
			array.forEach(['proxy/http'], function(ikey) {
				vals[ikey] = _vals[ikey];
			});

			// copy lists of nameservers/forwarders
			vals.nameserver = [];
			vals['dns/forwarder'] = [];
			tools.forIn(_vals, function(ikey) {
				array.forEach(['nameserver', 'dns/forwarder'], function(jname) {
					if (0 === ikey.indexOf(jname)) {
						vals[jname].push(_vals[ikey]);
					}
				});
			});

			// only show forwarder for master, backup, and slave
			this._currentRole = _vals['server/role'];
			var showForwarder = this._currentRole == 'domaincontroller_master' || this._currentRole == 'domaincontroller_backup' || this._currentRole == 'domaincontroller_slave';
			this._form.getWidget('dns/forwarder').set('visible', showForwarder);

			// hide domain nameserver on master when using system setup boot
			this._form.getWidget('nameserver').set('visible', ! ( this.wizard_mode && this._currentRole == 'domaincontroller_master' ) );
			// set values
			this._form.setFormValues(vals);
		},

		getValues: function() {
			var _vals = this._form.gatherFormValues();
			var vals = {};

			// copy values that do not change in their name
			array.forEach(['proxy/http'], function(ikey) {
				vals[ikey] = _vals[ikey];
			});

			// copy lists of nameservers/forwarders
			array.forEach(['nameserver', 'dns/forwarder'], function(iname) {
				array.forEach(_vals[iname], function(jval, j) {
					vals[iname + (j + 1)] = jval;
				});
			});

			return vals;
		},

		getSummary: function() {
			var vals = this._form.gatherFormValues();

			// create a verbose list of all settings
			return [{
				variables: [/nameserver.*/],
				description: _('Domain name server'),
				values: vals['nameserver'].join(', ')
			}, {
				variables: [/dns\/forwarder.*/],
				description: _('External name server'),
				values: vals['dns/forwarder'].join(', ')
			}, {
				variables: ['proxy/http'],
				description: _('HTTP proxy'),
				values: vals['proxy/http']
			}];
		},

		onSave: function() {
			// event stub
		}
	});
});
