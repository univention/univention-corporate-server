/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/aspect",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/TextArea",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/widgets/ContainerWidget",
	"umc/widgets/SuggestionBox",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/MemoryTextBox",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, aspect, Memory, Observable, tools, TitlePane, TextArea, TextBox, ComboBox, CheckBox, HiddenInput, Wizard, ContainerWidget, SuggestionBox, DriveGrid, MemoryTextBox, types, _) {

	return declare("umc.modules.uvmm.DomainWizard", [ Wizard ], {
		_profile: null,
		nodeURI: null,

		_driveStore: null,
		_driveGrid: null,
		_driveContainer: null,

		autoValidate: false,  // TODO: in the future we can activate this, when umc.widgets.Wizard/Form focuses the first invalid widget

		_loadValuesOfProfile: function() {
			// query the profile settings
			var wd = this.getWidget('profile');
			this._profile = wd.store.getValue(wd.item, "data");

			// pre-set the form fields
			this.getWidget('name').set('value', this._profile.name_prefix || '');
			this.getWidget('name').set('pattern', this._profile.name_prefix ? '^(?!' + this._profile.name_prefix + '$)[^./][^/]*$' : '.*');
			this.getWidget('maxMem').set('value', types.parseCapacity(this._profile.ram || '4 MiB'));
			this.getWidget('vcpus').set('value', this._profile.cpus);
			this.getWidget('vnc').set('value', this._profile.vnc);
			this.getWidget('cpu_model').set('value', this._profile.cpu_model);

			// update page header
			this._pages.general.set('headerText', _('Create a virtual machine (profile: %s)', this._profile.name));
		},

		_loadNodeValues: function() {
			this.standbyDuring(tools.umcpCommand('uvmm/node/query', {
				nodePattern: this.nodeURI
			}).then(lang.hitch(this, function(data) {
				if (data.result.length) {
					var node = data.result[0];

					var wm = this.getWidget('general', 'maxMem');
					wm.set('constraints', lang.mixin({}, wm.get('constraints'), {max: node.memPhysical}));
					wm.set('softMax', node.memPhysical - node.memUsed);

					types.setCPUs(node.cpus, this.getWidget('general', 'vcpus'));
				}
			})));
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// grid for the drives
			this._driveStore = new Observable(new Memory({
				idProperty: '$id$'
			}));
			this._driveGrid = new DriveGrid({
				moduleStore: this._driveStore
			});

			// wrap grid in a titlepane
			var titlePane = new TitlePane({
				title: _('Drives')
			});
			titlePane.addChild(this._driveGrid);

			// and the titlepane into a container
			this._driveContainer = new ContainerWidget({
				region: 'main'
			});
			this._driveContainer.addChild(titlePane);

			// mixin the page structure
			lang.mixin(this, {
				pages: [{
					name: 'general',
					headerText: _('Create a virtual machine'),
					helpText: _('The following settings were read from the selected profile and can be modified now.'),
					widgets: [{
						name: 'profile',
						type: ComboBox,
						label: _('Profile'),
						dynamicOptions: {nodeURI: this.nodeURI},
						dynamicValues: types.getProfiles,
						onChange: lang.hitch(this, '_loadValuesOfProfile')
					}, {
						name: 'name',
						type: TextBox,
						required: true,
						invalidMessage: _( 'A name for the virtual machine is required and should not be the same as the given name prefix' ),
						label: _('Name')
					}, {
						name: 'description',
						type: TextArea,
						cols: 120,
						rows: 5,
						label: _('Description')
					}, {
						name: 'maxMem',
						type: MemoryTextBox,
						required: true,
						softMax: 4*1024*1024*1024*1024,
						softMaxMessage: _('<b>Warning:</b> Memory size exceeds currently available RAM on node. Starting the VM may degrade the performance of the host and all other VMs.'),
						label: _('Memory (default unit MB)')
					}, {
						name: 'vcpus',
						type: ComboBox,
						label: _('Number of CPUs')
					}, {
						name: 'cpu_model',
						type: SuggestionBox,
						label: _('CPU model'),
						staticValues: types.cpuModels
					}, {
						name: 'autostart',
						type: CheckBox,
						label: _('Always start VM with host')
					}, {
						name: 'vnc',
						type: CheckBox,
						label: _('Direct access (VNC)')
					}]
				}, {
					name: 'drives',
					headerText: _('Add drive'),
					helpText: _('To finalize the creation of the virtual machine, please add one or more drives by clicking on "Add drive".')
				}],
				headerButtons: [{
					iconClass: 'umcCloseIconWhite',
					name: 'close',
					label: _('Back to overview'),
					callback: lang.hitch(this, 'onCancel')
				}]
			});

			this._loadNodeValues();
		},

		buildRendering: function() {
			this.inherited(arguments);

			// add the drive grid to the last page
			this._pages.drives.addChild(this._driveContainer);

			// connect to the onShow method of the drives page to adjust the size of the grid
			this.own(aspect.after(this._pages.drives, '_onShow', lang.hitch(this, function() {
				this._driveGrid.resize();
			})));
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			return array.filter(buttons, function(button) {
				if (button.name === 'cancel') {
					return false;
				}
				return true;
			});
		},

		next: function(pageName) {
			var nextName = this.inherited(arguments);
			if (pageName === 'general') {
				// update the domain info for the drive grid
				array.forEach(this.getPage(pageName)._form.getInvalidWidgets(), lang.hitch(this, function(widgetName) {  // TODO: remove when this.autoValidate
					this.getWidget(pageName, widgetName).focus();
					nextName = pageName;
					return false;
				}));

				if ( null !== nextName ) {
					this._driveGrid.domain = this.getValues();
					this._driveGrid.domain.profileData = this._profile;
				}
			}

			return nextName;
		},

		getValues: function() {
			var values = this._pages.general._form.get('value');
			values.nodeURI = this.nodeURI;
			values.hyperv = true;
			values.vnc_remote = true;
			values.disks = this._driveStore.data;

			// add standard interface
			values.interfaces = [{
				model: this._profile.pvinterface ? 'virtio' : 'rtl8139',
				source: this._profile.interface
			}];
			return values;
		}
	});
});
