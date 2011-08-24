/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.OverviewPage");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Page");

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
			isStandardAction: true
			// TODO isMultiAction useful?
		}, {
			name: 'deactivateQuota',
			label: this._('Deactivate'),
			isStandardAction: true
			// TODO isMultiAction useful?
		}, {
			name: 'configureQuota',
			label: this._('Configure'),
			isStandardAction: false
			// TODO isMultiAction useful?
		}];

		var columns = [{
			name: 'partitionDevice',
			label: this._('Partition'),
			width: 'auto' // adjust won't work correctly
		}, {
			name: 'mountPoint',
			label: this._('Mount point'),
			width: 'auto' // adjust won't work correctly
		}, {
			name: 'inUse',
			label: this._('Quota'),
			width: 'auto' // adjust won't work correctly
		}, {
			name: 'partitionSize',
			label: this._('Size'),
			width: 'auto' // adjust won't work correctly
		}, {
			name: 'freeSpace',
			label: this._('Free'),
			width: 'auto' // adjust won't work correctly
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
	},
});
