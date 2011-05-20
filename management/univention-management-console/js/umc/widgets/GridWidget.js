/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.GridWidget");

dojo.require("dojo.string");
dojo.require("dojo.data.ItemFileWriteStore");
dojo.require("dijit.form.Button");
dojo.require("dijit.form.DropDownButton");
dojo.require("dijit.Menu");
dojo.require("dijit.layout.BorderContainer");
dojo.require("dojox.grid.EnhancedGrid");
dojo.require("dojox.grid.cells");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.tools");

dojo.declare("umc.widgets.GridWidget", dijit.layout.BorderContainer, {
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

	// idField: String
	//		Data field that represents a unique identifier for an object.
	idField: '',

	// umcpSearchCommand: String
	//		UMCP command for querying a listing of all items with optional 
	//		filter parameters.
	umcpSearchCommand: '',

	// umcpSetCommand: String
	//		UMCP command for saving data from the grid directly.
	umcpSetCommand: '',

	_store: null,

	'class': 'umcNoBorder',

	buildRendering: function() {
		this.inherited(arguments);
		
		// assertions
		umc.tools.assert(dojo.isArray(this.columns), 'The property columns needs to be defined for umc.widgets.GridWidget as an array.');

		// create an empty store
		this._store = new dojo.data.ItemFileWriteStore({ 
			data: {
				identifier: this.idField,
				label: this.idField,
				items: [] 
			}
		});

		// create the layout for the grid columns
		var gridColumns = [];
		var query = {};
		dojo.forEach(this.columns, function(icol) {
			umc.tools.assert(icol.name !== undefined && icol.label !== undefined, 'The definition of grid columns requires the properties \'name\' and \'label\'.');

			// set common properties
			var col = {
				field: icol.name,
				name: icol.label,
				width: 'auto',
				description: icol.description || '',
				editable: icol.editable === undefined || icol.editable
			};

			// set cell type
			if (dojo.isString(icol.type) && 'checkbox' == icol.type.toLowerCase()) {
				col.cellType = dojox.grid.cells.Bool;
			}

			// push column config into array
			gridColumns.push(col);

			// adapt the query object to show all elements
			query[icol.name] = '*';
		}, this);

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
			if (iaction.callback) {
				dojo.connect(item, 'onClick', this, function() {
					iaction.callback(this._contextItemID);
				});
			}
		}, this);

		// add an additional column for a drop-down button with context actions
		gridColumns.push({
			field: this.idField,
			name: ' ',
			width: '20px',
			editable: false,
			formatter: dojo.hitch(this, function(itemID) {
				// create an HTML image that contains the down-arrow
				var img = dojo.string.substitute('<img src="${src}" style="height: ${height};" class="${class}" />', {
					src: dojo.moduleUrl("dojo", "resources/blank.gif").toString(),
					height: '6px',
					'class': 'dijitArrowButtonInner umcDisplayNone'
				});
				return img;
			})
		});

		// create the grid
		this._grid = new dojox.grid.EnhancedGrid({
			//id: 'ucrVariables',
			region: 'center',
			query: query,
			queryOptions: { ignoreCase: true },
			structure: gridColumns,
			clientSort: true,
			store: this._store,
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

		dojo.connect(this._grid, 'onCellClick', dojo.hitch(this, function(evt) {
			if (gridColumns.length != evt.cellIndex) {
				return;
			}

			// save the ID of the current element
			var item = this._grid.getItem(evt.rowIndex);
			this._contextItemID = this._store.getValue(item, this.idField);

			// show popup
			var column = this._grid.getCell(gridColumns.length);
			var cellNode = column.getNode(evt.rowIndex);
			var popupInfo = dijit.popup.open({
				popup: contextMenu,
				parent: this._grid,
				around: cellNode,
				orient: {
					BR: 'TR',
					TR: 'BR'
				}
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
		}));

		// register event for showing/hiding the combo buttons
		dojo.connect(this._grid, 'onRowMouseOver', dojo.hitch(this, function(evt) {
			// query DOM node of image and show it
			dojo.query('img.dijitArrowButtonInner', evt.rowNode).removeClass('umcDisplayNone');
		}));
		dojo.connect(this._grid, 'onRowMouseOut', dojo.hitch(this, function(evt) {
			// query DOM node of image and hide it
			dojo.query('img.dijitArrowButtonInner', evt.rowNode).addClass('umcDisplayNone');
		}));

		// register events for hiding the menu popup
		var hidePopup = function(evt) {
			dijit.popup.close(contextMenu);
		};
		dojo.connect(this._grid.scroller, 'scroll', hidePopup);
		dojo.forEach(['onHeaderCellClick', 'onHeaderClick', 'onRowClick', 'onSelectionChanged'], 
			dojo.hitch(this, function(ievent) {
				dojo.connect(this._grid, ievent, hidePopup);
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

		var buttonsCfg = [];
		dojo.forEach(this.actions, function(iaction) {
			// make sure we get all standard actions
			if (true !== iaction.isStandardAction) {
				return;
			}

			// prepare the list of button config objects
			buttonsCfg.push(iaction);
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
		dojo.forEach(this.actions, function(iaction) {
			// create a new menu item
			var item = new dijit.MenuItem({
				label: iaction.label,
				onClick: iaction.callback,
				iconClass: iaction.iconClass
			});
			actionsMenu.addChild(item);

			// connect callback function
			if (iaction.callback) {
				dojo.connect(item, 'onClick', iaction.callback);
			}
		}, this);

		// create drop-down button
		toolBarRight.addChild(new dijit.form.DropDownButton({
			label: 'Alle Aktionen...',
			dropDown: actionsMenu
		}));
		
		/*// disable edit menu in case there is more than one item selected
		dojo.connect(this._grid, 'onSelectionChanged', dojo.hitch(this, function() {
			var nItems = this._grid.selection.getSelectedCount();
			this._selectMenuItems.edit.set('disabled', nItems > 1);
		}));*/

		// save internally for which row the cell context menu was opened
/*		dojo.connect(this._grid, 'onCellContextMenu', dojo.hitch(this, function(e) {
			var item = this._grid.getItem(e.rowIndex);
			this._contextVariable = this._store.getValue(item, 'key');
		}));*/

/*		// connect to row edits
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
		});*/

	},

	umcpSearch: function(/*Object*/ parameters) {
		// summary:
		//		Send off an UMCP query to the server for searching...
		// parameters: Object
		//		Parameter object that is passed to the UMCP command containing a
		//		dictionary of search parameters.

		umc.tools.assert(this.umcpSearchCommand, 'In order to query form data from the server, umcpSearchCommand needs to be specified.');

		// query data from server
		umc.tools.umcpCommand(this.umcpSearchCommand, parameters).then(dojo.hitch(this, function(data) {
			// create a new store and assign it to the grid
			this._store = new dojo.data.ItemFileWriteStore({ 
				data: {
					identifier: this.idField,
					label: this.idField,
					items: data._result
				}
			});
			this._grid.setStore(this._store);

			// fire event
			this.onUmcpSearchDone(true);
		}), dojo.hitch(this, function(error) {
			// fire event also in error case
			this.onUmcpSearchDone(false);
		}));
	},

/*	umcpSet: function() {
		// summary:
		//		Gather all form values and send them to the server via UMCP.
		//		For this, the field umcpSetCommand needs to be set.

		umc.tools.assert(this.umcpSetCommand, 'In order to query form data from the server, umcpGetCommand needs to be set');

		// sending the data to the server
		var values = this.gatherFormValues();
		umc.tools.umcpCommand(this.umcpSetCommand, values).then(dojo.hitch(this, function(data) {
			// fire event
			this.onUmcpSetDone(true);
		}), dojo.hitch(this, function(error) {
			// fore event also in error case
			this.onUmcpSetDone(false);
		}));
	},*/

	onUmcpSetDone: function() {
		// event stub
	},

	onUmcpSearchDone: function() {
		// event stub
	},

	getSelection: function() {
		// summary:
		//		Return the currently selected items.
		// returns:
		//		An array of id strings (as specified by idField).
		var items = this._grid.selection.getSelected();
		var vars = [];
		for (var iitem = 0; iitem < items.length; ++iitem) {
			vars.push(this._store.getValue(items[iitem], this.idField));
		}
		return vars; // String[]
	}

//	unsetVariable: function(/*Array*/ variable) {
//		// prepare the JSON object
//		var jsonObj = {
//			variable: variable
//		};
//
//		// send off the data
//		umc.tools.umcpCommand('ucr/unset', {
//			variable: variable
//		}).then(dojo.hitch(this, function(data, ioargs) {
//			this.reload();
//		}));
//	},

//	saveVariable: function(variable, value, xhrHandler, reload) {
//		// prepare the JSON object
//		var jsonObj = {};
//		dojo.setObject('variables.' + variable, value, jsonObj);
//
//		// send off the data
//		umc.tools.xhrPostJSON(
//			jsonObj, 
//			'/umcp/command/ucr/set', 
//			dojo.hitch(this, function(dataOrError, ioargs) {
//				// check the status
//				if (dojo.getObject('xhr.status', false, ioargs) == 200 && (reload === undefined || reload)) {
//					this.reload();
//				}
//
//				// eventually execute custom callback
//				if (xhrHandler) {
//					xhrHandler(dataOrError, ioargs);
//				}
//			})
//		);
//	}
});







