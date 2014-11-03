/*
 * Copyright 2011-2014 Univention GmbH
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
	"dojo/aspect",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/form/MappedTextBox",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/TextArea",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/widgets/ContainerWidget",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, aspect, Memory, Observable, MappedTextBox, tools, TitlePane, TextArea, TextBox, ComboBox, CheckBox, HiddenInput, Wizard, ContainerWidget, DriveGrid, types, _) {

	return declare("umc.modules.uvmm.DomainWizard", [ Wizard ], {
		_profile: null,
		nodeURI: null,

		_driveStore: null,
		_driveGrid: null,
		_driveContainer: null,
		
		_loadValuesOfProfile: function() {
			// put limit on memory
			try {
				var nodeURI = this.getWidget('nodeURI');
				var maxMem = nodeURI.store.getValue(nodeURI.item, 'memAvailable');
				this.getWidget('maxMem').get('constraints').max = maxMem;
			} catch (err) { }

			// query the profile settings
			this.standby(true);
			var profileDN = this.getWidget('profileDN').get('value');
			tools.umcpCommand('uvmm/profile/get', {
				profileDN: profileDN
			}).then(lang.hitch(this, function(data) {
				// we got the profile...
				this._profile = data.result;
				this._profile.profileDN = profileDN;

				// pre-set the form fields
				var nodeURI = this.getWidget('nodeURI').get('value');
				this.getWidget('general', 'nodeURI').set('value', nodeURI);
				this.getWidget('profile').set('value', profileDN);
				this.getWidget('name').set('value', this._profile.name_prefix || '');
				this.getWidget('name').set('pattern', this._profile.name_prefix ? '^(?!' + this._profile.name_prefix + '$)[^./][^/]*$' : '.*');
				this.getWidget('maxMem').set('value', types.parseCapacity(this._profile.ram || '4 MiB'));
				this.getWidget('vcpus').set('value', this._profile.cpus);
				this.getWidget('vnc').set('value', this._profile.vnc);

				// update page header
				this._pages.general.set('headerText', _('Create a virtual machine (profile: %s)', this._profile.name));

				this.standby(false);
			}), lang.hitch(this, function() {
				// fallback... switch off the standby animation
				this.standby(false);
			}));
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			var nodeURI = this.nodeURI;
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
			this._driveContainer  = new ContainerWidget({
				region: 'main'
			});
			this._driveContainer.addChild(titlePane);

			// mixin the page structure
			lang.mixin(this, {
				pages: [{
/*					name: 'profile',
					headerText: _('Create a virtual machine'),
					helpText: _('By selecting a profile for the virtual machine most of the settings will be set to default values. In the following steps some of these values might be modified. After the creation of the virtual machine all parameters, extended settings und attached drives can be adjusted. It should be ensured that the profile is for the correct architecture as this option can not be changed afterwards.'),
					widgets: [{
						name: 'nodeURI',
						type: ComboBox,
						label: _('Physical server'),
						dynamicValues: types.getNodes,
						value: nodeURI
					}, {
						name: 'profileDN',
						type: ComboBox,
						label: _('Profile'),
						depends: 'nodeURI',
						dynamicValues: types.getProfiles
					}]
				}, {*/
					name: 'general',
					headerText: _('Create a virtual machine'),
					helpText: _('The following settings were read from the selected profile and can be modified now.'),
					widgets: [{
						name: 'nodeURI',
						type: HiddenInput,
						value: nodeURI
					}, {
						name: 'profile',
						type: HiddenInput
					}, {
						name: 'profileDN',
						type: ComboBox,
						label: _('Profile'),
						dynamicOptions: {nodeURI: nodeURI},
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
						type: MappedTextBox,
						required: true,
						constraints: {min: 4*1024*1024},
						format: types.prettyCapacity,
						parse: function(value) {
							return types.parseCapacity(value, 'M');
						},
						validator: function(value, constraints) {
							var size = types.parseCapacity(value, 'M');
							if (size === null) {
								return false;
							}
							if (constraints.min && size < constraints.min) {
								return false;
							}
							if (constraints.max && size > constraints.max) {
								return false;
							}
							return true;
						},
						invalidMessage: _('The memory size is invalid (e.g. 3GB or 1024 MB), minimum 4 MB'),
						label: _('Memory (default unit MB)')
					}, {
						name: 'vcpus',
						type: ComboBox,
						label: _('Number of CPUs'),
						dynamicOptions: {nodeURI: nodeURI},
						dynamicValues: types.getCPUs
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
				if (button.name == 'cancel') {
					return false;
				}
				return true;
			});
		},

		next: function(pageName) {
			var nextName = this.inherited(arguments);
			/*if (pageName == 'profile') {
				// put limit on memory
				try {
					var nodeURI = this.getWidget('nodeURI');
					var maxMem = nodeURI.store.getValue(nodeURI.item, 'memAvailable');
					this.getWidget('maxMem').get('constraints').max = maxMem;
				} catch (err) { }

				// query the profile settings
				this.standby(true);
				var profileDN = this.getWidget('profileDN').get('value');
				tools.umcpCommand('uvmm/profile/get', {
					profileDN: profileDN
				}).then(lang.hitch(this, function(data) {
					// we got the profile...
					this._profile = data.result;
					this._profile.profileDN = profileDN;

					// pre-set the form fields
					var nodeURI = this.getWidget('nodeURI').get('value');
					this.getWidget('general', 'nodeURI').set('value', nodeURI);
					this.getWidget('profile').set('value', profileDN);
					this.getWidget('name').set('value', this._profile.name_prefix || '');
					this.getWidget('name').set('pattern', this._profile.name_prefix ? '^(?!' + this._profile.name_prefix + '$)[^./][^/]*$' : '.*');
					this.getWidget('maxMem').set('value', types.parseCapacity(this._profile.ram || '4 MiB'));
					this.getWidget('vcpus').set('value', this._profile.cpus);
					this.getWidget('vnc').set('value', this._profile.vnc);

					// update page header
					this._pages.general.set('headerText', _('Create a virtual machine (profile: %s)', this._profile.name));

					this.standby(false);
				}), lang.hitch(this, function() {
					// fallback... switch off the standby animation
					this.standby(false);
				}));
			}
			else*/ if (pageName == 'general') {
				// update the domain info for the drive grid
				array.forEach( [ 'name', 'maxMem' ], lang.hitch( this, function( widgetName ) {
					if ( ! this.getWidget( widgetName ).isValid() ) {
						this.getWidget( widgetName ).focus();
						nextName = null;
						return false;
					}
				} ) );

				if ( null !== nextName ) {
					this._driveGrid.domain = this.getValues();
					this._driveGrid.domain.profileData = this._profile;
				}
			}

			return nextName;
		},

		getValues: function() {
			var values = this._pages.general._form.gatherFormValues();
			values.nodeURI = this.getWidget('nodeURI').get('value');
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
