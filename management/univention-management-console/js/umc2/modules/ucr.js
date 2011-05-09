/*global console MyError dojo dojox dijit umc2 */

dojo.provide("umc2.modules.ucr");

dojo.require("umc2.modules.Module");
dojo.require("umc2.tools");
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
dojo.require("umc2.widgets.SearchWidget");
dojo.require("umc2.widgets.ContainerWidget");
dojo.require("umc2.widgets.ContainerForm");
dojo.require("umc2.widgets.StandbyMixin");

dojo.declare("umc2.modules._ucrDetailDialog", [ dijit.Dialog, umc2.widgets.StandbyMixin ], {
	_fields: {},
	_form: null,
	_langStore: null,
	_grid: null,
	_descriptionStore: null,
	_categoryStore: new dojo.data.ItemFileWriteStore({
		data: { 
			identifier: 'id',
			label: 'name',
			items: []
		} 
	}),

	postMixInProperties: function() {
		// call superclass' method
		this.inherited(arguments);

		dojo.mixin(this, {
			title: 'Edit UCR-Variable',
			style: 'width: 450px'
		});
	},

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		// embed layout container within a form-element
		this._form = new umc2.widgets.ContainerForm({
			region: 'bottom',
			onSubmit: dojo.hitch(this, function(evt) {
				dojo.stopEvent(evt);
				this.onSubmit(this.getValues());
			})
		}).placeAt(this.containerNode);

		// create a table container which contains all search elements
		this._container = new dojox.layout.TableContainer({
			cols: 1,
			showLabels: true,
			orientation: 'vert'
		});
		this._form.addChild(this._container);

		// key field
		this._fields.variable = new dijit.form.TextBox({
			//id: '',
			style: 'width: 100%',
			label: 'Variable',
			value: ''
		});
		this._container.addChild(this._fields.variable);

		// value field
		this._fields.value = new dijit.form.TextBox({
			//id: '',
			style: 'width: 100%',
			label: 'Value',
			value: ''
		});
		this._container.addChild(this._fields.value);

		// categories
		this._fields.categories = new dojox.form.CheckedMultiSelect({
			//id: '',
			style: 'width: 100%',
			label: 'Categories',
			multiple: true,
			size: 5,
			store: this._categoryStore
		});
		this._container.addChild(this._fields.categories);

		// add a grid for descriptions
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

		// add 'search' button
		var buttonContainer = new umc2.widgets.ContainerWidget({
			style: 'text-align: right; width: 100%'
		});
		this._container.addChild(buttonContainer);
		buttonContainer.addChild(new dijit.form.Button({
			label: 'Save',
			type: 'submit',
			'class': 'submitButton'
		}));
	
		// add 'cancel' button
		buttonContainer.addChild(new dijit.form.Button({
			label: 'Cancel',
			onClick: dojo.hitch(this, function() {
				this.hide();
			})
		}));

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
		});
	},

	newVariable: function() {
		// start standing-by mode
		this._fields.variable.set('disabled', false);
		this._parseVariable({});
		this.show();
	},

	loadVariable: function(ucrVariable) {
		this.inherited(arguments);

		// start standing-by mode
		this._fields.variable.set('disabled', true);
		this.standby(true);
		this.show();

		// query JSON data 
		umc2.tools.xhrPostJSON(
			{ variable: ucrVariable },
			'/umcp/command/ucr/get',
			dojo.hitch(this, function(data, ioargs) {
				// make sure that we got data
				if (200 != dojo.getObject('xhr.status', false, ioargs)) {
					return;
				}

				// stop standing-by mode
				this.standby(false);

				// put values into fields
				var obj = dojo.mixin(dojo.getObject('_result', false, data), {
					variable: dojo.getObject('_options.variable', false, data)
				});
				this._parseVariable(obj);

			})
		);
	},

	_parseVariable: function(/*Object*/ obj) {
		// update fields for variable and value
		console.log(obj);
		this._fields.variable.set('value', obj.variable || '');
		this._fields.value.set('value', obj.value || '');

		// categories: a string with elements separated by comma
		var categoriesStr = dojo.getObject('categories', false, obj);
		if (categoriesStr) {
			this._fields.categories.set('value', categoriesStr.split(','));
		}
		else {
			this._fields.categories.set('value', []);
		}

		// remove old temporary widgets
		dojo.forEach(this._tmpWidgets, dojo.hitch(this, function(iWidget) {
			this.removeChild(iWidget);
		}));
		this._tmpWidgets = [];

		// for the description, we need to create and add new widgets
		// entries are of the form 'description[de]'
		var r = /^description\[([^\)]*)\]$/;
		var newData = {
			identifier: 'lang',
			label: 'lang',
			items: [ ]
		};
		for (var key in obj) {
			// try to match the key
			var m = r.exec(key);
			if (m) {
				// matched :) .. we found a new descrption
				var lang = m[1];
				newData.items.push({
					lang: lang,
					description: obj[key]
				});
			}
		}
		
		// create a new data store and assign it to the grid
		this._descriptionStore = new dojo.data.ItemFileWriteStore({
			data: newData
		});
		this._grid.setStore(this._descriptionStore);
	},
	
	getValues: function() {
		// description:
		//		Collect a property map of all currently entered/selected values.
		var map = {};
		for (var ikey in this._fields) {
			var el = this._fields[ikey];
			if ('value' in el) {
				map[ikey] = el.get('value');
			}
		}
		return map; // Object
	},

	onSubmit: function(values) {
		// stub for event handling
	}
});

