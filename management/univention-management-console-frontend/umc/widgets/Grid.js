/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Grid");

dojo.require("dijit.Menu");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.DropDownButton");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dojo.data.ObjectStore");
dojo.require("dojo.store.DataStore");
dojo.require("dojo.string");
dojo.require("dojox.data.ClientFilter");
dojo.require("dojox.grid.EnhancedGrid");
dojo.require("dojox.grid.cells");
dojo.require("dojox.grid.enhanced.plugins.IndirectSelection");
dojo.require("dojox.grid.enhanced.plugins.Menu");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.widgets.Grid", [ dijit.layout.BorderContainer, umc.i18n.Mixin, umc.widgets.StandbyMixin ], {
	// summary:
	//		Encapsulates a complex grid with store, UMCP commands and action buttons;
	//		offers easy access to select items etc.

	// actions: Object[]
	//		Array of config objects that specify the actions that are going to 
	//		be used in the grid. 
	//		TODO: explain isContextAction, isStandardAction, isMultiAction
	actions: null,

	// columns: Object[]
	//		Array of config objects that specify how the listing is rendered in
	//		the grid. Each element represents a column of the grid:
	//		'name': property that is going to be rendered in the column;
	//		'label': label of the column;
	//		'description': text for tooltip;
	//		'type': defaults to string, otherwise checkbox, icon, ...???;
	//		'editable': whether or not the field can be edited by the user;
	columns: null,

	// query: Object?
	//		The initial query for the data grid. If not specified no query will be executed 
	//		when the module has loaded.
	query: null,
	
	// moduleStore: umc.store.UmcpModuleStore
	//		Object store for module requests using UMCP commands.
	moduleStore: null,

	// use the framework wide translation file
	i18nClass: 'umc.app',

	'class': 'umcNoBorder',

	_contextItem: null,
	_contextItemID: null,

	_iconFormatter: function(valueField, iconField) {
		// summary:
		//		Generates a formatter functor for a given value and icon field.

		return dojo.hitch(this, function(value, rowIndex) {
			// get the iconNamae
			var item = this._grid.getItem(rowIndex);
			var iconName = this._dataStore.getValue(item, iconField);
			
			// create an HTML image that contains the down-arrow
			var html = dojo.string.substitute('<img src="/umc/images/icons/16x16/${icon}.png" height="${height}" width="${width}" style="float:left; margin-right: 5px" /> ${value}', {
				icon: iconName, //dojo.moduleUrl("dojo", "resources/blank.gif").toString(),
				height: '16px',
				width: '16px',
				value: value
			});
			return html;
		});
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		// encapsulate the object store into a old data store for the grid
		this._dataStore = new dojo.data.ObjectStore({
			objectStore: this.moduleStore
		});
	},

	buildRendering: function() {
		this.inherited(arguments);
		
		// assertions
		umc.tools.assert(dojo.isArray(this.columns), 'The property columns needs to be defined for umc.widgets.Grid as an array.');

		// create the layout for the grid columns
		var gridColumns = [];
		dojo.forEach(this.columns, function(icol) {
			umc.tools.assert(icol.name !== undefined && icol.label !== undefined, 'The definition of grid columns requires the properties \'name\' and \'label\'.');

			// set common properties
			var col = dojo.mixin({
				width: 'auto',
				editable: false,
				description: ''
			}, icol, {
				field: icol.name,
				name: icol.label
			});
			delete col.label;

			// set cell type
			if (dojo.isString(icol.type) && 'checkbox' == icol.type.toLowerCase()) {
				col.cellType = dojox.grid.cells.Bool;
			}

			// check for an icon
			if (icol.iconField) {
				// we need to specify a formatter
				col.formatter = this._iconFormatter(icol.name, icol.iconField);
			}

			// push column config into array
			gridColumns.push(col);

			// adapt the query object to show all elements
		}, this);

		// add an additional column for a drop-down button with context actions
		gridColumns.push({
			field: this.moduleStore.idProperty,
			name: ' ',
			width: '20px',
			editable: false,
			formatter: dojo.hitch(this, function() {
				// create an HTML image that contains the down-arrow
				var img = dojo.string.substitute('<img src="${src}" style="height: ${height};" class="${class}" />', {
					src: dojo.moduleUrl("dojo", "resources/blank.gif").toString(),
					height: '6px',
					'class': 'dijitArrowButtonInner umcDisplayNone'
				});
				return img;
			})
		});

		// create context menu
		var contextMenu = new dijit.Menu({ });
		dojo.forEach(this.actions, function(iaction) {
			// make sure we get all context actions
			if (false === iaction.isContextAction) {
				return;
			}

			// create a new menu item
			var item = new dijit.MenuItem({
				label: iaction.label,
				iconClass: iaction.iconClass
			});
			contextMenu.addChild(item);

			// connect callback function, pass the correct item ID
			this.connect(item, 'onClick', function() {
				dijit.popup.close(contextMenu);
				if (iaction.callback) {
					iaction.callback([this._contextItemID], [this._contextItem]);
				}
			});
		}, this);

		// create the grid
		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			store: this._dataStore,
			region: 'center',
			query: this.query,
			queryOptions: { ignoreCase: true },
			structure: gridColumns,
			rowSelector: '2px',
			plugins : {
				indirectSelection: {
					headerSelector: true,
					name: 'Selection',
					width: '25px',
					styles: 'text-align: center;'
				}
			},
			canSort: function(col) {
				// disable sorting for the last column
				return col != gridColumns.length + 1 && -col != gridColumns.length + 1;
			}
		});
		this._grid.setSortIndex(1);
		this.addChild(this._grid);

		// event handler for cell clicks...
		// -> handle context menus when clicked in the last column
		// -> call custom handler when clicked on any other cell
		this.connect(this._grid, 'onCellClick', function(evt) {
			if (gridColumns.length != evt.cellIndex) {
				// check for custom callback for this column
				var col = this.columns[evt.cellIndex - 1];
				if (col && col.callback) {
					// pass all values to the custom callback
					var values = this.getRowValues(evt.rowIndex);
					col.callback(values);
				}
				return;
			}

			// save the ID of the current element
			var item = this._grid.getItem(evt.rowIndex);
			this._contextItem = item;
			this._contextItemID = this._dataStore.getValue(item, this.moduleStore.idProperty);

			// show popup
			var column = this._grid.getCell(gridColumns.length);
			var cellNode = column.getNode(evt.rowIndex);
			var popupInfo = dijit.popup.open({
				popup: contextMenu,
				parent: this._grid,
				around: cellNode,
				onExecute: dijit.popup.close(contextMenu),
				onCancel: dijit.popup.close(contextMenu),
				orient: {
					BR: 'TR',
					TR: 'BR'
				}
			});
			contextMenu.focus();

			// make sure that the menu is being closed .. also for clicks outside the grid
			dojo.connect(contextMenu, '_onBlur', function(){
				dijit.popup.close(contextMenu);
			});
	
			// decorate popup element with our specific css class .. and remove obsolete css classes
			var posStr = 'Below';
			var notPosStr = 'Above';
			if ('TR' != popupInfo.corner) {
				posStr = 'Above';
				notPosStr = 'Below';
			}
			dojo.removeClass(contextMenu.containerNode.parentNode, 'umcGridRowMenu' + notPosStr);
			dojo.addClass(contextMenu.containerNode.parentNode, 'umcGridRowMenu' + posStr);
			dojo.addClass(contextMenu.domNode.parentNode, 'umcGridRowPopup' + posStr);
		});

		// register event for showing/hiding the combo buttons
		this.connect(this._grid, 'onRowMouseOver', function(evt) {
			// query DOM node of image and show it
			dojo.query('img.dijitArrowButtonInner', evt.rowNode).removeClass('umcDisplayNone');
		});
		this.connect(this._grid, 'onRowMouseOut', function(evt) {
			// query DOM node of image and hide it
			dojo.query('img.dijitArrowButtonInner', evt.rowNode).addClass('umcDisplayNone');
		});

		// register events for hiding the menu popup
		var hidePopup = function(evt) {
			dijit.popup.close(contextMenu);
		};
		this.connect(this._grid.scroller, 'scroll', hidePopup);
		dojo.forEach(['onHeaderCellClick', 'onHeaderClick', 'onRowClick', 'onSelectionChanged'], 
			dojo.hitch(this, function(ievent) {
				this.connect(this._grid, ievent, hidePopup);
			})
		);

		//
		// create toolbar
		//

		// create the toolbar containers
		var toolBar = new umc.widgets.ContainerWidget({
			region: 'bottom',
			'class': 'umcNoBorder'
		});
		this.addChild(toolBar);
		var toolBarLeft = new umc.widgets.ContainerWidget({
			region: 'bottom',
			style: 'float: left;',
			'class': 'umcNoBorder'
		});
		toolBar.addChild(toolBarLeft);
		var toolBarRight = new umc.widgets.ContainerWidget({
			region: 'bottom',
			style: 'float: right;',
			'class': 'umcNoBorder'
		});
		toolBar.addChild(toolBarRight);

		//
		// create buttons for standard actions
		//

		// call custom callback with selected values
		var actions = [];
		dojo.forEach(this.actions, dojo.hitch(this, function(iaction) {
			var jaction = iaction;
			if (iaction.callback) {
				jaction = dojo.mixin({}, iaction); // shallow copy

				// call custom callback with selected values
				jaction.callback = dojo.hitch(this, function() {
					iaction.callback(this.getSelectedIDs(), this.getSelectedItems());
				});
			}
			actions.push(jaction);
		}));

		// prepare buttons config list
		var buttonsCfg = [];
		dojo.forEach(actions, function(iaction) {
			// make sure we get all standard actions
			if (true === iaction.isStandardAction) {
				buttonsCfg.push(iaction);
			}

		}, this);
		var buttons = umc.tools.renderButtons(buttonsCfg);

		// add buttons to toolbar
		dojo.forEach(buttons._order, function(ibutton) {
			toolBarLeft.addChild(ibutton);
		}, this);

		//
		// create combo button for all actions
		//

		// create menu
		var actionsMenu = new dijit.Menu({});
		dojo.forEach(actions, function(iaction) {
			// make sure we only get non-standard actions
			if (true === iaction.isStandardAction) {
				return;
			}

			// create a new menu item
			var item = new dijit.MenuItem({
				label: iaction.label,
				iconClass: iaction.iconClass
			});
			if (iaction.callback) {
				item.onClick = iaction.callback;
			}
			actionsMenu.addChild(item);
		}, this);

		// create drop-down button if there are actions
		if (actionsMenu.hasChildren()) {
			toolBarRight.addChild(new dijit.form.DropDownButton({
				label: this._('More actions...'),
				dropDown: actionsMenu
			}));
		}

		//
		// register event handler
		//

		// in case of any changes in the module store, refresh the grid
		this.connect(this.moduleStore, 'onChange', function() {
			this.filter(this.query);
		});

		// standby animation when loading data
		this.connect(this._grid, "_onFetchComplete", function() {
			this.standby(false);
		});
		this.connect(this._grid, "_onFetchError", function() {
			this.standby(false);
		});

		// when a cell gets modified, save the changes directly back to the server
		this.connect(this._grid, 'onApplyCellEdit', dojo.hitch(this._dataStore, 'save'));
		
		/*// disable edit menu in case there is more than one item selected
		dojo.connect(this._grid, 'onSelectionChanged', dojo.hitch(this, function() {
			var nItems = this._grid.selection.getSelectedCount();
			this._selectMenuItems.edit.set('disabled', nItems > 1);
		}));*/

		// save internally for which row the cell context menu was opened
