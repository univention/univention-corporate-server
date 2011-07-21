/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.top");

dojo.require("dijit.layout.BorderContainer");
dojo.require("dojox.string.sprintf");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.SearchForm");

dojo.declare("umc.modules.top", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_grid: null,
	_store: null,
	_searchWidget: null,
	_contextVariable: null,
	_layoutContainer: null,

	i18nClass: 'umc.modules.top',
	idProperty: 'pid',

	killProcesses: function(signal, pids) {
		var params = {
			signal: signal,
			pid: pids
		};
		this.umcpCommand('top/kill', params).then(dojo.hitch(this, function(data) {
			umc.app.notify(this._('Processes killed successfully'));
		}));
	},

	buildRendering: function() {
		this.inherited(arguments);

		this._layoutContainer = new dijit.layout.BorderContainer({});
		this.addChild(this._layoutContainer);

		var actions = [{
			name: 'terminate',
			label: this._('Terminate processes'),
			iconClass: 'dijitIconDelete',
			callback: dojo.hitch(this, 'killProcesses', 'SIGTERM')
		}, {
			name: 'kill',
			label: this._('Kill processes'),
			iconClass: 'dijitIconDelete',
			callback: dojo.hitch(this, 'killProcesses', 'SIGKILL')
		}];

		var columns = [{
			name: 'user',
			label: this._('User'),
            width: '100px'
		}, {
			name: 'pid',
			label: this._('PID'),
            width: '75px'
		}, {
			name: 'cpu',
			label: this._('CPU (%)'),
            width: '50px'
		}, {
			name: 'vsize',
			label: this._('Virtual size (MB)'),
            width: '125px',
			formatter: function(value) {
				return dojox.string.sprintf('%.1f', value);
			}
		}, {
			name: 'rssize',
			label: this._('Resident set size (MB)'),
            width: '150px',
			formatter: function(value) {
				return dojox.string.sprintf('%.1f', value);
			}
		}, {
			name: 'mem',
			label: this._('Memory (%)'),
            width: '80px'
		}, {
			name: 'command',
			label: this._('Command'),
            width: 'auto'
		}];

		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			moduleStore: this.moduleStore,
			query: {
                category: 'all',
                filter: '*'
            }
		});
		this._layoutContainer.addChild(this._grid);

		var widgets = [{
			type: 'ComboBox',
			name: 'category',
			value: 'all',
			label: this._('Category'),
			staticValues: [
				{id: 'all', label: this._('All')},
				{id: 'user', label: this._('User')},
				{id: 'pid', label: this._('PID')},
				{id: 'command', label: this._('Command')}
			]
		}, {
			type: 'TextBox',
			name: 'filter',
			value: '*',
			label: this._('Keyword')
		}];

		this._searchWidget = new umc.widgets.SearchForm({
			region: 'top',
			widgets: widgets,
			layout: [['category', 'filter']],
			onSearch: dojo.hitch(this._grid, 'filter')
		});


		this._layoutContainer.addChild(this._searchWidget);

		this._layoutContainer.startup();
    }
});
