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
//dojo.require("umc.widgets.SearchForm");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules._ucrDetailDialog", [ dijit.Dialog, umc.widgets.StandbyMixin ], {
	//_fields: {},
	_form: null,
	//_langStore: null,
	//_grid: null,
	//_descriptionStore: null,

	postMixInProperties: function() {
		// call superclass' method
		this.inherited(arguments);

		dojo.mixin(this, {
			title: 'Detaildialog UCR-Variable',
			style: 'width: 450px'
		});
	},

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'variable',
			description: 'Name der UCR-Variable',
			label: 'UCR-Variable'
		}, {
			type: 'TextBox',
			name: 'value',
			description: 'Wert der UCR-Variable',
			label: 'Wert'
		}, {
			type: 'MultiSelect',
			name: 'categories',
			description: 'Kategorien, denen die Variable zugeordnet ist',
			label: 'Kategorien',
			umcpValues: 'ucr/categories'
		}];

		var buttons = [{
			name: 'submit',
			label: 'Speichern',
			callback: dojo.hitch(this, function() {
				this.standby(true);
				this._form.umcpSet();
			})
		}, {
			name: 'cancel',
			label: 'Abbrechen',
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

		/*// add a grid for descriptions
		this._descriptionStore = new dojo.data.ItemFileWriteStore({ data: {} }); 
		var layout = [{
			field: 'lang',
			name: 'Language',
			editable: true,
			width: '25%',
			cellType: dojox.grid.cells.Select,
			options: ['de', 'en'],
			formatter: function(val) {
				switch(val) {
					case 'de': 
						return 'German';
					case 'en': 
						return 'English';
				}
				return val;
			}
		},{
			field: 'description',
			name: 'Description',
			editable: true,
			width: '75%'
		}];
		this._grid = new dojox.grid.EnhancedGrid({
			label: 'Descriptions',
			query: { lang: '*', description: '*' },
			queryOptions: { ignoreCase: true },
			structure: layout,
			clientSort: true,
			store: this._descriptionStore,
			rowSelector: '2px',
			autoHeight: true
		});
		this._grid.setSortIndex(0);
		this._container.addChild(this._grid);

		// a little store for the different languages
		this._langStore = new dojo.data.ItemFileReadStore({
			data: {
				identifier: 'id',
				label: 'label',
				items: [{
					id: 'de',
					label: 'German'
				},{
					id: 'en',
					label: 'English'
				}]
			}
		});*/
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
		this._form._widgets.variable.set('disabled', false);

		// start standing-by mode
		this.standby(true);
		this.show();

		// start the query
		this._form.umcpGet({ variable: ucrVariable });
	},

//	_parseVariable: function(/*Object*/ obj) {
//		// update fields for variable and value
//		console.log(obj);
//		this._fields.variable.set('value', obj.variable || '');
//		this._fields.value.set('value', obj.value || '');
//
//		// categories: a string with elements separated by comma
//		var categoriesStr = dojo.getObject('categories', false, obj);
//		if (categoriesStr) {
//			this._fields.categories.set('value', categoriesStr.split(','));
//		}
//		else {
//			this._fields.categories.set('value', []);
//		}
//
//		/*// for the description, we need to create and add new widgets
//		// entries are of the form 'description[de]'
//		var r = /^description\[([^\)]*)\]$/;
//		var newData = {
//			identifier: 'lang',
//			label: 'lang',
//			items: [ ]
//		};
//		umc.tools.forIn(obj, function(el, ikey) {
//			// try to match the key
//			var m = r.exec(ikey);
//			if (m) {
//				// matched :) .. we found a new description
//				var lang = m[1];
//				newData.items.push({
//					lang: lang,
//					description: el
//				});
//			}
//		}, this);
//		
//		// create a new data store and assign it to the grid
//		this._descriptionStore = new dojo.data.ItemFileWriteStore({
//			data: newData
//		});
//		this._grid.setStore(this._descriptionStore);*/
//	},
	
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
			label: 'Hinzufügen',
			description: 'Hinzufügen einer neuen UCR-Variablen.',
			iconClass: 'dijitIconNewTask',
			isContextAction: false,
			isStandardAction: true,
			callback: dojo.hitch(this, function() {
				this._detailDialog.newVariable();
			})
		}, {
			name: 'edit',
			label: 'Bearbeiten',
			description: 'Löschen der ausgewählten UCR-Variablen.',
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isMultiAction: false,
			callback: dojo.hitch(this, function(vars) {
				if (vars.length) {
					this._detailDialog.loadVariable(vars[0]);
				}
			})
		}, {
			name: 'delete',
			label: 'Löschen',
			description: 'Löschen der ausgewählten UCR-Variablen.',
			iconClass: 'dijitIconDelete'
//			callback: dojo.hitch(this, function() {
//				var vars = this.getSelectedVariables();
//				if (vars.length) {
//					this.unsetVariable(vars[0]);
//				}
//			})
		}];

		// define grid columns
		var columns = [{
			name: 'variable',
			label: 'UCR-Variable',
			description: 'Eindeutiger Name der UCR-Variable',
			editable: false
		}, {
			name: 'value',
			label: 'Wert',
			description: 'Wert der UCR-Variable'
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
			description: 'Kategorie zu welcher die gesuchte Variable gehören soll',
			label: 'Kategorie',
			staticValues: {
				all: 'Alle'
			},
			umcpValues: 'ucr/categories'
		}, {
			type: 'ComboBox',
			name: 'key',
			value: 'all',
			description: 'Wo soll nach dem angegebenen Suchbegriff gesucht werden',
			label: 'Suchmaske',
			staticValues: {
				all: 'Alle',
				key: 'Variable',
				value: 'Wert',
				description: 'Beschreibung'
			}
		}, {
			type: 'TextBox',
			name: 'filter',
			value: '*',
			description: 'Suchbegriff nach dem gesucht werden soll',
			label: 'Suchbegriff'
		}];

		// define all buttons
		var buttons = [{
			name: 'submit',
			label: 'Suchen',
			callback: dojo.hitch(this._grid, 'umcpSearch')
		}, {
			name: 'reset',
			label: 'Zurücksetzen'
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

		// register to the onSubmit event of our dialog
		// in case a value has been updated, we need to refresh the grid
//		dojo.connect(this._detailDialog, 'onSubmit', this, function(values) {
//			// set the dialog on standby
//			this._detailDialog.standby(true);
//
//			// save UCR variable
//			this.saveVariable(values.variable, values.value, dojo.hitch(this, function(data, ioargs) {
//				// data is sent, stop standby mode
//				this._detailDialog.standby(false);
//
//				// only in case of success, close dialog
//				if (200 == dojo.getObject('xhr.status', false, ioargs)) {
//					this._detailDialog.hide();
//				}
//			}));
//		});
	}

//	reload: function() {
//		this.filter(this._searchWidget.gatherFormValues());
//	},

});


