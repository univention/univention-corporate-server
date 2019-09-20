/*
 * Copyright 2014-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/event",
	"dojo/on",
	"dojo/keys",
	"dijit/Tooltip",
	"umc/widgets/TextBox",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, dojoEvent, on, keys, Tooltip, TextBox, Text, ComboBox, HiddenInput, Wizard, types, _) {

	var _showTooltip = function(node, msg, evt) {
		Tooltip.show(msg, node);
		if (evt) {
			dojoEvent.stop(evt);
		}
		on.once(dojo.body(), 'click', function(evt) {
			Tooltip.hide(node);
			//dojoEvent.stop(evt); // links in tooltip should be clickable
		});
	};

	return declare("umc.modules.uvmm.InstanceWizard", [ Wizard ], {
		autoValidate: true,

		_size_id: null,

		cloud: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			// mixin the page structure
			lang.mixin(this, {
				pages: this.getPages(),
				headerButtons: [{
					name: 'close',
					iconClass: 'umcCloseIconWhite',
					label: _('Back to overview'),
					callback: lang.hitch(this, 'onCancel')
				}]
			});
		},

		_getHelpText: function() {
			if (this.cloud.type == 'OpenStack') {
				return _('Please enter the corresponding details for the virtual machine instance.');
			} else if (this.cloud.type == 'EC2') {
				return _('Please enter the corresponding details for the virtual machine instance. <a href="https://aws.amazon.com/documentation/ec2/" target=_blank>Use this link for more information about Amazon EC2</a>');
			}
		},

		_setupJavaScriptLinks: function() {
			array.forEach(this._getTooltipLinkArray(), function(iitem) {
				var iwidget = this.getWidget(iitem[0], iitem[1]);
				iwidget.set('label', lang.replace(iwidget.label, this));
			}, this);
		},

		_getTooltipLinkArray: function() {
			if (this.cloud.type == 'OpenStack') {
				return [
					['details', 'keyname'],
					['details', 'security_group_ids']
				];
			} else if (this.cloud.type == 'EC2') {
				return [
					['details', 'keyname'],
					['details', 'security_group_ids'],
					['details', 'network_id']
				];
			}
		},

		showTooltip: function(evt, type) {
			var msg = '';
			if (type == 'keyname') {
				msg = _('A key pair consists of a public and private key to log in using SSH. The configuration of all keys takes place directly via the administration page of the cloud. The key creation or upload has to be done at the provider\'s administration interface.');
			}
			else if (type == 'security_group_ids') {
				msg = _('A security group acts as a virtual firewall that controls the traffic of the instance. To enable access, correct rules have to be configured (for example, a UCS instance needs at least TCP ports 22 (ssh) and 443 (https)). The security group configuration has to be done at the provider\'s administration interface.');
			}
			else if (type == 'network_id') {
				msg = _('Select a network in which the new virtual machine instance should be launched. The network configuration has to be done at the provider\'s administration interface. <a href="https://aws.amazon.com/documentation/vpc/" target="_blank">Use this link for more information about Amazon VPC</a> and <a href="https://console.aws.amazon.com/vpc/home?#s=vpcs" target="_blank">this link to configure VPC</a>.');
			}
			if (msg) {
				_showTooltip(evt.target, msg, evt);
			}
		},

		getPages: function() {
			var content = this._getWidgets();
			var helpText = this._getHelpText();
			return [{
				name: 'details',
				headerText: _('Create a new virtual machine instance.'),
				helpText: helpText,
				widgets: content.widgets,
				buttons: content.buttons,
				layout: content.layout
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._setupJavaScriptLinks();
			// store umcp response of "size_id" for updating "size_info_text"
			var widget = this.getWidget('details', 'size_id');
			widget.on('dynamicValuesLoaded', lang.hitch(this, function(value) {
				this._size_id = value;
				this._update_size_info_text(value[0].id);
			}));
		},

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
			var widget = this.getWidget('details', 'size_info_text');
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

		_getWidgets: function() {
			if (this.cloud.type == 'OpenStack') {
				return {
					layout: [
						'name',
						'image_id',
						'size_id',
						'size_info_text',
						['keyname', 'security_group_ids']
					],
					widgets: [{
						name: 'cloudtype',
						type: HiddenInput,
						value: this.cloud.type
					}, {
						name: 'cloud',
						type: HiddenInput,
						value: this.cloud.name
					}, {
						name: 'name',
						type: TextBox,
						label: _('Instance Name'),
						required: true,
						size: 'Two'
					}, {
						name: 'keyname',
						type: ComboBox,
						label: _('Select a key pair') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'keyname\');">' +
						_('more information') +
						'</a>)',
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListKeypair,
						required: true
					}, {
						name: 'image_id',
						type: ComboBox,
						label: _('Choose an Image'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: lang.hitch(this, function(options) {
							return this.standbyDuring(types.getCloudListImage(options));
						}),
						required: true,
						size: 'Two'
					}, {
						name: 'size_id',
						type: ComboBox,
						label: _('Choose an Instance Size'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSize,
						required: true,
						size: 'Two',
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
						label: _('Configure Security Group') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'security_group_ids\');">' +
						_('more information') +
						'</a>)',
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSecgroup,
						required: true
					}]
				};
			}
			if (this.cloud.type == 'EC2') {
				return {
					layout: [
						'name',
						'image_filter',
						'image_id',
						'size_id',
						'size_info_text',
						['network_id', 'subnet_id'],
						['keyname', 'security_group_ids']
					],
					widgets: [{
						name: 'cloudtype',
						type: HiddenInput,
						value: this.cloud.type
					}, {
						name: 'cloud',
						type: HiddenInput,
						value: this.cloud.name
					}, {
						name: 'name',
						type: TextBox,
						label: _('Instance Name'),
						required: true,
						size: 'Two'
					}, {
						name: 'keyname',
						type: ComboBox,
						label: _('Select a key pair') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'keyname\');">' +
						_('more information') +
						'</a>)',
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListKeypair,
						required: true
					}, {
						name: 'size_id',
						type: ComboBox,
						label: _('Choose an Instance Size'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSize,
						required: true,
						size: 'Two',
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
						label: _('Choose an AMI'),
						sortDynamicValues: false,
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: lang.hitch(this, function(options) {
							return this.standbyDuring(types.getCloudListImage(options));
						}),
						required: true,
						size: 'Two'
					}, {
						name: 'network_id',
						type: ComboBox,
						label: _('Configure Network') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'network_id\');">' +
						_('more information') +
						'</a>)' +
						' [<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').getWidget(\'details\', \'network_id\').reloadDynamicValues();">' +
						_('Reload') +
						'</a>]',
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListNetwork,
						staticValues: [ { id: 'default', label: _('Launch into default Network') } ],
						onChange: lang.hitch(this, function(newVal) {
							var widget = this.getWidget('details', 'subnet_id');
							widget.set('disabled', newVal == 'default');
						}),
					}, {
						name: 'subnet_id',
						type: ComboBox,
						label: _('Configure Subnet'),
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSubnet,
						depends: 'network_id'
					}, {
						name: 'security_group_ids',
						type: ComboBox,
						label: _('Configure Security Group') +
						' (<a href="javascript:void(0);" onclick="require(\'dijit/registry\').byId(\'{id}\').showTooltip(event, \'security_group_ids\');">' +
						_('more information') +
						'</a>)',
						dynamicOptions: {conn_name: this.cloud.name},
						dynamicValues: types.getCloudListSecgroup,
						depends: 'network_id',
						required: true
					}]
				};
			}
			return {};
		},

		onFinished: function() {
			// event stub
		}
	});
});
