/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.quota");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");

dojo.require("umc.modules._quota.PartitionPage");
dojo.require("umc.modules._quota.DetailPage");

dojo.declare("umc.modules.quota", [ umc.widgets.Module, umc.i18n.Mixin ], {

	idProperty: 'partitionDevice',
	moduleStore: null,
	_overviewPage: null,
	_partitionPage: null,
	_detailPage: null,

	buildRendering: function() {
		this.inherited(arguments);
		this.renderOverviewPage();
		this.renderPartitionPage();
		this.renderDetailPage();
	},

	renderOverviewPage: function() {
		this._overviewPage = new umc.widgets.Page({
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
				this._partitionPage.init(partitionDevice[0]);
				this.selectChild(this._partitionPage);
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

	renderPartitionPage: function() {
		var partitionDevice = '';
		this._partitionPage = new umc.modules._quota.PartitionPage({
			moduleStore: this.getModuleStore('id', this.moduleID + '/partitions'),
			headerText: this._('Partition: %s', partitionDevice),
			helpText: this._('Set, unset and modify filesystem quota')
		});
		this.addChild(this._partitionPage);
		this.connect(this._partitionPage, 'onClosePage', function() {
			this.selectChild(this._overviewPage);
		});
		this.connect(this._partitionPage, 'onShowDetailPage', function(data) {
			this._detailPage.init(data);
			this.selectChild(this._detailPage);
		});
	},

	renderDetailPage: function() {
		this._detailPage = new umc.modules._quota.DetailPage({
			headerText: this._('Add quota setting for a user on partition'),
			helpText: this._('Add quota setting for a user on partition')
		});
		this.addChild(this._detailPage);
		this.connect(this._detailPage, 'onClosePage', function() {
			this.selectChild(this._partitionPage);
		});
	}
});
