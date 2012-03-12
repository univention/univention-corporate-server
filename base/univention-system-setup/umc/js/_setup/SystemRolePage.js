/*
 * Copyright 2012 Univention GmbH
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

dojo.provide("umc.modules._setup.SystemRolePage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.SystemRolePage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	umcpCommand: umc.tools.umcpCommand,

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// original values
	_orgValues: {},

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('System role');
		this.headerText = this._('System role');
	},

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'ComboBox',
			name: 'server/role',
			label: this._('Currently selected system role'),
			staticValues: [
				{ id: 'domaincontroller_master', label: this._('Domain controller master') },
				{ id: 'domaincontroller_backup', label: this._('Domain controller backup') },
				{ id: 'domaincontroller_slave', label: this._('Domain controller slave') },
				{ id: 'memberserver', label: this._('Member server') },
				{ id: 'basesystem', label: this._('Base system') }
 			],
 			onChange: dojo.hitch(this, function(val) {   // notify setup.js if value of ComboBox changed 
				this.switchDescription();
				this.onValuesChanged( {'server/role': val } );
			})
		}, {
			type: 'Text',
			label: '',
			name: 'text_domaincontroller_master',
			content: this._('<h2>Master domain controller master</h2>A system with the master domain controller role (DC master for short) is the primary domain controller of a UCS domain and is always installed as the first system. The domain data (such as users, groups, printers) and the SSL security certificates are saved on the DC master. 
Copies of these data are automatically transferred to all servers with the backup domain controller role.')
		}, {
			type: 'Text',
			label: '',
			name: 'text_domaincontroller_backup',
			content: this._('<h2>Backup domain controller/h2>All the domain data and SSL security certificates are saved as read-only copies on servers with the backup domain controller role (backup DC for short). The backup domain controller is the fallback system for the master DC. If the latter should fail, a backup DC can take over the role of the DC master permanently.')
		}, {
			type: 'Text',
			label: '',
			name: 'text_domaincontroller_slave',
			content: this._('<h2>Slave domain controller</h2>All the domain data are saved as read-only copies on servers with the slave domain controller role (slave DC for short). In contrast to the backup domain controller, however, not all security certificates are synchronised. As access to the services running on a slave domain controller are performed against the local LDAP server, slave DC systems are ideal for site servers and the distribution of load-intensive services. A slave DC system cannot be promoted to a master DC.')
		}, {
			type: 'Text',
			label: '',
			name: 'text_memberserver',
			content: this._('<h2>Member server</h2>Member servers are server systems without a local LDAP server. Access to domain data here is performed via other servers in the domain.')
		}, {
			type: 'Text',
			label: '',
			name: 'text_basesystem',
			content: this._('<h2>Base system</h2>A base system is an autonomous system which is not a member of the domain.A base system is thus suitable for services which are operated outside of the trust context of the domain, such as a web server or a firewall.')
		}];

		var layout = [{
			label: this._('Configuration of the UCS system role'),
			layout: [	'server/role', 
						'text_domaincontroller_master', 
						'text_domaincontroller_backup', 
						'text_domaincontroller_slave', 
						'text_memberserver', 
						'text_basesystem' ]
		}];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			onSubmit: dojo.hitch(this, 'onSave'),
			scrollable: true
		});

		// update visibility of description text before adding form otherwise all descriptions will be visible
		// for a short amount of time.
		this.switchDescription();
		this.addChild(this._form);
	},

	switchDescription: function() {
		if (this._form) {
			dojo.forEach(this._form.layout[0].layout, dojo.hitch(this, function (key) {
				var current = 'text_' + this._form.getWidget('server/role').get('value');
				if (key[0].match('^text_') == 'text_') {
					this._form.getWidget(key[0]).set('visible', (key[0] == current));
				}
			}));
		}
	},

	setValues: function(_vals) {
		var vals = dojo.mixin({}, _vals);

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
			description: this._('System role'),
			values: vals['server/role']
		}];
	},

	onSave: function() {
		// event stub
	}
});



