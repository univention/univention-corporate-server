/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.ucr");

dojo.require("umc.widgets.Module");
dojo.require("umc.tools");
dojo.require("dojo.data.ItemFileReadStore");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dojox.grid.EnhancedGrid");
//dojo.require("dojox.grid.DataGrid");
dojo.require("dojox.grid.enhanced.plugins.Menu");
dojo.require("dojox.grid.enhanced.plugins.IndirectSelection");
dojo.require("dojox.grid.cells");
dojo.require("dojox.layout.TableContainer");
dojo.require("dijit.Dialog");
dojo.require("dijit.Menu");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.TextBox");
dojo.require("dijit.form.Textarea");
dojo.require("dijit.form.ComboBox");
dojo.require("dojox.form.CheckedMultiSelect");
dojo.require("dojox.widget.Standby");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules._ucrDetailDialog", [ dijit.Dialog, umc.widgets.StandbyMixin ], {
	_form: null,

	postMixInProperties: function() {
		// call superclass' method
		this.inherited(arguments);

		dojo.mixin(this, {
			title: _( 'Edit UCR variable' ),
			style: 'width: 450px'
		});
	},

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'variable',
			description: _( 'Name of UCR variable' ),
			label: _( 'UCR variable' )
		}, {
			type: 'TextBox',
			name: 'value',
			description: _( 'Value of UCR variable' ),
			label: _( 'Value' )
		}, {
			type: 'MultiSelect',
			name: 'categories',
			description: _( 'Categories that the UCR variable is assoziated with' ),
			label: _( 'Categories' ),
			umcpValues: 'ucr/categories'
		}];

		var buttons = [{
			name: 'submit',
			label: _( 'Save' ),
			callback: dojo.hitch(this, function() {
				this.standby(true);
				this._form.umcpSet();
			})
		}, {
			//FIXME: Should be much simpled. The key name should be enough
			name: 'cancel',
			label: _( 'Cancel' ),
			callback: dojo.hitch(this, function() {
				this.hide();
			})
		}];

		var layout = [['variable'], ['value'], ['categories']];

		this._form = new umc.widgets.Form({
			style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			umcpGetCommand: 'ucr/get',
			umcpSetCommand: 'ucr/set',
			cols: 1
		}).placeAt(this.containerNode);

		// simple handler to disable standby mode
		dojo.connect(this._form, 'onUmcpGetDone', this, function() {
			this.standby(false);
		});
		dojo.connect(this._form, 'onUmcpSetDone', this, function() {
			this.standby(false);
		});

	},

	newVariable: function() {
		this._form._widgets.variable.set('disabled', false);
		var emptyValues = {};
		umc.tools.forIn(this._form.gatherFormValues(), function(ival, ikey) {
			emptyValues[ikey] = '';
		});
		this._form.setFormValues(emptyValues);
		this.show();
	},

	loadVariable: function(ucrVariable) {
		this._form._widgets.variable.set('disabled', true);

		// start standing-by mode
		this.standby(true);
		this.show();

		// start the query
		this._form.umcpGet({ variable: ucrVariable });
	},


	getValues: function() {
		// description:
		//		Collect a property map of all currently entered/selected values.

		return this._form.gatherFormValues();
	},

	onSubmit: function(values) {
		// stub for event handling
	}
});

dojo.declare("umc.modules.ucr", umc.widgets.Module, {
	// summary:
	//		Module for modifying and displaying UCR variables on the system.

	_grid: null,
	_store: null,
	_searchWidget: null,
	_detailDialog: null,
	_contextVariable: null,

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		//
		// add data grid
		//

		// define actions
		var actions = [{
			name: 'add',
			label: _( 'Add' ),
			description: _( 'Adding a new UCR variable' ),
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, function() {
				this._detailDialog.newVariable();
			})
		}, {
			name: 'edit',
			label: _( 'Edit' ),
			description: _( 'Setting the UCR variable, editing the categories and/or description' ),
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(vars) {
				if (vars.length) {
					this._detailDialog.loadVariable(vars[0].variable);
				}
			})
		}, {
			name: 'delete',
			label: _( 'Delete' ),
			description: _( 'Deleting the selected UCR variables' ),
			iconClass: 'dijitIconDelete'
		}];

		// define grid columns
		var columns = [{
			name: 'variable',
			label: _( 'UCR variable' ),
			description: _( 'Unique name of the UCR variable' ),
			editable: false
		}, {
			name: 'value',
			label: 'Wert',
			description: _( 'Value of the UCR variable' )
		}];

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			idField: 'variable',
			umcpSearchCommand: 'ucr/search',
			umcpSetCommand: 'ucr/set'
		});
		this.addChild(this._grid);

		//
		// add search widget
		//

		// define the different search widgets
		var widgets = [{
			type: 'ComboBox',
			name: 'category',
			value: 'all',
			description: _( 'Category the UCR vriable should assoziated with' ),
			label: 'Kategorie',
			staticValues: {
				all: 'Alle'
			},
			umcpValues: 'ucr/categories'
		}, {
			type: 'ComboBox',
			name: 'key',
			value: 'all',
			description: _( 'Select the attribute of a UCR variable that should be search for the given keyword' ),
			label: _( 'Search attribute' ),
			staticValues: {
				all: _( 'All' ),
				key: _( 'Variable' ),
				value: _( 'Value' ),
				description: _( 'Description' )
			}
		}, {
			type: 'TextBox',
			name: 'filter',
			value: '*',
			description: _( 'Keyword that should be searched for in the selected attribute' ),
			label: _( 'Keyword' )
		}];

		// define all buttons
		var buttons = [{
			name: 'submit',
			label: _( 'Search' ),
			callback: dojo.hitch(this._grid, 'umcpSearch')
		}, {
			name: 'reset',
			label: _( 'Reset' )
		}];

		// define the search form layout
		var layout = [
			[ 'category', '' ],
			[ 'key', 'filter' ]
		];

		// generate the search widget
		this._searchWidget = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});
		this.addChild(this._searchWidget);

		// simple handler to enable/disable standby mode
		dojo.connect(this._grid, 'umcpSearch', this, function() {
			this.standby(true);
		});
		dojo.connect(this._grid, 'onUmcpSearchDone', this, function() {
			this.standby(false);
		});

		//
		// create dialog for UCR variable details
		//

		this._detailDialog = new umc.modules._ucrDetailDialog({});
		this._detailDialog.startup();

	}

});


