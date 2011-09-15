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
dojo.require("umc.render");
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
	//		TODO: explain also the 'adjust' value for columns
	//		TODO: iconClass, label -> may be of type string or function
	//		      they are called either per item (with a dict as parameter) or
	//		      once as column caption (without any parameters)
	actions: null,

	// columns: Object[]
	//		Array of config objects that specify how the listing is rendered in
	//		the grid. Each element represents a column of the grid:
	//		'name': property that is going to be rendered in the column;
	//		'label': label of the column;
	//		'description': text for tooltip;
	//		'type': defaults to string, otherwise checkbox, icon, ...???;
	//		'editable': whether or not the field can be edited by the user;
	//		'canExecute': function that specifies whether an action can be excuted for
	//		              a particular item; the function receives a dict of all item
	//		              properties as parameter
	columns: null,

	// query: Object?
	//		The initial query for the data grid. If not specified no query will be executed
	//		when the module has loaded.
	query: null,

	// moduleStore: umc.store.UmcpModuleStore
	//		Object store for module requests using UMCP commands.
	moduleStore: null,

	// footerFormatter: Function?
	//		Function that is called with two parameters: the number of selected objects,
	//		total number of objects. The function is expected to return a string that
	//		will be displayed in the grid footer.
	footerFormatter: null,

	// use the framework wide translation file
	i18nClass: 'umc.app',

	// turn off gutters by default
	gutters: false,

	_contextItem: null,
	_contextItemID: null,
	_contextMenu: null,

	// temporary div elements to estimate width of text for columns
	_tmpCell: null,
	_tmpCellHeader: null,

	_footerCells: null,

	_footer: null,

	_footerLegend: null,

	_iconFormatter: function(valueField, iconField) {
		// summary:
		//		Generates a formatter functor for a given value and icon field.

		return dojo.hitch(this, function(value, rowIndex) {
			// get the iconNamae
			var item = this._grid.getItem(rowIndex);
			var iconName = this._dataStore.getValue(item, iconField);

			// create an HTML image that contains the icon
			var html = dojo.string.substitute('<img src="images/icons/16x16/${icon}.png" height="${height}" width="${width}" style="float:left; margin-right: 5px" /> ${value}', {
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

	_getHeaderWidth: function(text) {
		// if we do not have a temporary cell yet, create it
		if (!this._tmpCell && !this._tmpCellHeader) {
			this._tmpCellHeader = dojo.create('div', { 'class': 'dojoxGridHeader dijitOffScreen' });
			this._tmpCell = dojo.create('div', { 'class': 'dojoxGridCell' });
			dojo.place(this._tmpCell, this._tmpCellHeader);
			dojo.place(this._tmpCellHeader, dojo.body());
		}

		// set the text
		dojo.attr(this._tmpCell, 'innerHTML', text);

		// get the width of the cell
		return dojo.marginBox(this._tmpCell).w;
	},

	_getFooterCellWidths: function() {
		// query the widths of all columns
		var outerWidths = [];
		var innerWidths = [];
		dojo.query('th', this._grid.viewsHeaderNode).forEach(function(i) { 
			outerWidths.push(dojo.marginBox(i).w);
			innerWidths.push(dojo.contentBox(i).w);
		});

		// merge all data columns
		var footerWidths = [ innerWidths[0] + 2 ];
		var i;
		for (i = 1; i < outerWidths.length; ++i) {
			if (i < this.columns.length + 1) {
				footerWidths[0] += outerWidths[i];
			}
			else {
				footerWidths.push(innerWidths[i]);
			}
		}
		return footerWidths;
	},

	_setColumnsAttr: function ( value ) {
		this.columns = value;
		if ( this._grid === undefined ) {
			console.log( 'Grid: grid not yet defined' );
			return;
		}

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

			// check whether the width shall be computed automatically
			if ('adjust' == col.width) {
				col.width = (this._getHeaderWidth(col.name) + 18) + 'px';
			}

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

		// add additional columns for standard actions
		dojo.forEach(this.actions, function(iaction) {
			// get all standard context actions
			if (!(iaction.isStandardAction && (false !== iaction.isContextAction))) {
				return;
			}
			var ilabel = dojo.isFunction(iaction.label) ? iaction.label() : iaction.label;
			gridColumns.push({
				field: this.moduleStore.idProperty,
				name: ilabel,
				width: this._getHeaderWidth(ilabel) + 'px',
				description: iaction.description,
				editable: false,
				formatter: dojo.hitch(this, function(key, rowIndex) {
					// do not show buttons in case the row is disabled
					if (this._grid.rowSelectCell.disabled(rowIndex)) {
						return '';
					}

					// get icon and label (these properties may be functions)
					var item = this._grid.getItem(rowIndex);
					var iiconClass = dojo.isFunction(iaction.iconClass) ? iaction.iconClass(item) : iaction.iconClass;
					var ilabel = dojo.isFunction(iaction.label) ? iaction.label(item) : iaction.label;

					// by default only create a button with icon
					var props = { iconClass: iiconClass };
					if (!props.iconClass) {
						// no icon is set, set a label instead
						props = { label: ilabel };
					}

					// add callback handler
					if (iaction.callback) {
						props.onClick = dojo.hitch(this, function() {
							iaction.callback([key], [item]);
						});
					}

					// call canExecute to make sure the action can be executed
					if (iaction.canExecute && !iaction.canExecute(item)) {
						// the action cannot be executed... return an empty string
						return '';
					}

					// return final button
					return new dijit.form.Button(props);
				})
			});
		}, this);

		// add additional column for all other actions
		var tmpActions = dojo.filter(this.actions, function(iaction) {
			return !iaction.isStandardAction && (false !== iaction.isContextAction);
		});
		if (tmpActions.length) {
			gridColumns.push({
				field: this.moduleStore.idProperty,
				name: this._('More actions'),
				width: this._getHeaderWidth(this._('More actions')) + 'px',
				editable: false,
				formatter: dojo.hitch(this, function(key, rowIndex) {
					// do not show buttons in case the row is disabled
					if (this._grid.rowSelectCell.disabled(rowIndex)) {
						return '';
					}

					// get corresponding item
					var item = this._grid.getItem(rowIndex);

					// create context menu
					var menu = dijit.Menu({});
					dojo.forEach(tmpActions, function(iaction) {
						// call canExecute to make sure the action can be executed
						if (iaction.canExecute && !iaction.canExecute(item)) {
							// the action cannot be executed... return an empty string
							return true;
						}

						// get icon and label (these properties may be functions)
						var iiconClass = dojo.isFunction(iaction.iconClass) ? iaction.iconClass(item) : iaction.iconClass;
						var ilabel = dojo.isFunction(iaction.label) ? iaction.label(item) : iaction.label;

						// add the menu entry
						menu.addChild(new dijit.MenuItem({
							label: ilabel,
							iconClass: iiconClass,
							onClick: dojo.hitch(this, function() {
								if (iaction.callback) {
									iaction.callback([key], [item]);
								}
							})
						}));
					}, this);

					// we only need to display the drop-down button if it is populated
					if (0 === menu.getChildren().length) {
						return '';
					}

					// by default only create a button with icon
					return new dijit.form.DropDownButton({
						label: this._('More...'),
						dropDown: menu
					});
				})
			});
		}

		// set new grid structure
		this._grid.setStructure( gridColumns );
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create right-click context menu
		this._contextMenu = new dijit.Menu({});
		dojo.forEach(this.actions, function(iaction) {
			// make sure we get all context actions
			if (false === iaction.isContextAction) {
				return;
			}

			// get icon and label (these properties may be functions)
			var iiconClass = dojo.isFunction(iaction.iconClass) ? iaction.iconClass() : iaction.iconClass;
			var ilabel = dojo.isFunction(iaction.label) ? iaction.label() : iaction.label;

			// create a new menu item
			var item = new dijit.MenuItem({
				label: ilabel,
				iconClass: iiconClass,
				onClick: dojo.hitch(this, function() {
					if (iaction.callback) {
						iaction.callback([this._contextItemID], [this._contextItem]);
					}
				}),
				_action: iaction
			});
			this._contextMenu.addChild(item);
		}, this);

		// create the grid
		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			store: this._dataStore,
			region: 'center',
			query: this.query,
			queryOptions: { ignoreCase: true },
			//rowSelector: '2px',
			'class': 'umcGrid',
			plugins : {
				indirectSelection: {
					headerSelector: true,
					name: 'Selection',
					width: '25px',
					styles: 'text-align: center;'
				},
				menus: {
					rowMenu: this._contextMenu
				}
			},
			canSort: dojo.hitch(this, function(col) {
				// disable sorting for the action columns
				return Math.abs(col) - 2 < this.columns.length && Math.abs(col) - 2 >= 0;
			})
		});
		this._setColumnsAttr( this.columns );
		this._grid.setSortIndex(1);
		this.addChild(this._grid);

		//
		// create toolbar
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

		// render buttons
		var buttonsCfg = [];
		dojo.forEach(actions, function(iaction) {
			// make sure we get all standard actions
			if (false === iaction.isContextAction) {
				buttonsCfg.push(iaction);
			}

		}, this);
		var buttons = umc.render.buttons(buttonsCfg);

		// add the toolbar to the bottom of the widget
		var toolBar = new umc.widgets.ContainerWidget({
			region: 'bottom',
			'class': 'umcGridToolBar'
		});
		this.addChild(toolBar);

		// add buttons to toolbar
		dojo.forEach(buttons._order, function(ibutton) {
			toolBar.addChild(ibutton);
		});

		//
		// create combo button for all actions
		//

		// add a footer for the grid
		this._footer = new umc.widgets.ContainerWidget({
			region: 'bottom',
			'class': 'umcGridFooter'
		});
		this.addChild(this._footer);

		// connect to layout() and adjust widths of the footer cells
		this.connect(this._grid, '_resize', '_updateFooter');

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
			this._grid.selection.clear();
			this._updateFooterContent();
		});
		this.connect(this._grid, "_onFetchError", function() {
			this.standby(false);
			this._grid.selection.clear();
			this._updateFooterContent();
		});

		// when a cell gets modified, save the changes directly back to the server
		this.connect(this._grid, 'onApplyCellEdit', dojo.hitch(this._dataStore, 'save'));

		// disable edit menu in case there is more than one item selected
		this.connect(this._grid, 'onSelectionChanged', '_updateFooterContent');

		/*// disable edit menu in case there is more than one item selected
		this.connect(this._grid, 'onSelectionChanged', function() {
			var nItems = this._grid.selection.getSelectedCount();
			this._selectMenuItems.edit.set('disabled', nItems > 1);
		});*/

		// save internally for which row the cell context menu was opened and when 
		// -> handle context menus when clicked in the last column
		// -> call custom handler when clicked on any other cell
		this.connect(this._grid, 'onCellContextMenu', '_updateContextItem');
	},

	_updateFooterContent: function() {
		var nItems = this._grid.selection.getSelectedCount();
		var nItemsTotal = this._grid.rowCount;
		var msg = '';
		if (dojo.isFunction(this.footerFormatter)) {
			msg = this.footerFormatter(nItems, nItemsTotal);
		}
		else {
			var msg = this._('%d objects of %d selected', nItems, nItemsTotal);
			if (0 == nItemsTotal) {
				msg = this._('No objects could be found');
			}
			else if (1 == nItems) {
				msg = this._('1 object of %d selected', nItemsTotal);
			}
		}
		this._footerLegend.set('content', msg);
	},

	_updateContextItem: function(evt) {
		// save the ID of the current element
		var item = this._grid.getItem(evt.rowIndex);
		this._contextItem = item;
		this._contextItemID = this._dataStore.getValue(item, this.moduleStore.idProperty);

		// in case the row is disabled, or in case the action cannot be executed,
		// disable the context menu items
		var rowDisabled = this._grid.rowSelectCell.disabled(evt.rowIndex);
		dojo.forEach(this._contextMenu.getChildren(), function(iMenuItem, i) {
			var iaction = iMenuItem._action;
			var idisabled = rowDisabled || (iaction.canExecute && !iaction.canExecute(item));
			var iiconClass = dojo.isFunction(iaction.iconClass) ? iaction.iconClass(item) : iaction.iconClass;
			var ilabel = dojo.isFunction(iaction.label) ? iaction.label(item) : iaction.label;
			iMenuItem.set('disabled', idisabled);
			iMenuItem.set('label', ilabel);
			iMenuItem.set('iconClass', iiconClass);
		}, this);
	},

	_createFooter: function() {
		// make sure that the footer has not already been created
		if (this._footerCells) {
			return;
		}

		// make sure we have sensible values for the cell widths (i.e., > 0)
		// this method may be called when the grid has not been rendered yet
		var footerCellWidths = this._getFooterCellWidths();
		var width = 0;
		dojo.forEach(footerCellWidths, function(i) {
			width += i;
		});
		if (!width) {
			return false;
		}

		// add one div per footer element
		this._footerCells = [];
		dojo.forEach(footerCellWidths, function(iwidth) {
			// use display:inline-block; we need a hack for IE7 here, see:
			//   http://robertnyman.com/2010/02/24/css-display-inline-block-why-it-rocks-and-why-it-sucks/
			var cell = new umc.widgets.ContainerWidget({
				style: 'display:inline-block; padding: 0px 5px; vertical-align:top; zoom:1; *display:inline; height:auto;' // width:' + iwidth + 'px;'
			});
			this._footerCells.push(cell);
		}, this);

		// add a legend that states how many objects are currently selected
		this._footerLegend = new umc.widgets.Text({
			content: this._('No object selected')
		});
		this._footerCells[0].addChild(this._footerLegend);

		var i = 1;
		dojo.forEach(this.actions, function(iaction) {
			// get all standard context actions
			if (!(iaction.isStandardAction && (false !== iaction.isContextAction))) {
				return;
			}

			// only add action if it is a multi action
			if (iaction.isMultiAction) {
				// get icon and label (these properties may be functions)
				var iiconClass = dojo.isFunction(iaction.iconClass) ? iaction.iconClass() : iaction.iconClass;
				var ilabel = dojo.isFunction(iaction.label) ? iaction.label() : iaction.label;

				// by default only create a button with icon
				var props = { iconClass: iiconClass };
				if (!props.iconClass) {
					// no icon is set, set a label instead
					props = { label: ilabel };
				}

				// add callback handler
				if (iaction.callback) {
					props.onClick = dojo.hitch(this, function() {
						iaction.callback(this.getSelectedIDs(), this.getSelectedItems());
					});
				}

				// return final button
				if (! this._footerCells[i]) {
					console.log("WARNING: no footer cell: " + i);
				}
				else {
					this._footerCells[i].addChild(new dijit.form.Button(props));
				}
			}

			// increment counter
			++i;
		}, this);

		// add remaining actions to a combo button
		var tmpActions = dojo.filter(this.actions, function(iaction) {
			return !iaction.isStandardAction && (false !== iaction.isContextAction) && iaction.isMultiAction;
		});
		if (tmpActions.length) {
			var moreActionsMenu = dijit.Menu({});
			dojo.forEach(tmpActions, function(iaction) {
				// get icon and label (these properties may be functions)
				var iiconClass = dojo.isFunction(iaction.iconClass) ? iaction.iconClass() : iaction.iconClass;
				var ilabel = dojo.isFunction(iaction.label) ? iaction.label() : iaction.label;

				// create menu entry
				moreActionsMenu.addChild(new dijit.MenuItem({
					label: ilabel,
					iconClass: iiconClass,
					onClick: dojo.hitch(this, function() {
						if (iaction.callback) {
							iaction.callback([this._contextItemID], [this._contextItem]);
						}
					})
				}));
			});

			if (!this._footerCells[i]) {
				console.log("WARNING: no footer cell: " + i);
			}
			else {
				this._footerCells[i].addChild(new dijit.form.DropDownButton({
					label: this._('More...'),
					dropDown: moreActionsMenu
				}));
			}
		}

		dojo.forEach(this._footerCells, function(icell) {
			this._footer.addChild(icell);
		}, this);
		this._footer.startup();

		// redo the layout since we added elements
		this.layout();

		return true;
	},

	_updateFooter: function() {
		// try to create the footer if it does not already exist
		if (!this._footerCells) {
			var success = this._createFooter();
			if (!success) {
				return;
			}
		}
		
		// adjust the margin of the first cell in order to align correctly
		var margin = dojo.position(dojo.query('th', this._grid.viewsHeaderNode)[0]).x;
		margin -= dojo.position(this._grid.domNode).x;
		dojo.style(this._footerCells[0].domNode, 'margin-left', margin + 'px');

		// update footer cell widths
		dojo.forEach(this._getFooterCellWidths(), function(iwidth, i) {
			dojo.contentBox(this._footerCells[i].containerNode, { w: iwidth });
		}, this);
	},

	unitialize: function() {
		// remove the temporary cell from the DOM
		if (this._tmpCellHeader) {
			dojo.destroy(this._tmpCellHeader);
		}
		if (this._tmpCell) {
			dojo.destroy(this._tmpCell);
		}
	},

	filter: function(query) {
		// store the last query
		this.query = query;
		this.standby(true);
		this._grid.filter(query);
		this.layout();
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