dojo.declare("umc2.modules.ucr", umc2.modules.Module, {
	// summary:
	//		Module for modifying and displaying UCR variables on the system.

	_grid: null,
	_store: null,
	_searchWidget: null,
	_detailDialog: null,
	_contextVariable: null,
	_categoryStore: new dojo.data.ItemFileWriteStore({
		//url: 'json/ucr_categories.json'
		data: { 
			identifier: 'id',
			label: 'name',
			items: [{
				id: 'all',
				name: 'All'
			}]
		} 
	}),

	/*_setCategoryStore: function(newStore) {
		console.log('### _setCategoryStore');
		dojo.forEach(['_searchWidget._formWidgets.category', '_detailDialog._fields.categories'], 
			dojo.hitch(this, function(ipath) {
				var widget = dojo.getObject(ipath, false, this);
				if (widget) {
					console.log('### ' + ipath);
					widget.set('store', newStore);
				}
			})
		);
	},*/

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);

		// add search widget
		this._searchWidget = new umc2.widgets.SearchWidget({
			fields: [
				{
					id: 'category',
					label: 'Category',
					//value: 'all',
					labelAttr: 'name',
					store: this._categoryStore
				},
				null,
				{
					id: 'mask',
					label: 'Search mask',
					labelAttr: 'text',
					store: new dojo.data.ItemFileReadStore({ data: {
						identifier: 'id',
						label: 'text',
						items: [
							{ id: 'all', text: 'Alle' },
							{ id: 'key', text: 'Variable' },
							{ id: 'value', text: 'Value' },
							{ id: 'description', text: 'Description' }
						]
					}})
				},
				{
					id: 'search',
					label: 'Search string',
					value: '*'
				}
			],
			onSubmit: dojo.hitch(this, this.filter)
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
		var toolBar = new umc2.widgets.ContainerWidget({
			region: 'bottom',
			style: 'text-align: right'
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
		var layout = [{
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
			structure: layout,
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
		this._detailDialog = new umc2.modules._ucrDetailDialog({});
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

		//
		// query categories from server 
		//

		umc2.tools.xhrPostJSON(
			{},
			'/umcp/command/ucr/categories',
			dojo.hitch(this, function(data, ioargs) {
				// make sure that we got data
				if (200 != dojo.getObject('xhr.status', false, ioargs)) {
					return;
				}

				// add categories as new items to the categories of the detail dialog 
				// and the search widget
				for (var ikey in data._result) {
					console.log('### adding: ' + ikey + ' ' + data._result[ikey].name.en);
					var newItem = {
						id: ikey,
						name: data._result[ikey].name.en
					};
					this._categoryStore.newItem(newItem);
					this._detailDialog._categoryStore.newItem(newItem);
				}

				// save changes
				this._categoryStore.save();
				this._detailDialog._categoryStore.save();

				/*console.log('### saving categories');
				this._categoryStore.save({
					onError: function(error) {
						console.log('### error: ' + error);
					},
					onComplete: function() {
						console.log('### success');
					}
				});
				this._categoryStore.close();*/

				// create the data store
				//var newStore = new dojo.data.ItemFileReadStore({ data: {
				//	identifier: 'id',
				//	label: 'label',
				//	items: newItems
				//}});

				// use the store for the search form and the detail dialog
				//this._setCategoryStore(newStore);
			})
		);

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
		this.standby(true);
		
		// query JSON data
		umc2.tools.xhrPostJSON(
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
		this.filter(this._searchWidget.getValues());
	},

	unsetVariable: function(/*Array*/ variable) {
		// prepare the JSON object
		var jsonObj = {
			variable: variable
		};

		// send off the data
		umc2.tools.xhrPostJSON(
			jsonObj,
			'/umcp/command/ucr/unset',
			dojo.hitch(this, function(data, ioargs) {
				// check the status
				if (200 == dojo.getObject('xhr.status', false, ioargs)) {
					this.reload();
				}
			})
		);
	},

	saveVariable: function(variable, value, xhrHandler, reload) {
		// prepare the JSON object
		var jsonObj = {};
		dojo.setObject('variables.' + variable, value, jsonObj);

		// send off the data
		umc2.tools.xhrPostJSON(
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


