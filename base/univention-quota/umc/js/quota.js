/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.quota");

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
				umc.tools.umcpCommand('quota/partitions/activate', {"partitions" : partitions}).then(dojo.hitch(this, function(result) {
					umc.dialog.notify(this._('Quota support successfully activated'));
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
				umc.tools.umcpCommand('quota/partitions/deactivate', {"partitions" : partitions}).then(dojo.hitch(this, function() {
					umc.dialog.notify(this._('Quota support successfully deactivated'));
				}));
			})
		}, {
			name: 'configure',
			label: this._('Configure'),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(partitionDevice) {
				this.createPageContainer(partitionDevice[0]);
				// this._partitionPage.init(partitionDevice[0]);
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
			width: '85px'
		}, {
			name: 'partitionSize',
			label: this._('Size'),
			width: 'adjust'
		}, {
			name: 'freeSpace',
			label: this._('Free'),
			width: 'adjust'
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
