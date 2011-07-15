/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.top");

//TODO: All modules needed?
dojo.require("dijit.layout.BorderContainer");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules.top", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_grid: null,
	_store: null,
	_searchWidget: null,
	_contextVariable: null,
	_layoutContainer: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._layoutContainer = new dijit.layout.BorderContainer({});
		this.addChild(this._layoutContainer);

		var actions = [{
            //TODO: Muss der name delete sein? (bzgl. submit Button)
			name: 'delete',
			label: this._('Kill processes'),
			iconClass: 'dijitIconDelete',
			callback: dojo.hitch(this, function(ids) {
                //TODO: Korrekt?
				this.moduleStore.multiRemove(ids);
			})
		}];

		var columns = [{
			name: 'user',
			label: this._('User'),
            width: '10%'
		}, {
			name: 'pid',
			label: this._('PID'),
            width: '10%'
		}, {
			name: 'cpu',
			label: this._('CPU'),
            width: '10%'
		}, {
			name: 'vsize',
			label: this._('Virtual size'),
            width: '10%'
		}, {
			name: 'rssize',
			label: this._('Resident set size'),
            width: '10%'
		}, {
			name: 'mem',
			label: this._('Memory in %'),
            width: '10%'
		}, {
			name: 'prog',
			label: this._('Program'),
            width: '10%'
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
                _dummy: 'dummy'
            }
		});
		this._layoutContainer.addChild(this._grid);

		var widgets = [{
			type: 'ComboBox',
			name: 'count',
			value: '50',
			label: this._('Number of processes'),
			staticValues: [
				{id: 'all', label: this._('All')},
				{id: '10', label: '10'},
				{id: '20', label: '20'},
				{id: '50', label: '50'}
			]
		}];

		var buttons = [{
			name: 'submit',
			label: this._('Reload'),
			callback: dojo.hitch(this, function() {
                this._grid.filter({ _dummy: 'dummy' });
			})
		}];

		this._searchWidget = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: [['count', 'submit']]
		});
		this._layoutContainer.addChild(this._searchWidget);

		this._layoutContainer.startup();
    }
});
