/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._uvmm.DomainPage");

dojo.require("dojox.string.sprintf");
dojo.require("umc.i18n");
dojo.require("umc.render");
dojo.require("umc.tools");
dojo.require("umc.store");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets.TitlePane");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.modules._uvmm.types");

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
			headerText: this._('Devices'),
			title: this._('Settings for devices'),
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
		var diskGrid = new umc.widgets.Grid({
			query: { source: '*' },
			style: 'width: 100%; height: 150px;',
			moduleStore: this._diskStore,
			columns: [{
				name: 'device',
				label: this._('Type'),
				formatter: dojo.hitch(this, function(dev) {
					return umc.modules._uvmm.types.blockDevices[dev] || this._('unknown');
				})
			}, {
				name: 'source',
				label: this._('Image'),
				formatter: function(source) {
					var list = source.split('/');
					if (list.length) {
						return list[list.length - 1];
					}
					return this._('unknown');
				}
			}, {
				name: 'size',
				label: this._('Size'),
				formatter: function(size) {
					return dojox.string.sprintf('%.1f GB', size / 1073741824.0);
				}
			}, {
				name: 'pool',
				label: this._('Pool')
			}]
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
		var interfaceGrid = new umc.widgets.Grid({
			query: { source: '*' },
			style: 'width: 100%; height: 150px;',
			moduleStore: this._interfaceStore,
			columns: [{
				name: 'type',
				label: this._('Type')
			}, {
				name: 'source',
				label: this._('Source')
			}, {
				name: 'model',
				label: this._('Driver'),
				formatter: dojo.hitch(this, function(model) {
					return umc.modules._uvmm.types.interfaceModels[model] || this._('unknown');
				})
			}, {
				name: 'mac_address',
				label: this._('MAC address')
			}]
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
			headerText: this._('Snapshots'),
			title: this._('Snapshot settings'),
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
		this._snapshotGrid = new umc.widgets.Grid({
			moduleStore: this._snapshotStore,
			columns: [{
				name: 'label',
				label: this._('Name')
			}, {
				name: 'time',
				label: this._('Date')
			}]
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
				this._snapshotGrid.filter({ domainURI: this._domain.domainURI });
			}
			this.standby(false);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	onClose: function() {
		// event stub
	}

});



