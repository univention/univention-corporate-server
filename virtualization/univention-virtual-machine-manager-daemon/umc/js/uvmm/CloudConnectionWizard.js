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
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/form/MappedTextBox",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/TitlePane",
	"umc/widgets/TextArea",
	"umc/widgets/TextBox",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/widgets/ContainerWidget",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Memory, Observable, MappedTextBox, tools, dialog, TitlePane, TextArea, TextBox, Text, ComboBox, CheckBox, HiddenInput, Wizard, ContainerWidget, DriveGrid, types, _) {

	return declare("umc.modules.uvmm.CloudConnectionWizard", [ Wizard ], {
		autoValidate: true,

		_getWidgets: function(cloudtype) {
			if (cloudtype == 'OpenStack') {
				return [{
					name: 'username',
					type: TextBox,
					label: 'username',
					required: true
				}, {
					name: 'auth_version',
					type: ComboBox,
					label: 'auth_version',
					staticValues: [
						{ id: '2.0_password', label: '2.0_password' },
						{ id: '2.0_apikey', label: '2.0_apikey' },
					],
					onChange: lang.hitch(this, function(value){
						var widget = this.getWidget('credentials', 'password');
						widget.set('disabled', value.indexOf('2.0_password') < 0);
						var widget = this.getWidget('credentials', 'auth_token');
						widget.set('disabled', value.indexOf('2.0_apikey') < 0);
					}),
					required: true
				}, {
					name: 'password',
					type: TextBox,
					label: 'password',
					depends: 'auth_version',
					required: true
				}, {
					name: 'auth_token',
					type: TextBox,
					label: 'auth_token',
					depends: 'auth_version',
					required: true
				}, {
					name: 'url',
					type: TextBox,
					label: 'url',
					required: true
				}, {
					name: 'tenant',
					type: TextBox,
					label: 'tenant',
					required: false
				}, {
					name: 'service_region',
					type: TextBox,
					label: 'service_region',
					required: false
				}, {
					name: 'service_type',
					type: TextBox,
					label: 'service_type',
					value: 'compute',
					required: false
				}, {
					name: 'service_name',
					type: TextBox,
					label: 'service_name',
					value: 'nova',
					required: false
				}]
			}
			return [{}]
		},

		constructor: function(props, cloudtype) {
			// mixin the page structure
			lang.mixin(this, {
				pages: [{
					name: 'general',
					headerText: _('Register a new cloud connection.'),
					helpText: _('Please specify name for the cloud connection:'),
					widgets: [{
						name: 'name',
						type: TextBox,
						label: _('Name'),
						required: true
					}]
				}, {
					name: 'credentials',
					headerText: _('Register a new cloud connection.'),
					helpText: _('Please enter the corresponding credentials for the cloud connection:'),
					widgets: this._getWidgets(cloudtype)
				}]
			});
		},

		_finish: function(pageName) {
			this.inherited(arguments);
		},
		
		onFinished: function() {
			// event stub
		}
	});
});
