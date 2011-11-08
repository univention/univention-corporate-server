/*global console MyError dojo dojox dijit umc */

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
dojo.require("umc.modules._uvmm.DiskGrid");

dojo.declare("umc.modules._uvmm.DomainPage", [ umc.widgets.TabContainer, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	nested: true,

	i18nClass: 'umc.modules.uvmm',

	_generalForm: null,

	_generalPage: null,
	_devicesPage: null,
	_snapshotPage: null,

	_diskStore: null,
	_interfaceStore: null,
	_snapshotStore: null,
	_snapshotGrid: null,

	_domain: null,

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
				callback: dojo.hitch(this, 'onClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});
		this.addChild(this._generalPage);

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
				label: this._('Contact')
			}, {
				name: 'description',
				type: 'TextBox',
				label: this._('Description')
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
				name: 'boot',
				type: 'MultiInput',
				label: this._('Boot order'),
				subtypes: [{
					type: 'ComboBox',
					staticValues: types.bootDevices
				}]
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
				type: 'TextBox',
				label: this._('VNC password')
			}, {
				name: 'kblayout',
				type: 'ComboBox',
				label: this._('Keyboard layout'),
				staticValues: types.keyboardLayout
			}],
			layout: [{
				label: this._('Settings'),
				layout: [
					[ 'name', 'os' ],
					[ 'contact', 'description' ],
					'arch',
					[ 'vcpus', 'maxMem' ]
				]
			}, {
				label: this._('Extended settings'),
				layout: [
					[ 'domain_type', 'os_type', 'type' ],
					'boot',
					'rtc_offset',
					[ 'vnc', 'vnc_remote' ],
					'vnc_password',
					'kblayout'
				]
			}],
			onSubmit: dojo.hitch(this, 'save'),
			scrollable: true
		});
		this._generalPage.addChild(this._generalForm);

		//
		// devices page
		//

		this._devicesPage = new umc.widgets.Page({
			headerText: this._('Settings for devices'),
			title: this._('Devices'),
			footerButtons: [{
				label: this._('Back to overview'),
				name: 'cancel',
				callback: dojo.hitch(this, 'onClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});
		this.addChild(this._devicesPage);
		var container = new umc.widgets.ContainerWidget({
			scrollable: true
		});
		this._devicesPage.addChild(container);

		// grid for the disks
		this._diskStore = new umc.store.Memory({
			idProperty: 'source'
		});
		var diskGrid = new umc.modules._uvmm.DiskGrid({
			moduleStore: this._diskStore
		});

		// wrap grid in a titlepane
		var titlePane = new umc.widgets.TitlePane({
			title: this._('Drives')
		});
		titlePane.addChild(diskGrid);
		container.addChild(titlePane);

		// grid for the network interfaces
		this._interfaceStore = new umc.store.Memory({
			idProperty: 'mac_address'
		});
		var interfaceGrid = new umc.modules._uvmm.InterfaceGrid({
			moduleStore: this._interfaceStore
		});

		// wrap grid in a titlepane
		titlePane = new umc.widgets.TitlePane({
			title: this._('Network interfaces')
		});
		titlePane.addChild(interfaceGrid);
		container.addChild(titlePane);
		
		// we need to call resize() manually to make sure the grids are rendered correctly
		this.connect(this._devicesPage, 'onShow', function() {
			diskGrid.resize();
			interfaceGrid.resize();
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
				callback: dojo.hitch(this, 'onClose')
			}, {
				label: this._('Save'),
				defaultButton: true,
				name: 'save',
				callback: dojo.hitch(this, 'save')
			}]
		});
		this.addChild(this._snapshotPage);

		// grid for the disks
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
	},

	save: function() {
		this.onClose();
	},

	load: function(id) {
		this.standby(true);
		umc.tools.umcpCommand('uvmm/domain/get', {
			domainURI: id
		}).then(dojo.hitch(this, function(data) {
			// get data blob
			this._domain = dojo.getObject('result.data', false, data);
			this._domain.domainURI = id;

			if (data) {
				// set values to form
				this._generalForm.setFormValues(this._domain);

				// update the stores
				this._interfaceStore.setData(this._domain.interfaces);
				this._diskStore.setData(this._domain.disks);
				this._snapshotGrid.set('domainURI', id);
			}
			this.standby(false);
		}), dojo.hitch(this, function() {
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



