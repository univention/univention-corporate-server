/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.PartitionPage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");

dojo.declare("umc.modules._quota.PartitionPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	moduleStore: null,
	_form: null,
	_grid: null,
	_searchForm: null,

	buildRendering: function() {
		this.inherited(arguments);
		this.renderForm();
		this.renderGrid();
		this.startup();
	},

	renderForm: function() {
		var widgets = [{
			type: 'Text',
			name: 'mountPointText',
			content: this._('Mount point: ')
		}, {
			type: 'Text',
			name: 'mountPointValue',
			content: 'FIXME'
		}, {
			type: 'Text',
			name: 'filesystemText',
			content: this._('Filesystem: ')
		}, {
			type: 'Text',
			name: 'filesystemValue',
			content: 'FIXME'
		}, {
			type: 'Text',
			name: 'optionsText',
			content: this._('Options: ')
		}, {
			type: 'Text',
			name: 'optionsValue',
			content: 'FIXME'
		}];

		var layout = [['mountPointText', 'mountPointValue'], ['filesystemText', 'filesystemValue'], ['optionsText', 'optionsValue']];

		this._form = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			layout: layout
		});

		this.addChild(this._form);
	},

	renderGrid: function() {
		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Quota settings')
		});
		this.addChild(titlePane);

		//
		// SearchForm
		//
		var widgets = [{
			type: 'TextBox',
			name: 'filter',
			value: '*',
			label: this._('Keyword')
		}];

		this._searchForm = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [['filter']],
			onSearch: dojo.hitch(this._grid, 'filter')
		});

		titlePane.addChild(this._searchForm);

		//
		// Grid
		//
		var actions = [{
			name: 'configure',
			label: this._('Configure'),
			isStandardAction: true,
			isMultiAction: false
		}, {
			name: 'remove',
			label: this._('Remove quota settings'),
			isStandardAction: true,
			isMultiAction: true
		}];

		var columns = [{ // TODO
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
				filter: '*'
			}
		});

		titlePane.addChild(this._grid);
	}
});
