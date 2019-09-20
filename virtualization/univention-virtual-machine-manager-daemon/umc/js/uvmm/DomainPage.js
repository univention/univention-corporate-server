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
/*global define,location*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"dojo/on",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TabController",
	"dijit/layout/StackContainer",
	"umc/widgets/TitlePane",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/TextArea",
	"umc/widgets/HiddenInput",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/CheckBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/SuggestionBox",
	"umc/modules/uvmm/SnapshotGrid",
	"umc/modules/uvmm/TargetHostGrid",
	"umc/modules/uvmm/InterfaceGrid",
	"umc/modules/uvmm/DriveGrid",
	"umc/modules/uvmm/MemoryTextBox",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, topic, on, Memory, Observable, tools, dialog, store, Page, Form, ContainerWidget, TabController, StackContainer, TitlePane, StandbyMixin,
	TextBox, TextArea, HiddenInput, ComboBox, MultiInput, CheckBox, PasswordBox, SuggestionBox, SnapshotGrid, TargetHostGrid, InterfaceGrid, DriveGrid, MemoryTextBox, types, _) {

	return declare("umc.modules.uvmm.DomainPage", [ Page, StandbyMixin ], {
		nested: true,

		_generalForm: null,
		_advancedForm: null,

		_generalPage: null,
		_advancedPage: null,
		_devicesPage: null,
		_snapshotPage: null,
		_targethostPage: null,

		_driveStore: null,
		_driveGrid: null,
		_interfaceStore: null,
		_interfaceGrid: null,
		_snapshotStore: null,
		_snapshotGrid: null,
		_targethostGrid: null,
		_targethostStore: null,

		_domain: null,

		isClosable: false,

		addNotification: dialog.notify,

		postMixInProperties: function() {
			this.inherited(arguments);
			lang.mixin(this, {
				headerButtons: [{
					iconClass: 'umcCloseIconWhite',
					name: 'close',
					label: this.isClosable ? _('Cancel') : _('Back to overview'),
					callback: lang.hitch(this, 'onCloseTab')
				}, {
					name: 'save',
					iconClass: 'umcSaveIconWhite',
					label: _('Save'),
					defaultButton: true,
					callback: lang.hitch(this, 'save')
				}]
			});
		},

		buildRendering: function() {
			this.inherited(arguments);
			//
			// general settings page
			//

			this._generalPage = new Page({
				headerText: _('General settings'),
				title: _('General')
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
						var val = this._generalForm.get('value');
						if (val.contact) {
							location.href = 'mailto:' + encodeURIComponent(val.contact) + '?subject=' + encodeURIComponent(_('Virtual machine: %s', val.name));
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
				}]
			});
			this._generalForm.on('Submit', lang.hitch(this, 'save'));
			this._generalPage.addChild(this._generalForm);
			this._generalForm._buttons.email.set('visible', false);

			//
			// advanced settings page
			//

			this._advancedPage = new Page({
				headerText: _('Advanced settings'),
				title: _('Advanced')
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
					label: _('Number of CPUs')
				}, {
					name: 'cpu_model',
					type: SuggestionBox,
					label: _('CPU model'),
					staticValues: types.cpuModels
				}, {
					name: 'maxMem',
					type: MemoryTextBox,
					required: true,
					softMax: 4*1024*1024*1024*1024,
					softMaxMessage: _('<b>Warning:</b> Memory size exceeds currently available RAM on node. Starting the VM may degrade the performance of the host and all other VMs.'),
					label: _('Memory (default unit MB)')
				}, {
					name: 'boot_hvm',
					type: MultiInput,
					label: _('Boot order'),
					subtypes: [ {
						type: ComboBox,
						staticValues: types.bootDevices
					} ]
				}, {
					name: 'rtc_offset',
					type: ComboBox,
					label: _('RTC reference'),
					staticValues: types.rtcOffset
				}, {
					name: 'autostart',
					label: _('Always start VM with host'),
					type: CheckBox
				}, {
					name: 'vnc',
					type: CheckBox,
					label: _('Direct access (VNC)')
				}, {
					name: 'hyperv',
					type: CheckBox,
					label: _('Enable Hyper-V Enlightment')
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
					label: _('VNC password'),
					softMaxLength: 8,
					softMaxLengthMessage: _('<b>Warning:</b> VNC only supports passwords up to %s characters. Please consider shortening the password.', 8)
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
						'cpu_model',
						'maxMem',
						'rtc_offset',
						'boot_hvm',
						'hyperv',
						'autostart'
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
				title: _('Devices')
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
				title: _('Snapshots')
			});

			// grid for the snapshots
			this._snapshotStore = store('id', 'uvmm/snapshot');
			this._snapshotGrid = new SnapshotGrid({
				moduleStore: this._snapshotStore,
				onUpdateProgress: lang.hitch(this, 'onUpdateProgress')
			});
			this._snapshotPage.addChild(this._snapshotGrid);

			//
			// target host page
			//

			this._targethostPage = new Page({
				headerText: _('Migration targethost settings'),
				title: _('Migration targethosts')
			});

			// grid for the target hosts
			this._targethostStore = store('id', 'uvmm/targethost');
			this._targethostGrid = new TargetHostGrid({
				moduleStore: this._targethostStore,
				onUpdateProgress: lang.hitch(this, 'onUpdateProgress')
			});
			this._targethostPage.addChild(this._targethostGrid);

			this._stack = new StackContainer({});
			// add pages in the correct order
			this.addSubPage(this._generalPage);
			this.addSubPage(this._devicesPage);
			this.addSubPage(this._snapshotPage);
			this.addSubPage(this._targethostPage);
			this.addSubPage(this._advancedPage);
			this.addChild(this._stack);
		},

		addSubPage: function(page) {
			page.tabController = new TabController({
				containerId: this._stack.id,
				region: 'nav'
			});
			page.addChild(page.tabController);
			this._stack.addChild(page);
		},

		hideChild: function(page) {
			array.forEach(this._stack.getChildren(), function(child) {
				child.tabController.hideChild(page);
			});
		},

		showChild: function(page) {
			array.forEach(this._stack.getChildren(), function(child) {
				child.tabController.showChild(page);
			});
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
			values.boot = values.boot_hvm;

			this.standby(true);
			tools.umcpCommand('uvmm/domain/put', {
				nodeURI: this._domain.domainURI.split('#')[0],
				domain: values
			}).then(lang.hitch(this, function() {
				this.onCloseTab();
				this.standby(false);
			}), lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		load: function(id) {
			// clear form data
			this._generalForm.clearFormValues();
			this._stack.selectChild( this._generalPage, true);

			var nodeURI = id.slice(0, id.indexOf( '#'));

			this.standbyDuring(tools.umcpCommand('uvmm/node/query', {
					nodePattern: nodeURI
			}).then(lang.hitch(this, function(data) {
				if (data.result.length) {
					var node = data.result[0];

					var wm = this._advancedForm.getWidget('maxMem');
					wm.set('constraints', lang.mixin({}, wm.get('constraints'), {max: node.memPhysical}));
					wm.set('softMax', node.memPhysical - node.memUsed);

					types.setCPUs(node.cpus, this._advancedForm.getWidget('vcpus'));
				}

				return tools.umcpCommand('uvmm/domain/get', {
					domainURI: id
				}).then(lang.hitch(this, function(data) {
					// get data blob
					this._domain = lang.getObject('result', false, data);
					this._domain.domainURI = id;
					this._domain.nodeURI = nodeURI;

					if (data) {
						this._domain.domainURI = id;

						this.moduleWidget.set('titleDetail', this._domain.name);

						this._advancedForm.clearFormValues();
						// set values to form
						this._generalForm.setFormValues(this._domain);

						if ( ! this._domain.available ) {
							this.addNotification( _( '<p>For fail over the virtual machine can be migrated to another physical server re-using the last known configuration and all disk images. This can result in <strong>data corruption</strong> if the images are <strong>concurrently used</strong> by multiple running machines! Therefore the failed server <strong>must be blocked from accessing the image files</strong>, for example by blocking access to the shared storage or by disconnecting the network.</p><p>When the server is restored, all its previous virtual machines will be shown again. Any duplicates have to be cleaned up manually by migrating the machines back to the server or by deleting them. Make sure that shared images are not delete.</p>' ) );
							this.hideChild( this._devicesPage );
							this.hideChild( this._snapshotPage );
							this.hideChild( this._targethostPage );
							this.hideChild( this._advancedPage );
							this._headerButtons.save.set( 'disabled', true );
							// name should not be editable
							this._generalForm._widgets.name.set( 'disabled', true );
							this.standby( false );
							return;
						} else {
							this.showChild( this._advancedPage );
							this.showChild( this._devicesPage );
							this._headerButtons.save.set( 'disabled', false );
						}
						this._advancedForm._widgets.maxMem.resetCache();
						this._advancedForm.setFormValues(this._domain);

						// special handling for boot devices
						this._advancedForm._widgets.boot_hvm.set( 'value', this._domain.boot );

						// we need to add pseudo ids for the network interfaces
						array.forEach(this._domain.interfaces, function(idev, i) {
							idev.$id$ = i + 1;
						});

						// we need to add pseudo ids for the drives
						array.forEach(this._domain.disks, function(idrive, i) {
							idrive.$id$ = i + 1;
						});

						// update the stores
						this._targethostGrid.set('domain', this._domain);
						this._snapshotGrid.set('domain', this._domain);
						this._driveGrid.set('domain', this._domain);
						this._interfaceGrid.set('domain', this._domain);
						this._interfaceStore.setData(this._domain.interfaces);
						this._driveStore.setData(this._domain.disks);

						this.showChild( this._snapshotPage );
						this.showChild( this._targethostPage );

						// set visibility of the VNC-Port
						this._advancedForm._widgets.vnc_port.set('visible', Boolean(this._advancedForm._widgets.vnc_port.get('value')));

						// deactivate most input field when domain is running
						var domainActive = types.isActive(this._domain);

						// name should not be editable
						this._generalForm._widgets.name.set( 'disabled', true );

						this._targethostGrid.set( 'domainActive', domainActive );
						this._advancedForm._widgets.arch.set( 'disabled', domainActive );
						this._driveGrid.set( 'domainActive', domainActive );
						this._interfaceGrid.set( 'disabled', domainActive );
						tools.forIn( this._advancedForm._widgets, lang.hitch( this, function( iid, iwidget ) {
							if ( iwidget.readonly ) {
								iwidget.set( 'disabled', true );
							} else {
								iwidget.set( 'disabled', domainActive );
							}
						} ) );

						// force a refresh of the grids
						this._interfaceGrid.filter();
						this._driveGrid.filter();
						this._snapshotGrid.filter();
						this._targethostGrid.filter();
					}
				}));
			})));
		},

		onCloseTab: function() {
			// event stub
		},

		onUpdateProgress: function(/*i, n*/) {
			// event stub
		}
	});
});
