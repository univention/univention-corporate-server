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
	"umc/widgets/PasswordInputBox",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Memory, Observable, MappedTextBox, tools, dialog, TitlePane, TextArea, TextBox, PasswordInputBox, Text, ComboBox, CheckBox, HiddenInput, Wizard, Form, ContainerWidget, DriveGrid, types, _) {

	return declare("umc.modules.uvmm.CloudConnectionWizard", [ Wizard ], {
		autoValidate: true,

		_invalidUrlMessage: _('The url is invalid!<br/>Expected format is: <i>http(s)://</i>'),
		_validateUrl: function(url) {
			url = url || '';
			var _regUrl = /^(http|https)+:\/\//;
			var isUrl = _regUrl.test(url);
			var acceptEmtpy = !url && !this.required;
			return acceptEmtpy || isUrl;
		},

		_getWidgets: function(cloudtype) {
			if (cloudtype == 'OpenStack') {
				return [{
					name: 'parameter',
					type: Form,
					label: '&nbsp;',
					layout: [
						'username',
						'auth_version',
						[ 'password', 'auth_token' ],
						'auth_url',
						'tenant',
						'service_region',
						'service_type',
						'service_name',
						'base_url',
					],
					widgets: 
				[{
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
						var widget = this.getWidget('credentials', 'parameter').getWidget('password');
						widget.set('disabled', value.indexOf('2.0_password') < 0);
						var widget = this.getWidget('credentials', 'parameter').getWidget('auth_token');
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
					name: 'auth_url',
					type: TextBox,
					label: 'auth_url',
					required: true,
					validator: this._validateUrl,
					invalidMessage: this._invalidUrlMessage,
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
				}, {
					name: 'base_url',
					type: TextBox,
					label: 'base_url',
					required: false,
					validator: this._validateUrl,
					invalidMessage: this._invalidUrlMessage,
				}]
				}];
			};
			if (cloudtype == 'EC2') {
				return [{
					name: 'parameter',
					type: Form,
					label: '&nbsp;',
					layout: [
						'region',
						'access_id',
						'password',
						['host', 'port'],
						'secure',
					],
					widgets: 
				[{
					name: 'access_id',
					type: TextBox,
					label: 'Access Key ID',
					required: true
				}, {
					name: 'password',
					type: PasswordInputBox,
					label: 'Secret Access Key',
					required: true
				}, {
					name: 'region',
					type: ComboBox,
					staticValues: [
						{ id: 'EC2_EU_WEST', label: 'EU (Ireland)' },
						{ id: 'EC2_US_EAST', label: 'US East (N. Virginia)' },
						{ id: 'EC2_US_WEST', label: 'US West (N. California)' },
						{ id: 'EC2_US_WEST_OREGON', label: 'US West (Oregon)' },
						{ id: 'EC2_AP_SOUTHEAST', label: 'Asia Pacific (Sydney)' },
						{ id: 'EC2_AP_NORTHEAST', label: 'Asia Pacific (Tokyo)' },
						{ id: 'EC2_AP_SOUTHEAST2', label: 'Asia Pacific (Singapore)' },
						{ id: 'EC2_SA_EAST', label: 'South America (São Paulo)' },
					],
					label: 'EC2 Region',
					required: true
				}, {
					name: 'host',
					type: TextBox,
					label: 'host',
					required: false
				}, {
					name: 'port',
					type: TextBox,
					label: 'port',
					required: false
				}, {
					name: 'secure',
					type: CheckBox,
					label: 'secure',
					value: false,
					required: false
				}
				]}]};
			return [{}];
		},

		constructor: function(props, cloudtype) {
			// mixin the page structure
			lang.mixin(this, {
				pages: [{
					name: 'general',
					headerText: _('Register a new cloud connection.'),
					helpText: _('Please specify name for the cloud connection:'),
					widgets: [{
						name: 'cloudtype',
						type: HiddenInput,
						value: cloudtype
					}, {
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
