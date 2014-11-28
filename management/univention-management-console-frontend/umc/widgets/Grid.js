/*
 * Copyright 2011-2014 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global define require setTimeout clearTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/_base/window",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/topic",
	"dojo/aspect",
	"dojo/on",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"dojo/data/ObjectStore",
	"dojox/grid/EnhancedGrid",
	"dojox/grid/cells",
	"./Button",
	"./Text",
	"./ContainerWidget",
	"./StandbyMixin",
	"./Tooltip",
	"./_RegisterOnShowMixin",
	"../tools",
	"../render",
	"../i18n!",
	"dojox/grid/enhanced/plugins/IndirectSelection",
	"dojox/grid/enhanced/plugins/Menu"
], function(declare, lang, array, kernel, win, construct, attr, geometry, style, domClass,
		topic, aspect, on, Menu, MenuItem, DropDownButton,
		ObjectStore, EnhancedGrid, cells, Button, Text, ContainerWidget,
		StandbyMixin, Tooltip, _RegisterOnShowMixin, tools, render, _) {

	// disable Grid search with different starting points, as the results are loaded
	// only once entirely (see Bug #25476)
	var _Grid = declare([EnhancedGrid], {
		_fetch: function(start, isRender) {
			// force start=0
			arguments[0] = 0;
			this.inherited(arguments);
		},

		createView: function() {
			// workaround for FF:
			// if clicking into the last column, it might happen that the scrollbox
			// scrolls to the left such that the checkbox of the very first column
			// are moved half outside of the grid's visible area. This workaround makes
			// sure that horizontal scroll position is always 0 if via CSS horizontal
			// scrolling is disabled (i.e., overflow-x: hidden).
			var view = this.inherited(arguments);
			view.own(on(view.scrollboxNode, 'scroll', function(evt) {
				if (view.scrollboxNode.scrollLeft != 0 && style.get(view.scrollboxNode, 'overflowX') == 'hidden') {
					view.scrollboxNode.scrollLeft = 0;
				}
			}));
			return view;
		}
	});

	var _DropDownButton = declare([DropDownButton], {
		_onClick: function(evt) {
			// dont propagate any event here - otherwise dropDown gets closed.
			// this has something to do with the dropdown losing focus in favor
			// of the underlying td-node. it triggers _HasDropDown's _onBlur
			this.inherited(arguments);
			evt.stopPropagation();
		}
	});

	return declare("umc.widgets.Grid", [ContainerWidget, StandbyMixin, _RegisterOnShowMixin], {
		// summary:
		//		Encapsulates a complex grid with store, UMCP commands and action buttons;
		//		offers easy access to select items etc.

		// actions: Object[]
		//		Array of config objects that specify the actions that are going to
		//		be used in the grid.
		//		'canExecute': function that specifies whether an action can be excuted for
		//		              a particular item; the function receives a dict of all item
		//		              properties as parameter
		//		'tooltipClass': specifies a different tooltip class than umc/widgets/Tooltip
		//		'isContextAction': specifies that the action requires a selection
		//		'isStandardAction': specifies whether the action is displayed as own button or in the "more" menu
		//		'isMultiAction': specifies whether this action can be executed for multiple items
		//		'enablingMode': for multi actions; 'all' (default value) will require all selected items
		//		                to be executable, 'some' only requires at least one item in the selection
		//		                to be executable
		//		TODO: explain also the 'adjust' value for columns
		//		TODO: iconClass, label -> may be of type string or function
		//		      they are called either per item (with a dict as parameter) or
		//		      once as column caption (without any parameters)
		actions: [],

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

		// moduleStore: store.UmcpModuleStore
		//		Object store for module requests using UMCP commands.
		moduleStore: null,

		// footerFormatter: Function?
		//		Function that is called with two parameters: the number of selected objects,
		//		total number of objects. The function is expected to return a string that
		//		will be displayed in the grid footer.
		footerFormatter: null,

		// sortIndex: Number
		//		Controls which column is used for default sorting (values < 0 indicated
		//		sorting in descending order)
		sortIndex: 1,

		// use the framework wide translation file
		i18nClass: 'umc.app',

		// turn an labels for action columns by default
		actionLabel: true,

		// turn off gutters by default
		gutters: false,

		// defaultAction: Function/String a default action that is executed
		//		when clicking on the column defined in defaultActionColumn (if set) or in the first column.
		defaultAction: 'edit',

		// defaultActionColumn:
		//
		//
		defaultActionColumn: '',

		// gridOptions: options for the inner grid
		gridOptions: null,

		baseClass: 'umcGrid',

		disabled: false,

		_contextMenu: null,

		// temporary div elements to estimate width of text for columns
		_tmpCell: null,
		_tmpCellHeader: null,

		// ContainerWidget that holds all buttons
		_toolbar: null,

		_header: null,
		_footer: null,

		_footerLegend: null,

		// internal list of all disabled items... when data has been loaded, we need to
		// disable these items again
		_disabledIDs: null,

		// internal flag in order to ignore the next onFetch events
		_ignoreNextFetch: false,

		_selectionChangeTimeout: null,

		_resizeDeferred: null,

		_iconFormatter: function(valueField, iconField) {
			// summary:
			//		Generates a formatter functor for a given value and icon field.

			return lang.hitch(this, function(value, rowIndex) {
				// get the iconNamae
				var item = this._grid.getItem(rowIndex);
				var iconName = this._dataStore.getValue(item, iconField);

				// create an HTML image that contains the icon
				var html = lang.replace('<img src="{url}/umc/icons/16x16/{icon}.png" height="{height}" width="{width}" style="float:left; margin-right: 5px" /> {value}', {
					icon: iconName, //dojo.moduleUrl("dojo", "resources/blank.gif").toString(),
					height: '16px',
					width: '16px',
					value: value,
					url: require.toUrl('dijit/themes')
				});
				return html;
			});
		},

		_parentModule: undefined,
		_parentModuleTries: 0,
		_publishPrefix: null,
		_getParentModule: function() {
			if (!this._parentModule && this._parentModuleTries < 5) {
				++this._parentModuleTries;
				this._parentModule = tools.getParentModule(this);
			}
			return this._parentModule;
		},

		_publishAction: function(action) {
			var mod = this._getParentModule();
			if (mod) {
				topic.publish('/umc/actions', mod.moduleID, mod.moduleFlavor, this._publishPrefix, 'grid', action);
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// encapsulate the object store into a old data store for the grid
			this._dataStore = new ObjectStore({
				objectStore: this.moduleStore
			});

			this._disabledIDs = {};
		},

		buildRendering: function() {
			this.inherited(arguments);

			// create right-click context menu
			this._contextMenu = new Menu({});
			this.own(this._contextMenu);

			// add a header for the grid
			this._header = new ContainerWidget({
				baseClass: 'umcGridHeader'
			});
			this.addChild(this._header);

			// create the grid
			this._grid = new _Grid(lang.mixin({
				store: this._dataStore,
				query: this.query,
				queryOptions: { ignoreCase: true },
				'class': 'umcDynamicHeight',
				rowsPerPage: 30,
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
				}/*,
				canSort: lang.hitch(this, function(col) {
					// disable sorting for the action columns
					return Math.abs(col) - 2 < this.columns.length && Math.abs(col) - 2 >= 0;
				})*/
			}, this.gridOptions || {}));

			// add a footer for the grid
			this._footer = new ContainerWidget({
				baseClass: 'umcGridFooter'
			});
			this._createFooter();

			// update columns and actions
			this.setColumnsAndActions(this.columns, this.actions);
			if (typeof this.sortIndex == "number") {
				this._grid.setSortIndex(Math.abs(this.sortIndex), this.sortIndex > 0);
			}

			this.addChild(this._grid);
			this.addChild(this._footer);

			//
			// register event handler
			//

			// in case of any changes in the module store, refresh the grid
			// FIXME: should not be needed anymore with Dojo 1.8
			if (this.moduleStore.on && this.moduleStore.onChange) {
				this.own(this.moduleStore.on('Change', lang.hitch(this, function() {
					this.filter(this.query);
				})));
			}

			this.own(aspect.after(this._grid, "_onFetchComplete", lang.hitch(this, '_onFetched', true)));
			this.own(aspect.after(this._grid, "_onFetchError", lang.hitch(this, '_onFetched', false)));

			this._grid.on('selectionChanged', lang.hitch(this, '_selectionChanged'));
			this._grid.on('cellContextMenu', lang.hitch(this, '_updateContextItem'));

			this._grid.on('rowClick', lang.hitch(this, '_onRowClick'));

			// make sure that we update the disabled items after sorting etc.
			this.own(aspect.after(this._grid, '_refresh', lang.hitch(this, '_updateDisabledItems')));
		},

		startup: function() {
			this.inherited(arguments);

			this._registerAtParentOnShowEvents(lang.hitch(this._grid, 'resize'));
			this.own(on(win.doc, 'resize', lang.hitch(this, '_handleResize')));
			this.own(on(kernel.global, 'resize', lang.hitch(this, '_handleResize')));
		},

		_handleResize: function() {
			if (this._resizeDeferred && !this._resizeDeferred.isFulfilled()) {
				this._resizeDeferred.cancel();
			}
			this._resizeDeferred = tools.defer(lang.hitch(this, function() {
				this._grid.resize();
			}), 200);
			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		setColumnsAndActions: function(columns, actions) {
			this._setActionsAttr(actions, false);
			this._setColumnsAttr(columns);
		},

		_setColumnsAttr: function (columns) {
			tools.assert(columns instanceof Array, 'The property columns needs to be defined for umc/widgets/Grid as an array.');
			this.columns = columns;

			if (!this._grid) {
				// grid not yet defined
				return;
			}

			// create the layout for the grid columns
			var gridColumns = array.map(columns, function(icol, colNum) {
				tools.assert(icol.name !== undefined && icol.label !== undefined, 'The definition of grid columns requires the properties \'name\' and \'label\'.');

				// set common properties
				var col = lang.mixin({
					width: 'auto',
					editable: false,
					description: ''
				}, icol, {
					field: icol.name,
					name: icol.label
				});
				delete col.label;

				// default action
				var defaultActionExists = this.defaultAction && (typeof this.defaultAction == "function" || array.indexOf(array.map(this.actions, function(iact) { return iact.name; }), this.defaultAction) !== -1);
				var isDefaultActionColumn = (!this.defaultActionColumn && colNum === 0) || (this.defaultActionColumn && col.name == this.defaultActionColumn);

				if (defaultActionExists && isDefaultActionColumn) {
					col.formatter = lang.hitch(this, function(value, rowIndex) {
						var item = this._grid.getItem(rowIndex);

						value = icol.formatter ? icol.formatter(value, rowIndex) : value;

						if (!this._getDefaultActionForItem(item)) {
							if (value && value.domNode) {
								this.own(value);
							}
							return value;
						}

						if (value && value.domNode) {
							var container = new ContainerWidget({
								baseClass: 'umcGridDefaultAction',
								'style': 'display: inline!important;'
							});
							container.addChild(value);
							this.own(container);
							return container;
						} else {
							return this.own(new Text({
								content: value,
								baseClass: 'umcGridDefaultAction',
								'style': 'display: inline!important;'
							}))[0];
						}
					});
				}

				// check whether the width shall be computed automatically
				if ('adjust' == col.width) {
					col.width = (this._getHeaderWidth(col.name) + 18) + 'px';
				}

				// set cell type
				if (typeof icol.type == "string" && 'checkbox' == icol.type.toLowerCase()) {
					col.cellType = cells.Bool;
				}

				// check for an icon
				if (icol.iconField) {
					// we need to specify a formatter
					col.formatter = this._iconFormatter(icol.name, icol.iconField);
				}

				return col;
			}, this);

			// set new grid structure
			this._grid.setStructure(gridColumns);
		},

		layout: function() {
			this.resize();
		},

		resize: function() {
			if (this._grid) {
				this._grid.resize();
			}
		},

		_getHeaderWidth: function(text) {
			// if we do not have a temporary cell yet, create it
			if (!this._tmpCell && !this._tmpCellHeader) {
				this._tmpCellHeader = construct.create('div', { 'class': 'dojoxGridHeader dijitOffScreen' });
				this._tmpCell = construct.create('div', { 'class': 'dojoxGridCell' });
				construct.place(this._tmpCell, this._tmpCellHeader);
				construct.place(this._tmpCellHeader, win.body());
			}

			// set the text
			attr.set(this._tmpCell, 'innerHTML', text);

			// get the width of the cell
			return geometry.getMarginBox(this._tmpCell).w;
		},

		_setActionsAttr: function(actions, /*Boolean?*/ doSetColumns) {
			tools.assert(actions instanceof Array, 'The property actions needs to be defined for umc/widgets/Grid as an array.');
			this.actions = actions;

			// clear old actions
			array.forEach([this._header, this._contextMenu], function(iobj) {
				array.forEach(iobj.getChildren(), function(ichild) {
					iobj.removeChild(ichild);
					ichild.destroyRecursive();
				}, this);
			}, this);
			delete this._contextMenu.focusedChild;

			this._setGlobalActions();
			this._setContextActions();

			domClass.toggle(this._header.domNode, 'dijitHidden', !this.actions.length);
			if (this._toolbar.getChildren().length) {
				this._header.addChild(this._toolbar);
			}
			this._header.addChild(this._contextActionsToolbar);
			style.set(this._contextActionsToolbar.domNode, 'visibility', 'hidden');

			// redraw the columns
			if (doSetColumns !== false) {
				this._setColumnsAttr(this.columns);
			}
		},

		_getContextActions: function() {
			return array.filter(this.actions, function(iaction) { return (false !== iaction.isContextAction); });
		},

		_setContextActions: function() {
			this._contextActionsToolbar = new ContainerWidget({ style: 'float: left' });
			this._contextActionsMenu = new Menu({});
			this.own(this._contextActionsToolbar);
			this.own(this._contextActionsMenu);

			array.forEach(this._getContextActions(), function(iaction) {
				var getCallback = lang.hitch(this, function(prefix) {
					if (!iaction.callback) {
						return {};
					}
					return {
						onClick: lang.hitch(this, function() {
							this._publishAction(prefix + iaction.name);
							var ids = this.getSelectedIDs();
							var items = this.getSelectedItems();
							if (iaction.enablingMode == 'some') {
								items = array.filter(items, function(iitem) {
									return typeof iaction.canExecute == "function" ? iaction.canExecute(iitem) : true;
								});
								ids = array.map(items, function(iitem) {
									return this._dataStore.getValue(iitem, this.moduleStore.idProperty);
								}, this);
							}
							iaction.callback(ids, items);
						})
					};
				});
				// get icon and label (these properties may be functions)
				var iiconClass = typeof iaction.iconClass == "function" ? iaction.iconClass() : iaction.iconClass;
				var ilabel = typeof iaction.label == "function" ? iaction.label() : iaction.label;

				var props = { iconClass: iiconClass, label: ilabel, _action: iaction };

				if (iaction.isStandardAction) {
					// add action to the context toolbar
					var btn = new Button(lang.mixin(props, getCallback(''), { iconClass: props.iconClass || 'umcIconNoIcon' }));
					if (iaction.description) {
						try {
						var idescription = typeof iaction.description == "function" ? iaction.description(undefined) : iaction.description;
						var tooltip = new (iaction.tooltipClass || Tooltip)({
							label: idescription,
							connectId: [btn.domNode]
						});
						if (iaction.onShowDescription) {
							tooltip = lang.mixin(tooltip, { onShow: function(target) { iaction.onShowDescription(target, undefined); }});
						}
						if (iaction.onHideDescription) {
							tooltip = lang.mixin(tooltip, { onHide: function() { iaction.onHideDescription(undefined); }});
						}
						btn.own(tooltip);
						} catch (error) {}
					}
					this._contextActionsToolbar.addChild(btn);
				} else {
					// add action to the more menu
					this._contextActionsMenu.addChild(new MenuItem(lang.mixin(props, getCallback('multi-'))));
				}

				// add action to the context menu
				this._contextMenu.addChild(new MenuItem(lang.mixin(props, getCallback('menu-'))));
			}, this);

			// add more menu to toolbar
			if (this._contextActionsMenu.getChildren().length) {
				this._contextActionsToolbar.addChild(new _DropDownButton({
					baseClass: _DropDownButton.prototype.baseClass + ' umcGridMoreMenu',
					iconClass: 'umcIconNoIcon',
					label: _('more'),
					dropDown: this._contextActionsMenu
				}));
			}
		},

		_getGlobalActions: function() {
			return array.filter(this.actions, function(iaction) { return (false === iaction.isContextAction); });
		},

		_setGlobalActions: function() {
			//
			// toolbar for global actions
			//

			// add a toolbar which contains all non-context actions
			this._toolbar = new ContainerWidget({
				style: 'float: left',
				baseClass: 'umcGridToolBar'
			});
			this.own(this._toolbar);

			var buttonsCfg = array.map(this._getGlobalActions(), function(iaction) {
				var jaction = iaction;
				if (iaction.callback) {
					jaction = lang.mixin({}, iaction); // shallow copy

					// call custom callback with selected values
					jaction.callback = lang.hitch(this, function() {
						this._publishAction(iaction.name);
						iaction.callback(this.getSelectedIDs(), this.getSelectedItems());
					});
				}
				return jaction;
			}, this);

			// render buttons
			var buttons = render.buttons(buttonsCfg);

			// add buttons to toolbar
			array.forEach(buttons.$order$, function(ibutton) {
				this._toolbar.addChild(ibutton);
				ibutton.on('click', lang.hitch(this, function() {
					this._publishAction(ibutton.name);
				}));
			}, this);
		},

		_onFetched: function(success) {
			// standby animation when loading data
			if (this._ignoreNextFetch) {
				this._ignoreNextFetch = false;
				return;
			}
			this.standby(false);
			this._grid.selection.clear();
			this._updateFooterContent();
			this._updateDisabledItems();
			this.onFilterDone(success);
			this._grid.resize();
		},

		_selectionChanged: function() {
			if (this._selectionChangeTimeout) {
				clearTimeout(this._selectionChangeTimeout);
			}

			this._selectionChangeTimeout = setTimeout(lang.hitch(this, function() {
				this._updateContextActions();

				this._updateFooterContent();
			}), 50);
		},

		_getContextActionItems: function() {
			return this._contextActionsToolbar.getChildren().concat(this._contextMenu.getChildren()).concat(this._contextActionsMenu.getChildren());
		},

		_updateContextActions: function() {
			var nItems = this._grid.selection.getSelectedCount();

			array.forEach(this._getContextActionItems(), function(item) {
				if ((item instanceof Button || item instanceof MenuItem) && item._action) {
					var enabled = nItems !== 0;
					if (nItems > 1) {
						// when more than 1 row is selected:
						// disable actions which are no multiactions
						enabled = item._action.isMultiAction;
					}
					// disable multiaction if one of the selected items can not be executed
					var enablingFunction = array.every;
					if (item._action.enablingMode == 'some') {
						enablingFunction = array.some;
					}
					enabled = enabled && enablingFunction(this.getSelectedItems(), function(iitem) { return item._action.canExecute ? item._action.canExecute(iitem) : true; });
					item.set('disabled', !enabled);
				}
			}, this);

			// don't show context actions if they are not available
			var visibility = nItems === 0 ? 'hidden' : 'visible';
			style.set(this._contextActionsToolbar.domNode, 'visibility', visibility);
		},

		_updateContextItem: function(evt) {
			// when opening the context menu...
			var rowDisabled = this._grid.rowSelectCell.disabled(evt.rowIndex);
			if (rowDisabled) {
				return;
			}

			var hasClickedOnDefaultAction = (evt.target != evt.cellNode);
			if (!this._grid.selection.isSelected(evt.rowIndex) || hasClickedOnDefaultAction) {
				this._grid.selection.select(evt.rowIndex);
			}
		},

		_onRowClick: function(evt) {
			if (evt.cellIndex === 0) {
				// the checkbox cell was pressed, this does already the wanted behavior
				return true;
			}

			var rowDisabled = this._grid.rowSelectCell.disabled(evt.rowIndex);
			if (rowDisabled) {
				// deselect disabled rows
				this._grid.selection.deselect(evt.rowIndex);
				return;
			}

			this._grid.selection.select(evt.rowIndex);

			var item = this._grid.getItem(evt.rowIndex);
			var identity = item[this.moduleStore.idProperty];

			var defaultAction = this._getDefaultActionForItem(item);
			var isDefaultActionColumn = ((!this.defaultActionColumn && evt.cellIndex === 1) || (this.defaultActionColumn && evt.cell.field == this.defaultActionColumn));
			var hasClickedOnDefaultAction = (evt.target != evt.cellNode);

			// execute default action or toggle selection
			if (defaultAction && isDefaultActionColumn && hasClickedOnDefaultAction) {
				this._publishAction('default-' + defaultAction.name);
				defaultAction.callback([identity], [item]);
			}
		},

		_getDefaultActionForItem: function(item) {
			// returns the default action for a specified item if the action exists and can be executed
			var identity = item[this.moduleStore.idProperty];
			var defaultAction = typeof this.defaultAction == "function" ?
				this.defaultAction([identity], [item]) : this.defaultAction;

			if (defaultAction) {
				var action;
				array.forEach(this.actions, function(iaction) {
					if (iaction.name == defaultAction) {
						action = iaction;
						return false;
					}
				}, this);
				if (action && action.callback) {
					var isExecutable = typeof action.canExecute == "function" ? action.canExecute(item) : true;
					if (isExecutable && !this.getDisabledItem(identity)) {
						return action;
					}
				}
			}
		},

		_disableAllItems: function(disable) {
			var items = this.getAllItems();
			disable = undefined === disable ? true : disable;
			array.forEach(items, lang.hitch(this, function(iitem) {
				var idx = this.getItemIndex(iitem[this.moduleStore.idProperty]);
				if (idx >= 0) {
					this._grid.rowSelectCell.setDisabled(idx, disable);
				}
			}));
			this._grid.render();
		},

		_setDisabledAttr: function(value) {
			this.disabled = value;

			// disable items
			this._disableAllItems(value);
			// re-disable explicitly disabled items
			this._updateDisabledItems();

			// disable all actions
			array.forEach(this._toolbar.getChildren().concat(this._contextActionsToolbar), lang.hitch(this, function(widget) {
				if (widget instanceof Button || widget instanceof _DropDownButton) {
					widget.set('disabled', value);
				}
			}));
		},

		_createFooter: function() {
			// add a legend that states how many objects are currently selected
			this._footerLegend = new Text({
				content: _('No object selected'),
				style: 'padding-left: 5px'
			});
			this._footer.addChild(this._footerLegend);

			this._footer.startup();

			// redo the layout since we added elements
			this.layout();

			return true;
		},

		_updateFooterContent: function() {
			var nItems = this._grid.selection.getSelectedCount();
			var nItemsTotal = this._grid.rowCount;
			var msg = '';
			if (typeof this.footerFormatter == "function") {
				msg = this.footerFormatter(nItems, nItemsTotal);
			}
			else {
				msg = _('%d entries of %d selected', nItems, nItemsTotal);
				if (0 === nItemsTotal) {
					msg = _('No entries could be found');
				}
				else if (1 == nItems) {
					msg = _('1 entry of %d selected', nItemsTotal);
				}
			}
			this._footerLegend.set('content', msg);
		},

		uninitialize: function() {
			// remove the temporary cell from the DOM
			if (this._tmpCellHeader) {
				construct.destroy(this._tmpCellHeader);
			}
			if (this._tmpCell) {
				construct.destroy(this._tmpCell);
			}
		},

		filter: function(query) {
			// store the last query
			this.query = query;
			this.standby(true);
			this._grid.filter(query);
			this.clearDisabledItems(false);
			this.layout();
		},

		getAllItems: function() {
			// summary:
			//		Returns a list of all items
			var items = [];
			var i;
			for (i = 0; i < this._grid.rowCount; i++) {
				items.push(this._grid.getItem(i));
			}
			return items;
		},

		getSelectedItems: function() {
			// summary:
			//		Return the currently selected items.
			//		Filters disabled items.
			// returns:
			//		An array of dictionaries with all available properties of the selected items.
			return array.filter(this._grid.selection.getSelected(), lang.hitch(this, function(item) {
				var rowDisabled = this._grid.rowSelectCell.disabled(this._grid.getItemIndex(item));
				return !rowDisabled;
			}));
		},

		getSelectedIDs: function() {
			// summary:
			//		Return the currently selected items.
			// returns:
			//		An array of id strings (as specified by moduleStore.idProperty).
			var items = this.getSelectedItems();
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
			array.forEach(this._dataStore.getAttributes(item), lang.hitch(this, function(key) {
				values[key] = this._dataStore.getValue(item, key);
			}));
			return values;
		},

		getItemIndex: function(id) {
			// summary:
			//		Returns the index of the given item specified by its ID.
			//		In case the item could not be resolved, returns -1.
			// id: String

			var item = this.getItem(id);
			if (!item) {
				return -1;
			}
			return this._grid.getItemIndex(item);
		},

		getItem: function(id) {
			// summary:
			//		Returns the item for a given ID.
			// id: String

			return lang.getObject('item', false, this._grid._by_idty[id]);
		},

		_updateDisabledItems: function() {
			// see how many items are disabled
			var nDisabledItems = 0;
			tools.forIn(this._disabledIDs, function() {
				++nDisabledItems;
			});
			if (!nDisabledItems) {
				// nothing to do
				return;
			}

			// walk through all elements and make sure that their disabled state
			// is correctly set
			var idx, iitem, iid, disabled;
			for (idx = 0; idx < this._grid.rowCount; ++idx) {
				iitem = this._grid.getItem(idx);
				iid = iitem[this.moduleStore.idProperty];
				disabled = this._disabledIDs[iid] === true;
				if (disabled === (!this._grid.rowSelectCell.disabled(idx))) {
					this._grid.rowSelectCell.setDisabled(idx, disabled);
				}
			}
		},

		setDisabledItem: function(_ids, disable) {
			// summary:
			//		Disables the specified items.
			// ids: String|String[]
			//		Item ID or list of IDs.
			// disable: Boolean?
			//		Disable or enable the specified items.

			var ids = tools.stringOrArray(_ids);
			disable = undefined === disable ? true : disable;
			array.forEach(ids, function(id) {
				this._disabledIDs[id] = !!disable;
			}, this);
			this._updateDisabledItems();
			this._ignoreNextFetch = true;
			this._grid.render();
		},

		getDisabledItem: function(_ids) {
			// summary:
			//		Returns an array (if input is an array) of Boolean or Boolean.
			//		If an item could not be resolved, returns null.
			// ids: String|String[]
			//		Item ID or list of IDs.

			var ids = tools.stringOrArray(_ids);
			var result = array.map(ids, function(id) {
				var idx = this.getItemIndex(id);
				if (idx >= 0) {
					return this._grid.rowSelectCell.disabled(idx);
				}
				return null;
			}, this);

			// return Boolean or array depending on the input
			if (!(_ids instanceof Array)) {
				return result[0]; // Boolean
			}
			return result; // Boolean[]
		},

		clearDisabledItems: function(/*Boolean?*/ doRendering) {
			// summary:
			//		Enables all previously disabled items and clears internal cache.

			// clear internal cache
			this._disabledIDs = {};

			// enable all disabled items
			var idx;
			for (idx = 0; idx < this._grid.rowCount; ++idx) {
				// enable item if it is disabled
				if (this._grid.rowSelectCell.disabled(idx)) {
					this._grid.rowSelectCell.setDisabled(idx, false);
				}
			}

			// perform rendering if requested
			if (undefined === doRendering || doRendering) {
				this._ignoreNextFetch = true;
				this._grid.render();
			}
		},

		canExecuteOnSelection: function(/* String|Object */action, /* Object[] */items) {
			// summary:
			//		returns a subset of the given items that are available for the action according to the canExecute function
			var actionObj = null;
			var executableItems = [];

			if (typeof action == "string") {
				var tmpActions = array.filter(this.actions, function(iaction) {
					return iaction.isMultiAction && iaction.name == action;
				});
				if (!tmpActions.length) {
					throw 'unknown action ' + action;
				}
				actionObj = tmpActions[0];
			}
			executableItems = array.filter(items, function(iitem) {
				return typeof actionObj.canExecute == "function" ? actionObj.canExecute(iitem) : true;
			});

			return executableItems;
		},

		onFilterDone: function(success) {
			// event stub
		}
	});
});
