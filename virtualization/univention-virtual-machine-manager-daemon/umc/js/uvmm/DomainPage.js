/*
 * Copyright 2011-2015 Univention GmbH
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
/*global define, location*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/form/MappedTextBox",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TabContainer",
	"umc/widgets/TitlePane",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/TextArea",
	"umc/widgets/HiddenInput",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/CheckBox",
	"umc/widgets/PasswordBox",
	"umc/modules/uvmm/SnapshotGrid",
	"umc/modules/uvmm/InterfaceGrid",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Memory, Observable, MappedTextBox, tools, dialog, store, Page, Form, ContainerWidget, TabContainer, TitlePane, ExpandingTitlePane, StandbyMixin,
	TextBox, TextArea, HiddenInput, ComboBox, MultiInput, CheckBox, PasswordBox, SnapshotGrid, InterfaceGrid, DriveGrid, types, _) {

	return declare("umc.modules.uvmm.DomainPage", [ TabContainer, StandbyMixin ], {
		nested: true,

		_generalForm: null,
		_advancedForm: null,

		_generalPage: null,
		_advancedPage: null,
		_devicesPage: null,
		_snapshotPage: null,

		_driveStore: null,
		_driveGrid: null,
		_interfaceStore: null,
		_interfaceGrid: null,
		_snapshotStore: null,
		_snapshotGrid: null,

		_domain: null,

		addNotification: dialog.notify,

		buildRendering: function() {
			this.inherited(arguments);
			//
			// general settings page
			//

			this._generalPage = new Page({
				headerText: _('General settings'),
				title: _('General'),
				footerButtons: [{
					label: _('Back to overview'),
					name: 'cancel',
					callback: lang.hitch(this, 'onClose')
				}, {
					label: _('Save'),
					defaultButton: true,
					name: 'save',
					callback: lang.hitch(this, 'save')
				}]
			});

			this._generalForm = new Form({
				widgets: [{
					name: 'domainURI',
					type: HiddenInput
				}, {
					name: 'name',
					type: TextBox,
					label: _('Name')
				}, {
					name: 'os',
					type: TextBox,
					label: _('Operating system')
				}, {
					name: 'contact',
					type: TextBox,
					label: _('Contact'),
					onChange: lang.hitch(this, function(newVal) {
						// if the value looks like a email address, show the email button
						var r = /^.+@.+\..+$/;
						this._generalForm._buttons.email.set('visible', r.test(newVal));
					})
				}, {
					name: 'description',
					type: TextArea,
					cols: 120,
					rows: 5,
					label: _('Description')
				}],
				buttons: [{
					name: 'email',
					label: _('Send email'),
					callback: lang.hitch(this, function() {
						var val = this._generalForm.gatherFormValues();
						if (val.contact) {
							location.href = 'mailto:' + val.contact + '?subject=' + _('Virtual machine: %s', val.name);
						}
					})
				}],
				layout: [{
					label: _('Settings'),
					layout: [
						'name',
						'os',
						[ 'contact', 'email' ],
						'description'
					]
				}],
				scrollable: true
			});
			this._generalForm.on('Submit', lang.hitch(this, 'save'));
			this._generalPage.addChild(this._generalForm);
			this._generalForm._buttons.email.set('visible', false);

			//
			// advanced settings page
			//

			this._advancedPage = new Page({
				headerText: _('Advanced settings'),
				title: _('Advanced'),
				footerButtons: [{
					label: _('Back to overview'),
					name: 'cancel',
					callback: lang.hitch(this, 'onClose')
				}, {
					label: _('Save'),
					defaultButton: true,
					name: 'save',
					callback: lang.hitch(this, 'save')
				}]
			});

			this._advancedForm = new Form({
				widgets: [{
					name: 'domainURI',
					type: HiddenInput
				}, {
					name: 'arch',
					type: ComboBox,
					label: _('Architecture'),
					staticValues: types.architecture
				}, {
					name: 'vcpus',
					type: ComboBox,
					label: _('Number of CPUs'),
					depends: 'domainURI',
					dynamicValues: types.getCPUs
				}, {
					name: 'maxMem',
					type: MappedTextBox,
					required: true,
					constraints: {min: 4*1024*1024},
					format: types.prettyCapacity,
					parse: types.parseCapacity,
					validator: function(value, constraints) {
						var size = types.parseCapacity(value);
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
					label: _('Memory')
				}, {
					name: 'boot_hvm',
					type: MultiInput,
					label: _('Boot order'),
					subtypes: [ {
						type: ComboBox,
						staticValues: types.bootDevices
					} ]
				}, {
					name: 'boot_pv',
					type: ComboBox,
					label: _('Boot device')
				}, {
					name: 'os_type',
					type: HiddenInput
				}, {
					name: 'domain_type',
					type: HiddenInput
				}, {
					name: 'type',
					depends: 'domain_type',
					type: ComboBox,
					readonly: true,
					label: _('Virtualization technology'),
					dynamicValues: types.getVirtualizationTechnology
				}, {
					name: 'rtc_offset',
					type: ComboBox,
					label: _('RTC reference'),
					staticValues: types.rtcOffset
				}, {
					name: 'vnc',
					type: CheckBox,
					label: _('Direct access (VNC)')
				}, {
					name: 'vnc_remote',
					type: CheckBox,
					label: _('Globally available')
				}, {
					name: 'vnc_port',
					type: TextBox,
					disabled: true,
					visible: false,
					label: _('VNC Port')
				}, {
					name: 'vnc_password',
					type: PasswordBox,
					label: _('VNC password')
				}, {
					name: 'kblayout',
					type: ComboBox,
					label: _('Keyboard layout'),
					staticValues: types.keyboardLayout
				}],
				layout: [{
					label: _('Machine'),
					layout: [
						'arch',
						'vcpus',
						'maxMem',
						[ 'domain_type', 'os_type', 'type' ],
						'rtc_offset',
						'boot_hvm',
						'boot_pv'
					]
				}, {
					label: _('Remote access'),
					layout: [
						['vnc', 'vnc_remote'],
						'vnc_port',
						'vnc_password',
						'kblayout'
					]
				}],
				scrollable: true
			});
			this._advancedForm.on('Submit', lang.hitch(this, 'save'));
			this._advancedPage.addChild(this._advancedForm);

			//
			// devices page
			//

			this._devicesPage = new Page({
				headerText: _('Settings for devices'),
				title: _('Devices'),
				footerButtons: [{
					label: _('Back to overview'),
					name: 'cancel',
					callback: lang.hitch(this, 'onClose')
				}, {
					label: _('Save'),
					defaultButton: true,
					name: 'save',
					callback: lang.hitch(this, 'save')
				}]
			});
			var container = new ContainerWidget({
				scrollable: true
			});
			this._devicesPage.addChild(container);

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
			container.addChild(titlePane);

			// grid for the network interfaces
			this._interfaceStore = new Observable(new Memory({
				idProperty: '$id$'
			}));
			this._interfaceGrid = new InterfaceGrid({
				moduleStore: this._interfaceStore
			});

			// wrap grid in a titlepane
			titlePane = new TitlePane({
				title: _('Network interfaces')
			});
			titlePane.addChild(this._interfaceGrid);
			container.addChild(titlePane);

			// we need to call resize() manually to make sure the grids are rendered correctly
			this._devicesPage.on('Show', lang.hitch(this, function() {
				this._driveGrid.resize();
				this._interfaceGrid.resize();
			}));

			//
			// snapshot page
			//

			this._snapshotPage = new Page({
				headerText: _('Snapshots settings'),
				title: _('Snapshots'),
				footerButtons: [{
					label: _('Back to overview'),
					name: 'cancel',
					callback: lang.hitch(this, 'onClose')
				}, {
					label: _('Save'),
					defaultButton: true,
					name: 'save',
					callback: lang.hitch(this, 'save')
				}]
			});

			// grid for the snapshots
			this._snapshotStore = store('id', 'uvmm/snapshot');
			this._snapshotGrid = new SnapshotGrid({
				moduleStore: this._snapshotStore,
				onUpdateProgress: lang.hitch(this, 'onUpdateProgress')
			});
			titlePane = new ExpandingTitlePane({
				title: _('Snapshots')
			});
			titlePane.addChild(this._snapshotGrid);
			this._snapshotPage.addChild(titlePane);

			// add pages in the correct order
			this.addChild(this._generalPage);
			this.addChild(this._devicesPage);
			this.addChild(this._snapshotPage);
			this.addChild(this._advancedPage);
		},

		save: function() {
			// validate
			var valid = true;
			var widgets = lang.mixin({}, this._generalForm._widgets, this._advancedForm._widgets);
			var values = lang.clone(this._domain);
			delete values.domainURI;
			tools.forIn(widgets, function(iname, iwidget) {
				valid = valid && (false !== iwidget.isValid());
				values[iname] = iwidget.get('value');
				return valid;
			}, this);

			if (!valid) {
				dialog.alert(_('The entered data is not valid. Please correct your input.'));
				return;
			}
			// special handling for boot devices
			var paravirtual = this._domain.type == 'xen-xen';
			if ( paravirtual ) {
				var disks = [];
				array.forEach( this._domain.disks, function( disk ) {
					if ( values.boot_pv == disk.source ) {
						disks.unshift( disk );
					} else {
						disks.push( disk );
					}
				} );
				values.disks = disks;
			} else {
				values.boot = values.boot_hvm;
			}

			this.standby(true);
			tools.umcpCommand('uvmm/domain/put', {
				nodeURI: this._domain.domainURI.split('#')[0],
				domain: values
			}).then(lang.hitch(this, function() {
				this.onClose();
				this.standby(false);
			}), lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		load: function(id) {
			this._standbyWidget.opacity = 1;
			this.standby(true);
			this._standbyWidget.opacity = 0.75;

			tools.umcpCommand('uvmm/domain/get', {
				domainURI: id
			}).then(lang.hitch(this, function(data) {
				// get data blob
				this._domain = lang.getObject('result', false, data);
				this._domain.domainURI = id;
				this._domain.nodeURI = id.slice( 0, id.indexOf( '#' ) );

				if (data) {
					this._domain.domainURI = id;

					this.moduleWidget.set('titleDetail', this._domain.name);

					// clear form data
					this._generalForm.clearFormValues();
					this._advancedForm.clearFormValues();
					// set values to form
					this._generalForm.setFormValues(this._domain);

					if ( ! this._domain.available ) {
						this.addNotification( _( '<p>For fail over the virtual machine can be migrated to another physical server re-using the last known configuration and all disk images. This can result in <strong>data corruption</strong> if the images are <strong>concurrently used</strong> by multiple running machines! Therefore the failed server <strong>must be blocked from accessing the image files</strong>, for example by blocking access to the shared storage or by disconnecting the network.</p><p>When the server is restored, all its previous virtual machines will be shown again. Any duplicates have to be cleaned up manually by migrating the machines back to the server or by deleting them. Make sure that shared images are not delete.</p>' ) );
						this.hideChild( this._devicesPage );
						this.hideChild( this._snapshotPage );
						this.hideChild( this._advancedPage );
						this._generalPage._footerButtons.save.set( 'disabled', true );
						// name should not be editable
						this._generalForm._widgets.name.set( 'disabled', true );
						this.standby( false );
						return;
					} else {
						this.showChild( this._advancedPage );
						this.showChild( this._devicesPage );
						this._generalPage._footerButtons.save.set( 'disabled', false );
					}
					this._advancedForm.setFormValues(this._domain);

					// special handling for boot devices
					var paravirtual = this._domain.type == 'xen-xen';
					this._advancedForm._widgets.boot_pv.set( 'visible', paravirtual );
					this._advancedForm._widgets.boot_hvm.set( 'visible', ! paravirtual );
					if ( paravirtual ) {
						var block_devices = array.map( this._domain.disks, function( disk ) {
							return { id : disk.source, label: types.blockDevices[ disk.device ] + ': ' + disk.volumeFilename };
						} );
						block_devices.unshift( { id: '', label: '' } );
						this._advancedForm._widgets.boot_pv.set( 'staticValues', block_devices );
						this._advancedForm._widgets.boot_pv.set( 'value', block_devices[ 1 ].id );
					} else {
						this._advancedForm._widgets.boot_hvm.set( 'value', this._domain.boot );
					}
					this._advancedForm._widgets.rtc_offset.set('staticValues', types.getRtcOffset(this._domain.type, this._domain.rtc_offset));

					// we need to add pseudo ids for the network interfaces
					array.forEach(this._domain.interfaces, function(idev, i) {
						idev.$id$ = i + 1;
					});

					// we need to add pseudo ids for the network interfaces
					array.forEach(this._domain.disks, function(idrive, i) {
						idrive.$id$ = i + 1;
					});

					// update the stores
					this._snapshotGrid.set('domain', this._domain);
					this._driveGrid.set('domain', this._domain);
					this._interfaceGrid.set('domain', this._domain);
					this._interfaceStore.setData(this._domain.interfaces);
					this._driveStore.setData(this._domain.disks);

					// Only qemu can do snapshots
					if (types.getNodeType(this._domain.domainURI) == 'qemu') {
						this.showChild( this._snapshotPage );
					} else {
						this.hideChild( this._snapshotPage );
					}

					// set visibility of the VNC-Port
					this._advancedForm._widgets.vnc_port.set('visible', Boolean(this._advancedForm._widgets.vnc_port.get('value')));

					// deactivate most input field when domain is running
					var domainActive = types.isActive(this._domain);
					if (domainActive) {
						this.addNotification( _( 'While the virtual machine is running most of the settings can not be changed.' ) );
					}
					// name should not be editable
					this._generalForm._widgets.name.set( 'disabled', true );
					// currently this does not work for xen also (Bug #24829) -> otherwise the following block just deactivates the name for KVM
					// if ( types.getNodeType( this._domain.domainURI ) == 'qemu' ) {
					// 	this._generalForm._widgets.name.set( 'disabled', true );
					// } else {
					// 	this._generalForm._widgets.name.set( 'disabled', disabled );
					// }

					// hide architecture for xen domains
					if ( types.getNodeType( this._domain.domainURI ) == 'qemu' ) {
						this._advancedForm._widgets.arch.set( 'visible', true );
						this._advancedForm._widgets.arch.set( 'disabled', domainActive );
					} else {
						this._advancedForm._widgets.arch.set( 'visible', false );
					}
					this._driveGrid.set( 'domainActive', domainActive );
					this._interfaceGrid.set( 'disabled', domainActive );
					tools.forIn( this._advancedForm._widgets, lang.hitch( this, function( iid, iwidget ) {
						if ( iwidget.readonly ) {
							iwidget.set( 'disabled', true );
						} else {
							iwidget.set( 'disabled', domainActive );
						}
					} ) );
					this.selectChild( this._generalPage, true);

					// force a refresh of the grids
					this._interfaceGrid.filter();
					this._driveGrid.filter();
					this._snapshotGrid.filter();
				}
				this.standby(false);
			}), lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		onClose: function() {
			// event stub
		},

		onUpdateProgress: function(i, n) {
			// event stub
		}
	});
});
