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
			name: 'activate',
			label: this._('Activate')
		}, {
			name: 'deactivate',
			label: this._('Deactivate')
		}];

		var columns = [{
			name: 'partition',
			label: this._('Partition'),
			width: 'auto'
		}, {
			name: 'mountPoint',
			label: this._('Mount point'),
			width: 'auto'
		}, {
			name: 'quota',
			label: this._('Quota'),
			width: 'auto'
		}, {
			name: 'size',
			label: this._('Size'),
			width: 'auto'
		}, {
			name: 'free',
			label: this._('Free'),
			width: 'auto'
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore
		});
		titlePane.addChild(this._grid);
	},
});
