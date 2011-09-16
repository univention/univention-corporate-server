/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.PartitionPage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Text");

dojo.declare("umc.modules._quota.PartitionPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	moduleStore: null,
	partitionDevice: null,
	_form: null,
	_grid: null,
	_searchForm: null,

	buildRendering: function() {
		this.inherited(arguments);
		this.renderForm();
		this.renderGrid();

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Quota settings')
		});
		this.addChild(titlePane);
		titlePane.addChild(this._form);
		titlePane.addChild(this._searchForm);
		titlePane.addChild(this._grid);
	},

	postCreate: function() {
		this.inherited(arguments);
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

		var layout = [['mountPointText', 'mountPointValue', 'filesystemText', 'filesystemValue', 'optionsText', 'optionsValue']];
		//var layout = [['mountPointText', 'mountPointValue'], ['filesystemText', 'filesystemValue'], ['optionsText', 'optionsValue']];

		this._form = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			layout: layout
		});
	},

	renderGrid: function() {
		//
		// SearchForm
		//
		var widgets = [{
			type: 'TextBox',
			name: 'filter',
			value: '*',
			label: this._('User:')
		}];

		this._searchForm = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [['filter']],
			onSearch: dojo.hitch(this, function(data) {
				data.partitionDevice = this.partitionDevice;
				this._grid.filter(data);
			})
		});

		//
		// Grid
		//
		var actions = [{
			name: 'add',
			label: this._('Add'),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			isMultiAction: false
		}, {
			name: 'configure',
			label: this._('Configure'),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false
		}, {
			name: 'remove',
			label: this._('Remove quota settings'),
			iconClass: 'dijitIconDelete',
			isStandardAction: true,
			isMultiAction: true
		}];

		var columns = [{
			name: 'user',
			label: this._('User'),
			width: 'auto'
		}, {
			name: 'sizeLimitUsed',
			label: this._('Size used'),
			width: 'adjust'
		}, {
			name: 'sizeLimitSoft',
			label: this._('Soft'),
			width: 'adjust'
		}, {
			name: 'sizeLimitHard',
			label: this._('Hard'),
			width: 'adjust'
		}, {
			name: 'sizeLimitTime',
			label: this._('Grace'),
			width: 'adjust'
		}, {
			name: 'fileLimitUsed',
			label: this._('Files used'),
			width: 'adjust'
		}, {
			name: 'fileLimitSoft',
			label: this._('Soft'),
			width: 'adjust'
		}, {
			name: 'fileLimitHard',
			label: this._('Hard'),
			width: 'adjust'
		}, {
			name: 'fileLimitTime',
			label: this._('Grace'),
			width: 'adjust'
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			query: {
				filter: '*',
				partitionDevice: this.partitionDevice
			}
		});
	}
});
