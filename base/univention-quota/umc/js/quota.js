/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.quota");

dojo.require("dojox.string.sprintf");
dojo.require("umc.i18n");
dojo.require("umc.store");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TabbedModule");

dojo.require("umc.modules._quota.PageContainer");

dojo.declare("umc.modules.quota", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {

	idProperty: 'partitionDevice',
	moduleStore: null,
	_overviewPage: null,
	_pageContainer: null,

	buildRendering: function() {
		this.inherited(arguments);
		this.renderOverviewPage();
	},

	postMixInProperties: function() {
		this.inherited(arguments);
		this.moduleStore = umc.store.getModuleStore(this.idProperty, this.moduleID + '/partitions');
	},

	renderOverviewPage: function() {
		this._overviewPage = new umc.widgets.Page({
			title: this._('Partitions'),
			moduleStore: this.moduleStore,
			headerText: this._('List partitions'),
			helpText: this._('Set, unset and modify filesystem quota')
		});
		this.addChild(this._overviewPage);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Partition overview')
		});
		this._overviewPage.addChild(titlePane);

		var actions = [{
			name: 'activate',
			label: this._('Activate'),
			iconClass: 'dijitIconNewTask', // TODO
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, function() {
				var partitions = this._grid.getSelectedIDs();
				umc.tools.umcpCommand('quota/partitions/activate', {"partitions" : partitions}).then(dojo.hitch(this, function(data) {
					if (data.result.failed === false) {
							umc.dialog.alert(data.result.message);
					}
					else {
						umc.dialog.notify(this._('Quota support successfully activated'));
					}
					this._grid.filter({
						'dummy': 'dummy'
					});
				}));
			})
		}, {
			name: 'deactivate',
			label: this._('Deactivate'),
			iconClass: 'dijitIconDelete', // TODO
			isStandardAction: true,
			isMultiAction: true,
			callback: dojo.hitch(this, function() {
				var partitions = this._grid.getSelectedIDs();
				umc.tools.umcpCommand('quota/partitions/deactivate', {"partitions" : partitions}).then(dojo.hitch(this, function(data) {
					if (data.result.failed === false) {
						var message = '';
						dojo.forEach(data.result.partitions, function(i) {
							umc.dialog.notify(this._('Failed to deactivate quota support')); // TODO
						});
					}
					else {
						umc.dialog.notify(this._('Quota support successfully deactivated'));
					}
					this._grid.filter({'dummy': 'dummy'});
				}));
			})
		}, {
			name: 'edit',
			label: this._('Configure'),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(partitionDevice) {
				this.createPageContainer(partitionDevice[0]);
			})
		}];

		var columns = [{
			name: 'partitionDevice',
			label: this._('Partition'),
			width: 'auto'
		}, {
			name: 'mountPoint',
			label: this._('Mount point'),
			width: 'auto'
		}, {
			name: 'inUse',
			label: this._('Quota'),
			width: '85px',
			formatter: dojo.hitch(this, function(value) {
				if (value === true) {
					return this._('Activated');
				} else {
					return this._('Deactivated');
				}
			})
		}, {
			name: 'partitionSize',
			label: this._('Size (GB)'),
			width: 'adjust',
			formatter: function(value) {
				if (value == null) {
					return '-';
				} else {
					return dojox.string.sprintf('%.1f', value);
				}
			}
		}, {
			name: 'freeSpace',
			label: this._('Free (GB)'),
			width: 'adjust',
			formatter: function(value) {
				if (value == null) {
					return '-';
				} else {
					return dojox.string.sprintf('%.1f', value);
				}
			}
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			query: {
				dummy: 'dummy'
			}
		});
		titlePane.addChild(this._grid);
		this.connect(this._grid, 'onFilterDone', function() {
			var gridItems = this._grid.getAllItems();
			console.log(gridItems);
			dojo.forEach(gridItems, dojo.hitch(this, function(item) {
				if (item.inUse === false) {
					this._grid.setDisabledItem(item.partitionDevice);
				}
			}));
		});

		this._overviewPage.startup();
	},

	createPageContainer: function(partitionDevice) {
		this._pageContainer = new umc.modules._quota.PageContainer({
			title: partitionDevice,
			closable: true,
			moduleID: this.moduleID,
			partitionDevice: partitionDevice
		});
		this.addChild(this._pageContainer);
		this.selectChild(this._pageContainer);
	}
});
