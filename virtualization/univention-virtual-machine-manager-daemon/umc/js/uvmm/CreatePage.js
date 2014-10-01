/*
 * Copyright 2014 Univention GmbH
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

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"dijit/layout/ContentPane",
	"dijit/form/RadioButton",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Page",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"umc/widgets/Form",
	"umc/widgets/ComboBox",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Tree",
	"umc/modules/uvmm/TreeModel",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, all, ContentPane, RadioButton, tools, dialog, Page, ContainerWidget, LabelPane, Form, ComboBox, Text, TextBox, HiddenInput, Tree, TreeModel, types, _) {

	return declare("umc.modules.uvmm.CreatePage", [ Page ], {
		umcpCommand: null,
		_generalForm: null,
		_tree: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				headerText: _('Create a virtual machine'),
				helpText: _('Select the cloud in which a new virtual machine instance is going to be created. Alternatively, it is possible to register a new cloud connection.'),
				headerButtons: [{
					name: 'close',
					iconClass: 'umcCloseIconWhite',
					label: _('Back to overview'),
					callback: lang.hitch(this, 'onCancel')
				}],
				footerButtons: [{
					label: _('Next'),
					defaultButton: true,
					name: 'next',
					callback: lang.hitch(this, '_finish')
				}]
			});
		},

		buildRendering: function() {
			this.inherited(arguments);
		
			this._container = new ContainerWidget({});

			/* new vm */
			this._vmRadioButton = new RadioButton({
				name: 'type',
				value: 'vm',
				checked: true
			});
			var vmLabel = new LabelPane({
				style: 'display: block;',
				content: this._vmRadioButton,
				label: _('Create a new virtual machine instance.')
			});
			this._container.addChild(vmLabel);

			/* ... for node or cloud */
			var _getNodes = lang.hitch(this, function() {
				var deferreds = [];
				deferreds.push(this.umcpCommand('uvmm/node/query'));
				deferreds.push(this.umcpCommand('uvmm/cloud/query'));

				return all(deferreds).then(lang.hitch(this, function(results) {
					var servers = [];
					array.forEach(results, function(iresult) {
						array.forEach(iresult.result, function(iserver) {
							servers.push(iserver);
						});
					});
					return servers;
				}));
			});

			this._serverComboBox = new ComboBox({
				name: 'server',
				dynamicValues: _getNodes
			});
			var serverLabel = new LabelPane({
				style: 'display: block; padding-left: 27px;',
				content: this._serverComboBox,
				label: _('Where shall the virtual machine instance be created?')
			});
			this._container.addChild(serverLabel);

			/* new cloud connection */
			this._cloudRadioButton = new RadioButton({
				name: 'type',
				value: 'cloud'
			});
			var cloudLabel = new LabelPane({
				style: 'display: block; padding-top: 20px;',
				content: this._cloudRadioButton,
				label: _('Register a new cloud connection service account.')
			});
			this._container.addChild(cloudLabel);

			/* ... for cloud type */
			var _getCloudTypes = lang.hitch(this, function() {
				var deferreds = [];
				deferreds.push(this.umcpCommand('uvmm/cloudtype/get'));

				return all(deferreds).then(lang.hitch(this, function(results) {
					var types = [];
					array.forEach(results, function(iresult) {
						array.forEach(iresult.result, function(itype) {
							types.push(itype);
						});
					});
					return types;
				}));
			});

			this._cloudTypeComboBox = new ComboBox({
				name: 'type',
				dynamicValues: _getCloudTypes
			});
			var cloudTypeLabel = new LabelPane({
				style: 'display: block; padding-left: 27px;',
				content: this._cloudTypeComboBox,
				label: _('Which cloud connection is to be created?')
			});
			this._container.addChild(cloudTypeLabel);

			this.addChild(this._container);

			array.forEach([this._vmRadioButton, this._cloudRadioButton], lang.hitch(this, function(radioButton) {
				radioButton.watch('checked', lang.hitch(this, function(attr, oldval, newval) {
					var value = radioButton.get('value');
					if (newval) {
						this.set('type', value);
					}
				}));
			}));

			tools.ucr(["server/role"]).then(lang.hitch(this, function(ucr){
				console.log(ucr["server/role"]);
				if (ucr["server/role"] != 'domaincontroller_master') {
					this._cloudRadioButton.set('checked', false);
					this._cloudRadioButton.set('visible', false);
					this._cloudTypeComboBox.set('visible', false);
					this._vmRadioButton.set('checked', true);
					this.set('type', 'vm');
				}
			}));

			this.own(this.watch('type', lang.hitch(this, function(attr, oldval, newval) {
				console.log('# watch type: ', newval);
				var isDisabled = newval == 'cloud';
				this._serverComboBox.set('disabled', isDisabled);
				var isDisabled = newval == 'vm';
				this._cloudTypeComboBox.set('disabled', isDisabled);
			})));
		},

		startup: function() {
			this.inherited(arguments);
			this.set('type', 'vm');
		},

		_getSelectedServer: function() {
			var serverID = this._serverComboBox.get('value');
			var server = array.filter(this._serverComboBox.getAllItems(), function(item) {
				return item.id == serverID;
			});
			if (!server.length) {
				return null;
			}
			return server[0];
		},

		_getSelectedCloudType: function() {
			var cloudtypeID = this._cloudTypeComboBox.get('value');
			var cloudtype = array.filter(this._cloudTypeComboBox.getAllItems(), function(item) {
				return item.id == cloudtypeID;
			});
			if (!cloudtype.length) {
				return null;
			}
			return cloudtype[0];
		},

		getValues: function() {
			// save the type that shall be created
			var values = {};
			values.type = this.type;
			var server = this._getSelectedServer();
			var cloudtype = this._getSelectedCloudType();
			if (this.type == 'vm' && server.type == 'cloud') {
				values.type = 'instance';
				values.cloud = server.id;
				values.cloudtype = server.cloudtype;
			}
			else if (this.type == 'vm' && server.type == 'node') {
				values.type = 'domain';
				values.nodeURI = server.id;
			} else if (this.type == 'cloud') {
				values.cloudtype = cloudtype.id;
			}
			return values;
		},

		_finish: function() {
			// trigger finished event
			this.onFinished(this.getValues());
		},
		
		onFinished: function() {
			// event stub
		},

		onCancel: function() {
			// event stub
		}
	});
});
