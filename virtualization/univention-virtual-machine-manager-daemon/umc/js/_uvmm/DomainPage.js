/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc location */

dojo.provide("umc.modules._uvmm.DomainPage");

dojo.require("dojox.string.sprintf");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.store");
dojo.require("umc.dialog");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets.TitlePane");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.modules._uvmm.types");
dojo.require("umc.modules._uvmm.SnapshotGrid");
dojo.require("umc.modules._uvmm.InterfaceGrid");
dojo.require("umc.modules._uvmm.DriveGrid");

dojo.declare("umc.modules._uvmm.DomainPage", [ umc.widgets.TabContainer, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	nested: true,

	i18nClass: 'umc.modules.uvmm',

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
	_loadedValues: null,

	disabled: false,

	buildRendering: function() {
		this.inherited(arguments);
		var types = umc.modules._uvmm.types;

		//
		// general settings page
		//

		this._generalPage = new umc.widgets.Page({
			headerText: this._('General settings'),
			title: this._('General'),
			footerButtons: [{
				label: this._('Back to overview'),
				name: 'cancel',
				callback: dojo.hitch(this, 'confirmClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});

		this._generalForm = new umc.widgets.Form({
			widgets: [{
				name: 'domainURI',
				type: 'HiddenInput'
			}, {
				name: 'name',
				type: 'TextBox',
				label: this._('Name')
			}, {
				name: 'os',
				type: 'TextBox',
				label: this._('Operating system')
			}, {
				name: 'contact',
				type: 'TextBox',
				label: this._('Contact'),
				onChange: dojo.hitch(this, function(newVal) {
					// if the value looks like a email address, show the email button
					var r = /^.+@.+\..+$/;
					this._generalForm._buttons.email.set('visible', r.test(newVal));
				})
			}, {
				name: 'description',
				type: 'TextBox',
				label: this._('Description')
			}],
			buttons: [{
				name: 'email',
				label: this._('Send email'),
				callback: dojo.hitch(this, function() {
					var val = this._generalForm.gatherFormValues();
					if (val.contact) {
						location.href = 'mailto:' + val.contact + '?subject=' + this._('Virtual instance: %s', val.name);
					}
				})
			}],
			layout: [{
				label: this._('Settings'),
				layout: [
					'name',
					'os',
					[ 'contact', 'email' ],
					'description'
				]
			}],
			scrollable: true
		});
		this.connect(this._generalForm, 'onSubmit', 'save');
		this._generalPage.addChild(this._generalForm);
		this._generalForm._buttons.email.set('visible', false);

		//
		// advanced settings page
		//

		this._advancedPage = new umc.widgets.Page({
			headerText: this._('Advanced settings'),
			title: this._('Advanced'),
			footerButtons: [{
				label: this._('Back to overview'),
				name: 'cancel',
				callback: dojo.hitch(this, 'confirmClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});

		this._advancedForm = new umc.widgets.Form({
			widgets: [{
				name: 'domainURI',
				type: 'HiddenInput'
			}, {
				name: 'arch',
				type: 'ComboBox',
				label: this._('Architecture'),
				staticValues: types.architecture
			}, {
				name: 'vcpus',
				type: 'ComboBox',
				label: this._('Number of CPUs'),
				depends: 'domainURI',
				dynamicValues: types.getCPUs
			}, {
				name: 'maxMem',
				type: 'TextBox',
				label: this._('Memory')
			}, {
				name: 'boot_hvm',
				type: 'MultiInput',
				label: this._('Boot order'),
				subtypes: [ {
					type: 'ComboBox',
					staticValues: types.bootDevices
				} ]
			}, {
				name: 'boot_pv',
				type: 'ComboBox',
				label: this._('Boot device')
			}, {
				name: 'os_type',
				type: 'HiddenInput'
			}, {
				name: 'domain_type',
				type: 'HiddenInput'
			}, {
				name: 'type',
				depends: 'domain_type',
				type: 'ComboBox',
				readonly: true,
				label: this._('Virtualization technology'),
				dynamicValues: types.getVirtualizationTechnology
			}, {
				name: 'rtc_offset',
				type: 'ComboBox',
				label: this._('RTC reference'),
				staticValues: types.rtcOffset
			}, {
				name: 'vnc',
				type: 'CheckBox',
				label: this._('Direct access (VNC)')
			}, {
				name: 'vnc_remote',
				type: 'CheckBox',
				label: this._('Globally available')
			}, {
				name: 'vnc_password',
				type: 'PasswordBox',
				label: this._('VNC password')
			}, {
				name: 'kblayout',
				type: 'ComboBox',
				label: this._('Keyboard layout'),
				staticValues: types.keyboardLayout
			}],
			layout: [{
				label: this._('Machine'),
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
				label: this._('Remote access'),
				layout: [
					 [ 'vnc', 'vnc_remote' ],
					'vnc_password',
					'kblayout'
				]
			}],
			scrollable: true
		});
		this.connect(this._advancedForm, 'onSubmit', 'save');
		this._advancedPage.addChild(this._advancedForm);

		//
		// devices page
		//

		this._devicesPage = new umc.widgets.Page({
			headerText: this._('Settings for devices'),
			title: this._('Devices'),
			footerButtons: [{
				label: this._('Back to overview'),
				name: 'cancel',
				callback: dojo.hitch(this, 'confirmClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});
		var container = new umc.widgets.ContainerWidget({
			scrollable: true
		});
		this._devicesPage.addChild(container);

		// grid for the drives
		this._driveStore = new umc.store.Memory({
			idProperty: '$id$'
		});
		this._driveGrid = new umc.modules._uvmm.DriveGrid({
			moduleStore: this._driveStore
		});

		// wrap grid in a titlepane
		var titlePane = new umc.widgets.TitlePane({
			title: this._('Drives')
		});
		titlePane.addChild(this._driveGrid);
		container.addChild(titlePane);

		// grid for the network interfaces
		this._interfaceStore = new umc.store.Memory({
			idProperty: '$id$'
		});
		this._interfaceGrid = new umc.modules._uvmm.InterfaceGrid({
			moduleStore: this._interfaceStore
		});

		// wrap grid in a titlepane
		titlePane = new umc.widgets.TitlePane({
			title: this._('Network interfaces')
		});
		titlePane.addChild(this._interfaceGrid);
		container.addChild(titlePane);

		// we need to call resize() manually to make sure the grids are rendered correctly
		this.connect(this._devicesPage, 'onShow', function() {
			this._driveGrid.resize();
			this._interfaceGrid.resize();
		});

		//
		// snapshot page
		//

		this._snapshotPage = new umc.widgets.Page({
			headerText: this._('Snapshots settings'),
			title: this._('Snapshots'),
			footerButtons: [{
				label: this._('Back to overview'),
				name: 'cancel',
				callback: dojo.hitch(this, 'confirmClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});

		// grid for the drives
		this._snapshotStore = umc.store.getModuleStore('id', 'uvmm/snapshot');
		this._snapshotGrid = new umc.modules._uvmm.SnapshotGrid({
			moduleStore: this._snapshotStore,
			onUpdateProgress: dojo.hitch(this, 'onUpdateProgress')
		});
		titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Snapshots')
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
		var widgets = dojo.mixin({}, this._generalForm._widgets, this._advancedForm._widgets);
		umc.tools.forIn(widgets, function(iname, iwidget) {
			valid = valid && (false !== iwidget.isValid());
			return valid;
		}, this);

		if (!valid) {
			umc.dialog.alert(this._('The entered data is not valid. Please correct your input.'));
			return;
		}

		var values = this.getValues();
		delete values.domainURI;

		this.standby(true);
		umc.tools.umcpCommand('uvmm/domain/put', {
			nodeURI: this._domain.domainURI.split('#')[0],
			domain: values
		}).then(dojo.hitch(this, function() {
			this.onClose();
			this.standby(false);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	load: function(id) {
		this._standbyWidget.opacity = 1;
		this.standby(true);
		this._standbyWidget.opacity = 0.75;

		umc.tools.umcpCommand('uvmm/domain/get', {
			domainURI: id
		}).then(dojo.hitch(this, function(data) {
			// get data blob
			this._domain = dojo.getObject('result', false, data);
			this._domain.domainURI = id;
			this._domain.nodeURI = id.slice( 0, id.indexOf( '#' ) );

			if (data) {
				var types = umc.modules._uvmm.types;
				this._domain.domainURI = id;

				this.moduleWidget.set( 'title', 'UVMM: ' + this._domain.name );

				// clear form data
				this._generalForm.clearFormValues();
				this._advancedForm.clearFormValues();
				// set values to form
				this._generalForm.setFormValues(this._domain);

				this._generalPage.clearNotes();
				if ( ! this._domain.available ) {
					this._generalPage.addNote( this._( '<p>For fail over the virtual machine can be migrated to another physical server re-using the last known configuration and all disk images. This can result in <strong>data corruption</strong> if the images are <strong>concurrently used</strong> by multiple running instances! Therefore the failed server <strong>must be blocked from accessing the image files</strong>, for example by blocking access to the shared storage or by disconnecting the network.</p><p>When the server is restored, all its previous virtual instances will be shown again. Any duplicates have to be cleaned up manually by migrating the instances back to the server or by deleting them. Make sure that shared images are not delete.</p>' ) );
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
					var block_devices = dojo.map( this._domain.disks, function( disk ) {
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
				dojo.forEach(this._domain.interfaces, function(idev, i) {
					idev.$id$ = i + 1;
				});

				// we need to add pseudo ids for the disk drives
				dojo.forEach(this._domain.disks, function(idrive, i) {
					idrive.$id$ = i + 1;
				});

				// update the stores
				this._snapshotGrid.set('domainURI', id);
				this._driveGrid.set('domain', this._domain);
				this._interfaceGrid.set('domain', this._domain);
				this._interfaceStore.setData(this._domain.interfaces);
				this._driveStore.setData(this._domain.disks);

				var qcow2_images = 0;
				var snapshots_possible = dojo.every( this._domain.disks, function( disk ) {
					if ( disk.driver_type == 'qcow2' ) {
						++qcow2_images;
						return true;
					}
					return disk.device == 'floppy' || ( disk.driver_type == 'qcow2' || disk.readonly );
				} );
				if ( snapshots_possible && qcow2_images > 0 ) {
					this.showChild( this._snapshotPage );
				} else {
					this.hideChild( this._snapshotPage );
				}

				// deactivate most input field when domain is running
				var disabled = false;
				if ( this._domain.state == 'RUNNING' || this._domain.state == 'IDLE' ) {
					disabled = true;
				}
				if ( disabled && ! this.disabled ) {
					this._generalPage.addNote( this._( 'While the virtual instance is running most of the settings can not be changed.' ) );
				} else if ( ! disabled ) {
					this._generalPage.clearNotes();
				}
				this.disabled = disabled;
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
					this._advancedForm._widgets.arch.set( 'disabled', disabled );
				} else {
					this._advancedForm._widgets.arch.set( 'visible', false );
				}
				this._driveGrid.set( 'disabled', disabled );
				this._interfaceGrid.set( 'disabled', disabled );
				umc.tools.forIn( this._advancedForm._widgets, dojo.hitch( this, function( iid, iwidget ) {
					if ( iwidget.readonly ) {
						iwidget.set( 'disabled', true );
					} else {
						iwidget.set( 'disabled', disabled );
					}
				} ) );
				this.selectChild( this._generalPage, true);
			}
			this._loadedValues = this.getValues();
			// iterate over all advanced settings to set dynamically loaded values
			umc.tools.forIn(this._advancedForm._widgets, function(ikey) {
				if (this._loadedValues[ikey] === '' && this._domain[ikey] !== null && this._domain[ikey] !== undefined) {
					this._loadedValues[ikey] = String(this._domain[ikey]);
				}
			}, this);
			this.standby(false);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	getValues : function() {
		var values = dojo.mixin({}, this._domain, 
			this._generalForm.gatherFormValues(), 
			this._advancedForm.gatherFormValues()
		);

		// special handling for boot devices
		var paravirtual = this._domain.type === 'xen-xen';
		if ( paravirtual ) {
			var disks = [], boot_medium = null;
			dojo.forEach( this._domain.disks, function( disk ) {
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
		return values;
	},

	confirmClose : function() {
		// summary:
		// 		If changes have been made show a confirmation dialogue before closing the page

		if (!umc.tools.isEqual(this._loadedValues, this.getValues())) {
			// Changes have been made. Display confirm dialogue.
			return umc.dialog.confirm( this._('There are unsaved changes. Are you sure to cancel nevertheless?'), [{
				label: this._('Discard changes'),
				name: 'quit',
				callback: dojo.hitch(this, 'onClose')
				}, {
					label: this._('Continue editing'),
					name: 'cancel',
					'default': true
				}]
			);
		}

		// No changes have been made. Close the page
		this.onClose();
	},

	onClose: function() {
		// event stub
	},

	onUpdateProgress: function(i, n) {
		// event stub
	}
});
