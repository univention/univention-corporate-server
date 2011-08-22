/*global console MyError dojo dojox dijit umc */
// TODO
// 		Fix moduleStore

dojo.provide("umc.modules._quota.QuotaSettingsPage");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Page");

dojo.declare("umc.modules._quota.QuotaSettingsPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	_grid: null,

	buildRendering: function() {
		this.inherited(arguments);

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Entries')
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
			moduleStore: this.getModuleStore('id', this.moduleID + '/partitions')
		});
		titlePane.addChild(this._grid);
	},

	PostMixInProperties: function() {
		this.inherited(arguments);

		this.headerText = this._('Filesystem quotas');
		this.helpText = this._('Set, unset and modify filesystem quota');
	}
});