/*		dojo.connect(this._grid, 'onCellContextMenu', dojo.hitch(this, function(e) {
			var item = this._grid.getItem(e.rowIndex);
			this._contextVariable = this._dataStore.getValue(item, 'key');
		}));*/
	},

	filter: function(query) {
		// store the last query
		this.query = query;
		this.standby(true);
		this._grid.filter(query);
	},

	getSelectedItems: function() {
		// summary:
		//		Return the currently selected items.
		// returns:
		//		An array of dictionaries with all available properties of the selected items.
		return this._grid.selection.getSelected();
	},

	getSelectedIDs: function() {
		// summary:
		//		Return the currently selected items.
		// returns:
		//		An array of id strings (as specified by moduleStore.idProperty).
		var items = this._grid.selection.getSelected();
		var vars = [];
		for (var iitem = 0; iitem < items.length; ++iitem) {
			vars.push(this._dataStore.getValue(items[iitem], this.moduleStore.idProperty));
		}
		return vars; // String[]
	},

	getRowValues: function(rowIndex) {
		// summary:
		//		Convenience method to fetch all attributes of an item as dictionary.
		var values = {};
		var item = this._grid.getItem(rowIndex);
		dojo.forEach(this._dataStore.getAttributes(item), dojo.hitch(this, function(key) {
			values[key] = this._dataStore.getValue(item, key);
		}));
		return values;
	}
});


