/*
 * Copyright 2012-2014 Univention GmbH
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
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/setup"
], function(declare, lang, array, tools, Page, Form, Text, ComboBox, _) {

	return declare("umc.modules.setup.SystemRolePage", [ Page ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit UDM objects.

		umcpCommand: tools.umcpCommand,

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		// original values
		_orgValues: {},
		_oldRole: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('System role');
			this.headerText = _('System role');
			this.helpText = _('If the system is not part of a domain yet, the <i>system role</i> may be changed.');
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: ComboBox,
				name: 'server/role',
				label: _('Currently selected system role'),
				staticValues: [
					{ id: 'domaincontroller_master', label: _('Domain controller master') },
					{ id: 'domaincontroller_backup', label: _('Domain controller backup') },
					{ id: 'domaincontroller_slave', label: _('Domain controller slave') },
					{ id: 'memberserver', label: _('Member server') }
					// { id: 'basesystem', label: _('Base system') }
 				]
			}, {
				type: Text,
				label: '',
				name: 'text_domaincontroller_master',
				content: _('<h2>Domain controller master</h2>A system with the domain controller master role (DC master for short) is the primary domain controller of a UCS domain and is always installed as the first system. The domain data (such as users, groups, printers) and the SSL security certificates are saved on the DC master.  Copies of these data are automatically transferred to all servers with the DC backup role.')
			}, {
				type: Text,
				label: '',
				name: 'text_domaincontroller_backup',
				content: _('<h2>Domain controller backup</h2>All the domain data and SSL security certificates are saved as read-only copies on servers with the domain controller backup role (DC backup for short). The DC backup is the fallback system for the DC master. If the latter should fail, a DC backup can take over the role of the DC master permanently.')
			}, {
				type: Text,
				label: '',
				name: 'text_domaincontroller_slave',
				content: _('<h2>Domain controller slave</h2>All the domain data are saved as read-only copies on servers with the domain controller slave role (DC slave for short). In contrast to the DC backup, however, not all security certificates are synchronised. As access to the services running on a DC slave are performed against the local LDAP server, DC slave systems are ideal for site servers and the distribution of load-intensive services. A DC slave system cannot be promoted to a DC master.')
			}, {
				type: Text,
				label: '',
				name: 'text_memberserver',
				content: _('<h2>Member server</h2>Member servers are server systems without a local LDAP server. Access to domain data here is performed via other servers in the domain.')
			}, {
				type: Text,
				label: '',
				name: 'text_basesystem',
				content: _('<h2>Base system</h2>A base system is an autonomous system which is not a member of the domain. A base system is thus suitable for services which are operated outside of the trust context of the domain, such as a web server or a firewall.')
			}];

			var layout = [{
				label: _('Configuration of the UCS system role'),
				layout: [	'server/role',
							'text_domaincontroller_master',
							'text_domaincontroller_backup',
							'text_domaincontroller_slave',
							'text_memberserver',
							'text_basesystem' ]
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			this._form.on('submit', lang.hitch(this, 'onSave'));

			this._oldRole = this._form.getWidget('server/role').get('value');

			this.own(this._form.getWidget('server/role').watch('value', lang.hitch(this, function(name, old, val) {
				// notify setup.js if value of ComboBox changed
				// only notify if value really changed (see Bug #27240)
				if (this._oldRole != val) {
					this._oldRole = val;
					this.switchDescription();
					this.onValuesChanged( {'server/role': val } );
				}
			})));
 		
			// update visibility of description text before adding form otherwise all descriptions will be visible
			// for a short amount of time.
			this.switchDescription();
			this.addChild(this._form);
		},

		switchDescription: function() {
			if (this._form) {
				array.forEach(this._form.layout[0].layout, lang.hitch(this, function (key) {
					var current = 'text_' + this._form.getWidget('server/role').get('value');
					if (key[0].match('^text_') == 'text_') {
						this._form.getWidget(key[0]).set('visible', (key[0] == current));
					}
				}));
			}
		},

		setValues: function(_vals) {
			var vals = lang.mixin({}, _vals);

			this._form.setFormValues(vals);
		},

		getValues: function() {
			return this._form.gatherFormValues();
		},

		onValuesChanged: function(_vals) {
			// event stub
		},

		getSummary: function() {
			var vals = this.getValues();
			return [{
				variables: ['server/role'],
				description: _('System role'),
				values: vals['server/role']
			}];
		},

		onSave: function() {
			// event stub
		}
	});
});
