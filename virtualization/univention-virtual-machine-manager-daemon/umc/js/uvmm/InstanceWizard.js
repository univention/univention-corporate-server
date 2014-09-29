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
/*global define*/

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
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Memory, Observable, MappedTextBox, tools, dialog, TitlePane, TextArea, TextBox, Text, ComboBox, CheckBox, HiddenInput, Wizard, Form, ContainerWidget, DriveGrid, types, _) {

	return declare("umc.modules.uvmm.InstanceWizard", [ Wizard ], {
		autoValidate: true,

		_size_id: null,
		_get_size_id: function(newVal) {
			var value = array.filter(this._size_id, function(item) {
				return item.id == newVal;
			});
			if (!value.length) {
				return null;
			}
			return value[0];
		},
		_update_size_info_text: function(newVal) {
			var widget = this.getWidget('details', 'parameter').getWidget('size_info_text');
			var size = this._get_size_id(newVal);
			if (size) {
				var text = '';
				if (size.vcpus !== null) {
					text += _('Number of CPUs') + ': ' + size.vcpus + ', ';
				}
				text += _('Memory') + ': ' + size.ram + ' MB, ';
				text += _('Hard drive') + ': ' + size.disk + ' GB ';
				widget.set('content', '<p>' + text + '</p>');
			}
		},

		_getWidgets: function(cloudtype, cloud) {
			if (cloudtype == 'OpenStack') {
				return [{
					name: 'parameter',
					type: Form,
					label: '&nbsp;',
					layout: [
						'keyname',
						'image_id',
						['size_id', 'size_info_text'],
						'security_group_ids'
					],
					widgets: [{
						name: 'keyname',
						type: ComboBox,
						label: _('Select a key pair'),
						dynamicOptions: {conn_name: cloud},
						dynamicValues: types.getCloudListKeypair,
						required: true
					}, {
						name: 'image_id',
						type: ComboBox,
						label: _('Choose an Image'),
						dynamicOptions: {conn_name: cloud},
						dynamicValues: lang.hitch(this, function(options) {
							return this.standbyDuring(types.getCloudListImage(options));
						}),
						required: true
					}, {
						name: 'size_id',
						type: ComboBox,
						label: _('Choose an Instance Size'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: cloud},
						dynamicValues: types.getCloudListSize,
						required: true,
						onChange: lang.hitch(this, function(newVal) {
							this._update_size_info_text(newVal);
						})
					}, {
						type: Text,
						name: 'size_info_text',
						content: '',
						label: '&nbsp;'
					}, {
						name: 'security_group_ids',
						type: ComboBox,
						label: _('Configure Security Group'),
						dynamicOptions: {conn_name: cloud},
						dynamicValues: types.getCloudListSecgroup,
						required: true
					}]
				}];
			}
			if (cloudtype == 'EC2') {
				var owner_id = 223093067001; // univention images
				return [{
					name: 'parameter',
					type: Form,
					label: '&nbsp;',
					layout: [
						'keyname',
						['image_id', 'image_univention'],
						['size_id', 'size_info_text'],
						'security_group_ids'
					],
					widgets: [{
						name: 'keyname',
						type: ComboBox,
						label: _('Select a key pair'),
						dynamicOptions: {conn_name: cloud},
						dynamicValues: types.getCloudListKeypair,
						required: true
					}, {
						name: 'size_id',
						type: ComboBox,
						label: _('Choose an Instance Size'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: cloud},
						dynamicValues: types.getCloudListSize,
						required: true,
						onChange: lang.hitch(this, function(newVal) {
							this._update_size_info_text(newVal);
						})
					}, {
						type: Text,
						name: 'size_info_text',
						content: '',
						label: '&nbsp;'
					}, {
						name: 'image_id',
						type: ComboBox,
						label: _('Choose AMI'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: cloud, pattern: owner_id},
						dynamicValues: lang.hitch(this, function(options) {
							return this.standbyDuring(types.getCloudListImage(options));
						}),
						required: true
					}, {
						name: 'image_univention',
						type: CheckBox,
						value: true,
						label: _('Only show Univention images'),
						description: _('Show only images which are provided by Univention.'),
						onChange: lang.hitch(this, function(newVal) {
							var widget = this.getWidget('details', 'parameter').getWidget('image_id');
							var options = widget.get('dynamicOptions');
							options.pattern = newVal ? owner_id : '';
							widget.set('dynamicOptions', options);
						})
					}, {
						name: 'security_group_ids',
						type: ComboBox,
						label: _('Configure Security Group'),
						dynamicOptions: {conn_name: cloud},
						dynamicValues: types.getCloudListSecgroup,
						required: true
					}]
				}];
			}
			return [{}];
		},

		constructor: function(props, cloudtype, cloud) {
			// mixin the page structure
			lang.mixin(this, {
				pages: [{
					name: 'general',
					headerText: _('Create a new virtual machine instance.'),
					helpText: _('Please specify name for the instance:'),
					widgets: [{
						name: 'cloudtype',
						type: HiddenInput,
						value: cloudtype
					}, {
						name: 'cloud',
						type: HiddenInput,
						value: cloud
					}, {
						name: 'name',
						type: TextBox,
						label: _('Instance Name'),
						required: true
					}]
				}, {
					name: 'details',
					headerText: _('Create a new virtual machine instance.'),
					helpText: _('Please enter the corresponding details for virtual machine instance:'),
					widgets: this._getWidgets(cloudtype, cloud)
				}]
			});
		},

		buildRendering: function() {
			this.inherited(arguments);
			// store umcp response of "size_id" for updating "size_info_text"
			var widget = this.getWidget('details', 'parameter').getWidget('size_id');
			widget.on('dynamicValuesLoaded', lang.hitch(this, function(value) {
				this._size_id = value;
				this._update_size_info_text(value[0].id);
			}));
		},

		_finish: function(pageName) {
			this.inherited(arguments);
		},
		
		onFinished: function() {
			// event stub
		}
	});
});
