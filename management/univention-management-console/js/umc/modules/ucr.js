/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.ucr");

dojo.require("umc.modules.Module");
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
//dojo.require("umc.widgets.SearchWidget");
dojo.require("umc.widgets.FormWidget");
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
		
		this._form = new umc.widgets.FormWidget({
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

dojo.declare("umc.modules.ucr", umc.modules.Module, {
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

		// add search widget
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
			name: 'mask',
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
			name: 'search',
			value: '*',
			description: 'Suchbegriff nach dem gesucht werden soll',
			label: 'Suchbegriff'
		}];

		var buttons = [{
			name: 'submit',
			label: 'Suchen',
			callback: dojo.hitch(this, this.filter)
		}, {
			name: 'reset',
			label: 'Zurücksetzen'
		}];

		var layout = [
			[ 'category', '' ],
			[ 'mask', 'search' ]
		];

		this._searchWidget = new umc.widgets.FormWidget({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});
		this.addChild(this._searchWidget);

		//
		// create toolbar
		//

		// first create a container for grid and tool bar
		//var gridContainer = new dijit.layout.BorderContainer({
		//	region: 'center'
		//});
		//this.addChild(gridContainer);

		// create the toolbar container
		var toolBar = new umc.widgets.ContainerWidget({
			region: 'bottom',
			style: 'text-align: right',
			'class': 'umcNoBorder'
		});
		this.addChild(toolBar);

		// create 'edit' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Edit',
			iconClass: 'dijitIconEdit',
			onClick: dojo.hitch(this, function() {
				var vars = this.getSelectedVariables();
				if (vars.length) {
					this._detailDialog.loadVariable(vars[0]);
				}
			})
		}));

		// create 'add' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Add',
			iconClass: 'dijitIconNewTask',
			onClick: dojo.hitch(this, function() {
				this._detailDialog.newVariable();
			})
		}));

		// create 'delete' button
		toolBar.addChild(new dijit.form.Button({
			label: 'Delete',
			iconClass: 'dijitIconDelete',
			onClick: dojo.hitch(this, function() {
				var vars = this.getSelectedVariables();
				if (vars.length) {
					this.unsetVariable(vars[0]);
				}
			})
		}));

		//
		// create menues for grid
		//

		// menu for selected entries
		this._selectMenuItems = {};
		dojo.mixin(this._selectMenuItems, {
			edit: new dijit.MenuItem({
				label: 'Edit',
				iconClass: 'dijitIconEdit',
				onClick: dojo.hitch(this, function() {
					console.log('### onClick');
					console.log(arguments);
					var vars = this.getSelectedVariables();
					if (vars.length) {
						this._detailDialog.loadVariable(vars[0]);
					}
				})
			}),
			del: new dijit.MenuItem({
				label: 'Delete',
				iconClass: 'dijitIconDelete',
				onClick: dojo.hitch(this, function() {
					var vars = this.getSelectedVariables();
					if (vars.length) {
						this.unsetVariable(vars[0]);
					}
				})
			}),
			add: new dijit.MenuItem({
				label: 'Add',
				iconClass: 'dijitIconNewTask',
				onClick: dojo.hitch(this, function() {
					this._detailDialog.newVariable();
				})
			})
		});
	
		// put menu items together
		this._selectMenu = new dijit.Menu({ });
		this._selectMenu.addChild(this._selectMenuItems.edit);
		this._selectMenu.addChild(this._selectMenuItems.del);
		this._selectMenu.addChild(this._selectMenuItems.add);

		// menu for cells
		this._cellMenuItems = {};
		dojo.mixin(this._cellMenuItems, {
			edit: new dijit.MenuItem({
				label: 'Edit',
				iconClass: 'dijitIconEdit',
				onClick: dojo.hitch(this, function() {
					if (this._contextVariable) {
						this._detailDialog.loadVariable(this._contextVariable);
					}
				})
			}),
			del: new dijit.MenuItem({
				label: 'Delete',
				iconClass: 'dijitIconDelete',
				onClick: dojo.hitch(this, function() {
					if (this._contextVariable) {
						this.unsetVariable(this._contextVariable);
					}
				})
			}),
			add: new dijit.MenuItem({
				label: 'Add',
				iconClass: 'dijitIconNewTask',
				onClick: dojo.hitch(this, function() {
					this._detailDialog.newVariable();
				})
			})
		});

		// put menu items together
		this._cellMenu = new dijit.Menu({ });
		this._cellMenu.addChild(this._cellMenuItems.edit);
		this._cellMenu.addChild(this._cellMenuItems.del);
		this._cellMenu.addChild(this._cellMenuItems.add);

		//
		// create the grid
		//

		// create store
		this._store = new dojo.data.ItemFileWriteStore({ data: {items:[]} });
		var gridLayout = [{
			field: 'key',
			name: 'UCR-Variable',
			width: 'auto'
		},{
			field: 'value',
			name: 'Wert',
			width: 'auto',
			editable: true
		}];
		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			region: 'center',
			query: { key: '*', value: '*' },
			queryOptions: { ignoreCase: true },
			structure: gridLayout,
			clientSort: true,
			store: this._store,
			rowSelector: '2px',
			//sortFields: {
			//	attribute: 'variable',
			//	descending: true
			//},
			plugins : {
				menus:{ 
					cellMenu: this._cellMenu,
					selectedRegionMenu: this._selectMenu
				},
				indirectSelection: {
					headerSelector: true,
					name: 'Selection',
					width: '25px',
					styles: 'text-align: center;'
				}
			}
		});
		this._grid.setSortIndex(1);
		this.addChild(this._grid);

		// disable edit menu in case there is more than one item selected
		dojo.connect(this._grid, 'onSelectionChanged', dojo.hitch(this, function() {
			var nItems = this._grid.selection.getSelectedCount();
			this._selectMenuItems.edit.set('disabled', nItems > 1);
		}));

		// save internally for which row the cell context menu was opened
		dojo.connect(this._grid, 'onCellContextMenu', dojo.hitch(this, function(e) {
			var item = this._grid.getItem(e.rowIndex);
			this._contextVariable = this._store.getValue(item, 'key');
		}));

		// connect to row edits
		dojo.connect(this._grid, 'onApplyEdit', this, function(rowIndex) {
			// get the ucr variable and value of edited row
			var item = this._grid.getItem(rowIndex);
			var ucrVar = this._store.getValue(item, 'key');
			var ucrVal = this._store.getValue(item, 'value');
			
			// while saving, set module to standby
			this.standby(true);

			// save values
			this.saveVariable(ucrVar, ucrVal, dojo.hitch(this, function() {
				this.standby(false);
			}), false);
		});

		// create dialog for UCR variable details
		this._detailDialog = new umc.modules._ucrDetailDialog({});
		this._detailDialog.startup();

		// register to the onSubmit event of our dialog
		// in case a value has been updated, we need to refresh the grid
		dojo.connect(this._detailDialog, 'onSubmit', this, function(values) {
			// set the dialog on standby
			this._detailDialog.standby(true);

			// save UCR variable
			this.saveVariable(values.variable, values.value, dojo.hitch(this, function(data, ioargs) {
				// data is sent, stop standby mode
				this._detailDialog.standby(false);

				// only in case of success, close dialog
				if (200 == dojo.getObject('xhr.status', false, ioargs)) {
					this._detailDialog.hide();
				}
			}));
		});
	},

	getSelectedVariables: function() {
		var items = this._grid.selection.getSelected();
		var vars = [];
		for (var iitem = 0; iitem < items.length; ++iitem) {
			vars.push(this._store.getValue(items[iitem], 'key'));
		}
		console.log('### getSelectedVariables');
		console.log(vars);
		console.log(items);
		return vars;
	},

	filter: function(valMap) {
		console.log('### filter');
		console.log(valMap);
		this.standby(true);
		
		// query JSON data
		umc.tools.xhrPostJSON(
			{
				filter: valMap.search,
				key: valMap.mask,
				category: valMap.category
			},
			'/umcp/command/ucr/search',
			dojo.hitch(this, function(data, ioargs) {
				// we received the data from our search
				// create a new store and assign it to the grid
				if (data) {
					this._store = new dojo.data.ItemFileWriteStore({ 
						data: data._result
					});
					this._grid.setStore(this._store);
				}

				// stop standing-by mode
				this.standby(false);
			})
		);
	},

	reload: function() {
		this.filter(this._searchWidget.gatherFormValues());
	},

	unsetVariable: function(/*Array*/ variable) {
		// prepare the JSON object
		var jsonObj = {
			variable: variable
		};

		// send off the data
		umc.tools.umcpCommand('ucr/unset', {
			variable: variable
		}).then(dojo.hitch(this, function(data, ioargs) {
			this.reload();
		}));
	},

	saveVariable: function(variable, value, xhrHandler, reload) {
		// prepare the JSON object
		var jsonObj = {};
		dojo.setObject('variables.' + variable, value, jsonObj);

		// send off the data
		umc.tools.xhrPostJSON(
			jsonObj, 
			'/umcp/command/ucr/set', 
			dojo.hitch(this, function(dataOrError, ioargs) {
				// check the status
				if (dojo.getObject('xhr.status', false, ioargs) == 200 && (reload === undefined || reload)) {
					this.reload();
				}

				// eventually execute custom callback
				if (xhrHandler) {
					xhrHandler(dataOrError, ioargs);
				}
			})
		);
	}
});


