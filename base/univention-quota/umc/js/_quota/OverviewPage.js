/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.OverviewPage");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Page");
dojo.require("umc.tools");

dojo.declare("umc.modules._quota.OverviewPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	moduleStore: null,
	_grid: null,

	buildRendering: function() {
		this.inherited(arguments);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Partition overview')
		});
		this.addChild(titlePane);

		var actions = [{
			name: 'activateQuota',
			label: this._('Activate'),
			isStandardAction: true,
			callback: dojo.hitch(this, function() {
				var partitions = this._grid.getSelectedIDs();
				umc.tools.umcpCommand('quota/partitions/activate', {"partitions" : partitions}).then(dojo.hitch(this, function() {
					umc.dialog.notify(this._('quota/partitions/activate'));
				}));
			})
			// TODO isMultiAction useful?
		}, {
			name: 'deactivateQuota',
			label: this._('Deactivate'),
			isStandardAction: true,
			callback: dojo.hitch(this, function() {
				var partitions = this._grid.getSelectedIDs();
				umc.tools.umcpCommand('quota/partitions/deactivate', {"partitions" : partitions}).then(dojo.hitch(this, function() {
					umc.dialog.notify(this._('quota/partitions/deactivate'));
				}));
			})
		}, {
			name: 'configureQuota',
			label: this._('Configure'),
			isStandardAction: false
		}];

		var columns = [{
			name: 'partitionDevice',
			label: this._('Partition'),
			width: 'auto' // TODO adjust won't work correctly
		}, {
			name: 'mountPoint',
			label: this._('Mount point'),
			width: 'auto'
		}, {
			name: 'inUse',
			label: this._('Quota'),
			width: 'auto'
		}, {
			name: 'partitionSize',
			label: this._('Size'),
			width: 'auto'
		}, {
			name: 'freeSpace',
			label: this._('Free'),
			width: 'auto'
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
	}
});
