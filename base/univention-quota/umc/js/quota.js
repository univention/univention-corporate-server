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
			label: dojo.hitch(this, function(item) {
				if (item === undefined) {
					return this._('(De)activate');
				} else if (item.inUse === true) {
					return this._('Deactivate');
				} else {
					return this._('Activate');
				}
			}),
			isStandardAction: true,
			callback: dojo.hitch(this, function(partitionDevice) {
				var doActivate = true;
				var item = this._grid.getItem(partitionDevice);
				if (item.inUse === true) {
					doActivate = false;
				}
				this.activateQuota(partitionDevice, doActivate);
			})
		}, {
			name: 'edit',
			label: this._('Configure'),
			iconClass: 'umcIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			canExecute: function(item) {
				if (item.inUse === true) {
					return true;
				} else {
					return false;
				}
			},
			callback: dojo.hitch(this, function(partitionDevice) {
				this.createPageContainer(partitionDevice[0]);
			})
		}, {
			name: 'refresh',
			label: this._('Refresh'),
			isContextAction: false,
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function() {
				this._grid.filter({'dummy': 'dummy'});
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
				if (value === null) {
					return this._('Unknown');
				} else if (value === true) {
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
				if (value === null) {
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
				if (value === null) {
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
			var gridItems = this._grid.getAllItems(); // TODO rename?
			dojo.forEach(gridItems, dojo.hitch(this, function(item) {
				if (item.inUse === null) {
					this._grid.setDisabledItem(item.partitionDevice, true);
				}
			}));
		});

		this._overviewPage.startup();
	},

	activateQuota: function(partitionDevice, doActivate) {
		var dialogMessage = '';
		if (doActivate === true) {
			dialogMessage = this._('Please confirm quota support activation on device: %s', partitionDevice);
		} else {
			dialogMessage = this._('Please confirm quota support deactivation on device: %s', partitionDevice);
		}
		umc.dialog.confirm(dialogMessage, [{
			label: this._('OK'),
			callback: dojo.hitch(this, function() {
				umc.tools.umcpCommand('quota/partitions/' + (doActivate ? 'activate' : 'deactivate'),
									  {"partitionDevice" : partitionDevice.shift()}).then(
										  dojo.hitch(this, function(data) {
											  if (data.result.success === true) {
												  this._grid.filter({'dummy': 'dummy'});
											  } else {
												  this._showActivateQuotaDialog(data.result, doActivate);
											  }
										  })
									  );
			})
		}, {
			label: this._('Cancel')
		}]);
	},

	_showActivateQuotaDialog: function(result, doActivate) {
		var message = [];
		if (doActivate === true) {
			message = this._('Failed to activate quota support: ');
		} else {
			message = this._('Failed to deactivate quota support: ');
		}
		dojo.forEach(result.objects, function(item) {
			if (item.success === false) {
				message = message + item.message;
			}
		});
		umc.dialog.confirm(message, [{
			label: this._('OK')
		}]);
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
