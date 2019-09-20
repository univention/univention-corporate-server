/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define, require, setTimeout, clearTimeout, JSON*/

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
	"dijit/Destroyable",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"dojox/html/entities",
	"dgrid/OnDemandGrid",
	"dgrid/Selection",
	"dgrid/extensions/DijitRegistry",
	"dgrid/Selector",
	"dstore/legacy/StoreAdapter",
	"dstore/Memory",
	"./Button",
	"./Text",
	"./ContainerWidget",
	"./StandbyMixin",
	"./Tooltip",
	"./_RegisterOnShowMixin",
	"../tools",
	"../render",
	"../i18n!"
], function(declare, lang, array, kernel, win, construct, attr, geometry, style, domClass,
		topic, aspect, on, Destroyable, Menu, MenuItem, DropDownButton, entities,
		OnDemandGrid, Selection, DijitRegistry, Selector, StoreAdapter, Memory, Button, Text, ContainerWidget,
		StandbyMixin, Tooltip, _RegisterOnShowMixin, tools, render, _) {

	var _Grid = declare([OnDemandGrid, Selection, Selector, DijitRegistry, Destroyable], {
		getItem: function(item) {
			// For legacy dojox grid compatibility
			// e.g. formaters that expect to be working with a dojox grid
			return item;
		},

		getSelectedIDs: function() {
			// summary:
			//		Return the currently selected items.
			// returns:
			//		An array of id strings (as specified by moduleStore.idProperty).
			return array.filter(Object.keys(this.selection), function(id) {
				return this.selection[id];
			}, this);
		},

		selectIDs: function(ids) {
			array.forEach(ids, lang.hitch(this, function(id) {
				this.select(id);
			}));
		},

		_setSort: function() {
			var selectedIDs = this.getSelectedIDs();
			this.inherited(arguments);
			this.selectIDs(selectedIDs);
		}
	});

	var _DropDownButton = declare([DropDownButton], {
		_onClick: function(evt) {
			// don't propagate any event here - otherwise dropDown gets closed.
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
		//		'canExecute': function that specifies whether an action can be executed for
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
		naturalSort: true,

		// use the framework wide translation file
		i18nClass: 'umc.app',

		// turn an labels for action columns by default
		actionLabel: true,

		// turn off gutters by default
		gutters: false,

		// auto escape all values written into the cells
		allowHTML: true,

		// defaultAction: Function/String a default action that is executed
		//		when clicking on the column defined in defaultActionColumn (if set) or in the first column.
		defaultAction: 'edit',

		// defaultActionColumn:
		//
		//
		defaultActionColumn: '',

		initialStatusMessage: _("Please perform a search"),

		_necessaryUdmValues: null,

		// gridOptions: options for the inner grid
		gridOptions: null,

		baseClass: 'umcGrid',

		additionalViews: null,

		_widgetList: null,
		own: function() {
			array.forEach(arguments, function(iarg) {
				this._widgetList.push(iarg);
			}, this);
			return this.inherited(arguments);
		},

		disabled: false,

		_contextMenu: null,

		_views: null,

		// temporary div elements to estimate width of text for columns
		_tmpCell: null,
		_tmpCellHeader: null,

		// ContainerWidget that holds all buttons
		_toolbar: null,

		hideGlobalActionsOnSelection: false,

		updateActionsMenuVisibility: true,

		_header: null,

		// internal list of all disabled items... when data has been loaded, we need to
		// disable these items again
		_disabledIDs: null,

		_selectionChangedTimeout: null,

		// internal adapter to the module store
		_store: null,
		collection: null,

		_iconFormatter: function(valueField, iconField) {
			// summary:
			//		Generates a formatter functor for a given value and icon field.

			return lang.hitch(this, function(value, item) {
				// get the iconName
				var iconName = item[iconField];

				// create an HTML image that contains the icon
				var html = lang.replace('<img src="{src}" height="{height}" width="{width}" style="float:left; margin-right: 5px" /> {value}', {
					icon: iconName, //dojo.moduleUrl("dojo", "resources/blank.gif").toString(),
					height: '16px',
					width: '16px',
					value: value,
					src: require.toUrl(lang.replace('dijit/themes/umc/icons/16x16/{0}.png', [iconName]))
				});
				return html;
			});
		},

		_createSortQuerier: function(sorted) {
			// see also dstore/SimpleQuery
			var sorter = sorted[0];
			var column = this._getColumnByName(sorter.property);
			var sortFormatter = function(value) {return value;};
			if (column.hasOwnProperty('sortFormatter')) {
				sortFormatter = column.sortFormatter;
			}
			var stringCompare;
			var hasIntl = typeof(Intl) === 'object';
			var hasCollator = hasIntl && Intl.hasOwnProperty("Collator") && typeof(Intl.Collator) === 'function';
			if (hasCollator) {
				var intlCollator =  new Intl.Collator(kernel.locale, {numeric: true});
				stringCompare = function(a, b) {
					return intlCollator.compare(a, b);
				};
			} else {
				stringCompare = function(a, b) {
					if (a.toLowerCase() < b.toLowerCase()) {
						return -1;
					} else if (a.toLowerCase() > b.toLowerCase()) {
						return 1;
					}
					return 0;
				};
			}
			var compare = function(aValue, bValue) {
				var a = sortFormatter(aValue);
				var b = sortFormatter(bValue);
				if (typeof(a) === 'string' && typeof(b) === 'string') {
					return stringCompare(a, b);
				}
				if (a === b) {
					return 0;
				}
				if (a === null && typeof(b) === 'undefined') {
					return 1;
				}
				if (typeof(a) === 'undefined' && b === null) {
					return -1;
				}
				if (a === null || typeof(a) === 'undefined') {
					return -1;
				}
				if (b === null || typeof(b) === 'undefined') {
					return 1;
				}
				if (a > b) {
					return 1;
				} else {
					return -1;
				}
			};
			return function(data) {
				data = data.slice();
				data.sort(function(a,b) {
					var aValue = a[sorter.property];
					var bValue = b[sorter.property];
					return compare(aValue, bValue) * (sorter.descending ? -1 : 1);
				});
				return data;
			};
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

		_selectAll: function() {
			this._grid.collection.fetch().forEach(lang.hitch(this, function(item){
				var row = this._grid.row(item);
				this._grid.select(row);
			}));
		},

		_updateGridSorting: function() {
			if (typeof this.sortIndex === "number" && this.sortIndex !== 0) {
				var column = this.columns[Math.abs(this.sortIndex) - 1];
				this._grid.set('sort', [{property: column.name, descending: this.sortIndex < 0 }]);
			}
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			this._necessaryUdmValues = [];
			this._widgetList = [];
			this._disabledIDs = {};
			this._views = {};
			this._store = new StoreAdapter({
				objectStore: this.moduleStore,
				isUmcpCommandStore: typeof(this.moduleStore.umcpCommand) === "function",
				idProperty: this.moduleStore.idProperty
			});
			if (this._store.isUmcpCommandStore) {
				this.own(this.moduleStore.on('Change', lang.hitch(this, function() {
					this.filter(this.query);
				})));
			} else if (this.moduleStore.query().observe) {
				this.moduleStore.query().observe(lang.hitch(this, function() {
					this.filter(this.query);
				}));
			}
			this.collection = new Memory({
				idProperty: this._store.idProperty
			});
			if (this.naturalSort) {
				this.collection._createSortQuerier = lang.hitch(this, '_createSortQuerier');
			}
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._buildHeader();

			this._grid = new _Grid(lang.mixin({
				collection: this.collection,
				bufferRows: 0,
				_refresh: lang.hitch(this, '_refresh'),
				selectionMode: 'extended',
				allowSelectAll: true,
				allowSelect: lang.hitch(this, 'allowSelect'),
				_selectAll: lang.hitch(this, '_selectAll'),
				update: lang.hitch(this, 'update'),
				selectAll: function() {
					if (this.getSelectedIDs().length === 0) {
						this.inherited(arguments);
						this._selectAll(); // Bug: dgrid only selects visible entries, we want to select everything. See also dgrid #1198
					} else {
						this.clearSelection();
					}
				}
			}, this.gridOptions || {}));

			if (this.additionalViews) {
				this._addViewsToGrid();
			}

			this._updateGridSorting();

			this._contextMenu = new Menu({
				targetNodeIds: [this._grid.domNode]
			});
			this.own(this._contextMenu);

			this.setColumnsAndActions(this.columns, this.actions);

			this.addChild(this._grid);

			//
			// register event handler
			//

			this._grid.on('dgrid-select', lang.hitch(this, '_selectionChanged'));
			this._grid.on('dgrid-deselect', lang.hitch(this, '_selectionChanged'));

			// if the row that is deselected is no longer in the dom (which happens when scrolling due to
			// 'farOffRemoval' from OnDemandList) the 'dgrid-deselect' event is not fired
			aspect.after(this._grid, 'clearSelection', lang.hitch(this, '_selectionChanged'));

			this._grid.on(".dgrid-row:contextmenu", lang.hitch(this, '_updateContextItem'));

			this.on('filterDone', lang.hitch(this, '_updateGlobalCanExecute'));

			this._grid.on('dgrid-refresh-complete', lang.hitch(this, '_cleanupWidgets'));

			aspect.after(this._grid, '_updateHeaderCheckboxes', lang.hitch(this, '_updateHeaderSelectClass'));
			aspect.before(this._grid, '_updateHeaderCheckboxes', lang.hitch(this, '_updateAllSelectedStatus'));

			if (this.query) {
				this.filter(this.query);
			} else if (!this._store.isUmcpCommandStore) {
				this.filter();
			}

			// this is for the inner scroll in the udm/navigation module
			this.own(on(this._grid, 'scroll', lang.hitch(this, function() {
				domClass.toggle(this.domNode, 'scrollIsNotAtTop', this._grid.getScrollPosition().y !== 0);
			})));
		},

		_buildHeader: function() {
			this._header = new ContainerWidget({
				baseClass: 'umcGridHeader'
			});
			this._toolbar = new ContainerWidget({
				baseClass: 'umcGrid__toolbar',
				'class': 'dijitDisplayNone'
			});
			this._contextWrapper = new ContainerWidget({
				'class': 'umcGrid__contextWrapper'	
			});
			this._contextActionsToolbar = new ContainerWidget({
				baseClass: 'umcGrid__contextActionsToolbar',
				'class': 'dijitDisplayNone'
			});
			this._statusMessage = new Text({
				'class': 'umcGridStatus',
				content: this.initialStatusMessage
			});
			var tooltip = new Tooltip({
				label: this._statusMessage.content,
				connectId: [this._statusMessage.domNode]
			});
			this._statusMessage.watch('content', function(name, old, new_) {
				tooltip.set('label', new_);
			});

			this._contextWrapper.addChild(this._contextActionsToolbar);
			this._contextWrapper.addChild(this._statusMessage);
			this._header.addChild(this._toolbar);
			this._header.addChild(this._contextWrapper);
			this.addChild(this._header);
		},

		_addViewsToGrid: function() {
			array.forEach(Object.keys(this.additionalViews), lang.hitch(this, function(viewName) {
				var view = this.additionalViews[viewName];
				view.grid = this;
				view.renderRow = lang.hitch(view, view.renderRow);
				if (view.necessaryUdmValues) {
					this._necessaryUdmValues = this._necessaryUdmValues.concat(array.filter(view.necessaryUdmValues, lang.hitch(function(value) {
						return array.indexOf(this._necessaryUdmValues, value) === -1;
					})));
				}
			}));
			this._views.default = {renderRow: this._grid.renderRow, baseClass: this.baseClass};
			lang.mixin(this._views, this.additionalViews);
		},

		changeView: function(newView) {
			if (!this._views[newView]) {
				console.warn("unknown grid view selected");
				return;
			}
			domClass.toggle(this._statusMessage.domNode, 'dijitDisplayNone', newView === 'tile');
			if (newView === 'tile') {
				this._grid.set('selectionMode', 'single');
			} else {
				this._grid.set('selectionMode', 'extended');
			}
			this._grid.renderRow = this._views[newView].renderRow;
			var allBaseClasses = array.map(Object.keys(this._views), function(view) {
				return this._views[view].baseClass;
			}, this);
			domClass.replace(this.domNode, this._views[newView].baseClass, allBaseClasses);
			this._grid.refresh();
			this._grid.resize();
			this.activeViewMode = newView;
		},

		_updateGlobalCanExecute: function() {
			var items = this.getAllItems();
			array.forEach(this._getGlobalActions(), lang.hitch(this, function(action) {
				if (action.canExecute) {
					var enabled = action.canExecute(items);
					this._globalActionsMenuMap[action.name].set('disabled', !enabled);
					array.forEach(this._toolbar.getChildren(), function(button) {
						if (button.name === action.name) {
							button.set('disabled', !enabled);
						}
					});
				}
			}));
		},

		_cleanupWidgets: function() {
			this._widgetList = array.filter(this._widgetList, function(iwidget) {
				if ((iwidget.isInstanceOf && !iwidget.isInstanceOf(Menu)) && (iwidget.id && !document.getElementById(iwidget.id)) && !iwidget._destroyed && iwidget.destroy) {
					iwidget.destroy();
					return false;
				}
				if (iwidget._destroyed) {
					return false;
				}
				return true;
			}, this);
		},

		startup: function() {
			this.inherited(arguments);

			this._registerAtParentOnShowEvents(lang.hitch(this, function() {
				this._grid.resize();
				this.updateActionsVisibility();
			}));
			on(window, 'resize', lang.hitch(this, function() {
				this.updateActionsVisibility();
			}));
			this.updateActionsVisibility();
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
//					width: 'auto',
//					editable: false,
//					description: ''
				}, icol, {
					field: icol.name
				});
//				delete col.label;

				// default action
				var defaultActionExists = this.defaultAction && (typeof this.defaultAction === "function" || array.indexOf(array.map(this.actions, function(iact) { return iact.name; }), this.defaultAction) !== -1);
				var isDefaultActionColumn = (!this.defaultActionColumn && colNum === 0) || (this.defaultActionColumn && col.name === this.defaultActionColumn);
				var allowHTML = icol.allowHTML === undefined ? this.allowHTML : icol.allowHTML;

				if (defaultActionExists && isDefaultActionColumn) {
					col.renderCell = lang.hitch(this, function(item, value/*, node, options*/) {
						value = icol.formatter ? icol.formatter(value, item) : value;
						if (! allowHTML && typeof value == "string") {
							value = entities.encode(value);
						}

						var defaultAction = this._getDefaultActionForItem(item);

						if (!defaultAction) {
							if (value && value.domNode) {
								this.own(value);
								return value.domNode;
							} else {
								var valueText = new Text({
									content: value
								});
								this.own(valueText);
								return valueText.domNode;
							}
						}

						var container = null;

						if (value && value.domNode) {
							container = new ContainerWidget({
								baseClass: 'umcGridDefaultAction'
							});
							container.addChild(value);
							container.own(value);
						} else {
							container = new Text({
								content: value,
								baseClass: 'umcGridDefaultAction'
							});
						}
						this.own(container);
						container.on('click', lang.hitch(this, function() {
							var idProperty = this.moduleStore.idProperty;
							defaultAction.callback([item[idProperty]], [item]);
						}));
						return container.domNode;
					});
				}

				// check whether the width shall be computed automatically
				if ('adjust' === col.width) {
					col.width = (this._getHeaderWidth(col.label) + 10) + 'px';
				}

				if (icol.formatter && !col.renderCell) {
					col.renderCell = function(item, value) {
						var colContent = icol.formatter(value, item, col);
						if (! allowHTML && typeof colContent == "string") {
							colContent = entities.encode(colContent);
						}
						if (colContent && colContent.domNode) {
							return colContent.domNode;
						} else {
							var container = construct.create("div", {
								innerHTML: colContent
							});
							return container;
						}
					};
				}
				// check for an icon
				if (icol.iconField) {
					// we need to specify a formatter
					col.formatter = this._iconFormatter(icol.name, icol.iconField);
				}

				return col;
			}, this);

			var showCheckboxColumn = !this.gridOptions || !this.gridOptions.selectionMode || this.gridOptions.selectionMode !== 'none';

			if (showCheckboxColumn) {
				var selectionColumn = {
					selector: 'checkbox',
					label: 'Selector',
					width: '30px'
				};
				gridColumns.unshift(selectionColumn);
			}

			// set new grid structure
			this._grid.set('columns', gridColumns);
			array.forEach(gridColumns, lang.hitch(this, function(column, id) {
				this._grid.styleColumn(id, 'width: ' + column.width);
			}));
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
				this._tmpCellHeader = construct.create('div', { 'class': 'dgrid-header dijitOffScreen' });
				this._tmpCell = construct.create('div', { 'class': 'dgrid-cell' });
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
			array.forEach([this._toolbar, this._contextActionsToolbar, this._contextMenu], function(iobj) {
				array.forEach(iobj.getChildren(), function(ichild) {
					iobj.removeChild(ichild);
					ichild.destroyRecursive();
				}, this);
			}, this);
			delete this._contextMenu.focusedChild;

			this._setGlobalActions();
			this._setContextActions();

			domClass.toggle(this._header.domNode, 'dijitDisplayNone', !this.actions.length);
			domClass.toggle(this._toolbar.domNode, 'dijitDisplayNone', this._toolbar.getChildren().length === 0);
			domClass.add(this._contextActionsToolbar.domNode, 'dijitDisplayNone');

			// redraw the columns
			if (doSetColumns !== false) {
				this._setColumnsAttr(this.columns);
			}

			if (this._started) {
				this.updateActionsVisibility();
			}
		},

		_getContextActions: function() {
			return array.filter(this.actions, function(iaction) { return (false !== iaction.isContextAction); });
		},

		_setContextActions: function() {
			this._contextActionsMenu = new Menu({});
			this.own(this._contextActionsMenu);
			this._alwaysShowContextActionsMenu = false;
			this._contextActionsMenuMap = {};

			var contextActions = this._getContextActions();
			var contextStandard = array.filter(contextActions, function(action) {
				return action.isStandardAction;
			});
			var contextNonStandard = array.filter(contextActions, function(action) {
				return !action.isStandardAction;
			});
			if (contextNonStandard.length) {
				this._alwaysShowContextActionsMenu = true;
			}

			var contextActionsSorted = contextStandard.concat(contextNonStandard);
			array.forEach(contextActionsSorted, function(iaction) {
				tools.assert(iaction.name, 'An action needs a name: ' + JSON.stringify(iaction));
				var getCallback = lang.hitch(this, function(prefix) {
					if (!iaction.callback) {
						return {};
					}
					return {
						onClick: lang.hitch(this, function() {
							this._publishAction(prefix + iaction.name);
							var ids = this.getSelectedIDs();
							var items = this.getSelectedItems();
							if (iaction.enablingMode === 'some') {
								items = array.filter(items, function(iitem) {
									return typeof iaction.canExecute === "function" ? iaction.canExecute(iitem) : true;
								});
								ids = array.map(items, function(iitem) {
									return iitem[this.moduleStore.idProperty];
								}, this);
							}
							iaction.callback(ids, items);
						})
					};
				});
				// get icon and label (these properties may be functions)
				var iiconClass = typeof iaction.iconClass === "function" ? iaction.iconClass() : iaction.iconClass;
				var ilabel = typeof iaction.label === "function" ? iaction.label() : iaction.label;

				var props = { iconClass: iiconClass, label: ilabel, _action: iaction, name: iaction.name };

				if (iaction.isStandardAction) {
					// add action to the context toolbar
					var btn = new Button(lang.mixin(props, getCallback(''), { iconClass: props.iconClass || 'umcIconNoIcon' }));
					if (iaction.description) {
						try {
						var idescription = typeof iaction.description === "function" ? iaction.description(undefined) : iaction.description;
						var TooltipClass = iaction.tooltipClass || Tooltip;
						var tooltip = new TooltipClass({
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
				}

				var menuItem = new MenuItem(lang.mixin(props, getCallback('multi-')));
				this._contextActionsMenuMap[iaction.name] = menuItem;
				this._contextActionsMenu.addChild(menuItem);

				this._contextMenu.addChild(new MenuItem(lang.mixin(props, getCallback('menu-'))));
			}, this);

			this._contextActionsMenuButton = new _DropDownButton({
				label: _('more'),
				dropDown: this._contextActionsMenu
			});
			this._contextActionsToolbar.addChild(this._contextActionsMenuButton);
		},

		_getGlobalActions: function() {
			return array.filter(this.actions, function(iaction) { return (false === iaction.isContextAction); });
		},

		_setGlobalActions: function() {
			var buttonsCfg = array.map(this._getGlobalActions(), function(iaction) {
				tools.assert(iaction.name, 'An action needs a name: ' + JSON.stringify(iaction));
				var jaction = iaction;
				if (Object.prototype.hasOwnProperty.call(iaction, 'showAction')) {
					jaction.visible = typeof iaction.showAction === 'function' ? iaction.showAction() : iaction.showAction;
				}
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

			this._globalActionsMenu = new Menu({});
			this.own(this._globalActionsMenu);
			this._globalActionsMenuMap = {};

			var buttons = render.buttons(buttonsCfg);
			array.forEach(buttons.$order$, function(ibutton) {
				this._toolbar.addChild(ibutton);
				var menuItem = new MenuItem({
					iconClass: ibutton.iconClass,
					label: ibutton.label,
					onClick: ibutton.callback
				});
				this._globalActionsMenuMap[ibutton.name] = menuItem;
				this._globalActionsMenu.addChild(menuItem);
			}, this);
			this._globalActionsMenuButton = new _DropDownButton({
				'class': 'dijitDisplayNone',
				label: _('more'),
				dropDown: this._globalActionsMenu
			});
			this._toolbar.addChild(this._globalActionsMenuButton);
		},

		_updateActionsVisibilityDeferred: null,
		updateActionsVisibility: function() {
			if (this._updateActionsVisibilityDeferred && !this._updateActionsVisibilityDeferred.isFulfilled()) {
				this._updateActionsVisibilityDeferred.cancel();
			}

			this._updateActionsVisibilityDeferred = tools.defer(lang.hitch(this, function() {
				if (geometry.getMarginBox(this.domNode).w === 0) {
					return;
				}
				this.__updateActionsVisibility();
			}), 200);
			this._updateActionsVisibilityDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		__updateActionsVisibility: function() {
			domClass.remove(this._toolbar.domNode, 'dijitDisplayNone');
			domClass.remove(this._contextActionsToolbar.domNode, 'dijitDisplayNone');

			var globalActionsToCheckForWidth = [];
			array.forEach(this._toolbar.getChildren(), lang.hitch(this, function(button) {
				if (button === this._globalActionsMenuButton) {
					domClass.remove(this._globalActionsMenuButton.domNode, 'dijitDisplayNone');
					return;
				}

				if (Object.prototype.hasOwnProperty.call(button, 'showAction')) {
					var showButton = typeof button.showAction === 'function' ? button.showAction() : button.showAction;
					if (!showButton) {
						button.set('visible', false);
						domClass.add(this._globalActionsMenuMap[button.name].domNode, 'dijitDisplayNone');
						return;
					}
				}

				button.set('visible', true);
				globalActionsToCheckForWidth.push(button);
			}));

			var contextActionsToCheckForWidth = [];
			array.forEach(this._contextActionsToolbar.getChildren(), lang.hitch(this, function(button) {
				if (button === this._contextActionsMenuButton) {
					domClass.remove(this._contextActionsMenuButton.domNode, 'dijitDisplayNone');
					return;
				}

				button.set('visible', true);
				contextActionsToCheckForWidth.push(button);
			}));

			window.requestAnimationFrame(lang.hitch(this, function() {
				var headerWidth = geometry.getContentBox(this._header.domNode).w;
				var statusWidth = geometry.getMarginBox(this._statusMessage.domNode).w;
				var changeVisibility = [/* [widgetToHide, shouldBeHidden, isButton] */];

				// global actions
				var toolbarExtents = geometry.getPadExtents(this._toolbar).w + geometry.getMarginExtents(this._toolbar.domNode).w;
				var widthForGlobalButtons = headerWidth - toolbarExtents;
				var widthRemainingForGlobalButtons = widthForGlobalButtons;

				// show or hide 'more' button for global actions
				var widthOfAllGlobalButtons = 0;
				array.forEach(globalActionsToCheckForWidth, function(button) {
					widthOfAllGlobalButtons += geometry.getMarginBox(button.domNode).w;
				});
				var showGlobalMoreMenu = widthOfAllGlobalButtons > widthForGlobalButtons;
				if (showGlobalMoreMenu) {
					widthRemainingForGlobalButtons -= geometry.getMarginBox(this._globalActionsMenuButton.domNode).w;
				}

				// move buttons which do not fit in the 'more' menu
				var numsOfGlobalStandardButtons = 0;
				array.forEach(globalActionsToCheckForWidth, lang.hitch(this, function(button) {
					var buttonWidth = geometry.getMarginBox(button.domNode).w;
					if (buttonWidth <= widthRemainingForGlobalButtons) {
						changeVisibility.push([this._globalActionsMenuMap[button.name], true, false]);
						widthRemainingForGlobalButtons -= buttonWidth;
						numsOfGlobalStandardButtons++;
					} else {
						changeVisibility.push([button, true, true]);
						changeVisibility.push([this._globalActionsMenuMap[button.name], false, false]);
					}
				}));


				// context actions
				var contextActionsToolbarExtents = geometry.getPadExtents(this._contextActionsToolbar).w + geometry.getMarginExtents(this._contextActionsToolbar.domNode).w;
				var widthForContextButtons = headerWidth - contextActionsToolbarExtents - statusWidth;
				var widthRemainingForContextButtons = widthForContextButtons;

				// show or hide 'more' button for global actions
				var showContextMoreMenu = this._alwaysShowContextActionsMenu;
				if (!showContextMoreMenu) {
					var widthOfAllContextButtons = 0;
					array.forEach(contextActionsToCheckForWidth, lang.hitch(this, function(button) {
						widthOfAllContextButtons += geometry.getMarginBox(button.domNode).w;
					}));
					showContextMoreMenu = widthOfAllContextButtons > widthForContextButtons;
				}
				if (showContextMoreMenu) {
					widthRemainingForContextButtons -= geometry.getMarginBox(this._contextActionsMenuButton.domNode).w;
				}

				// move buttons which do not fit in the 'more' menu
				var numsOfContextStandardButtons = 0;
				array.forEach(contextActionsToCheckForWidth, lang.hitch(this, function(button) {
					var buttonWidth = geometry.getMarginBox(button.domNode).w;
					if (buttonWidth <= widthRemainingForContextButtons) {
						changeVisibility.push([this._contextActionsMenuMap[button.name], true, false]);
						widthRemainingForContextButtons -= buttonWidth;
						numsOfContextStandardButtons++;
					} else {
						changeVisibility.push([button, true, true]);
						changeVisibility.push([this._contextActionsMenuMap[button.name], false, false]);
					}
				}));


				if (this.updateActionsMenuVisibility) {
					array.forEach(changeVisibility, function(i /* [widget, shouldBeHidden, isButton] */) {
						if (i[2]) {
							i[0].set('visible', !i[1]);
						} else {
							domClass.toggle(i[0].domNode, 'dijitDisplayNone', i[1]);
						}
					});
					domClass.toggle(this._globalActionsMenuButton.domNode, 'dijitDisplayNone', !showGlobalMoreMenu);
					domClass.toggle(this._contextActionsMenuButton.domNode, 'dijitDisplayNone', !showContextMoreMenu);

					this._globalActionsMenuButton.set('label', numsOfGlobalStandardButtons === 0 ? _('Actions') : _('more'));
					this._contextActionsMenuButton.set('label', numsOfContextStandardButtons === 0 ? _('Actions') : _('more'));
				} else {
					domClass.add(this._globalActionsMenuButton.domNode, 'dijitDisplayNone');
					domClass.toggle(this._contextActionsMenuButton.domNode, 'dijitDisplayNone', !this._alwaysShowContextActionsMenu);

					this._globalActionsMenuButton.set('label', _('more'));
					this._contextActionsMenuButton.set('label', _('more'));
				}

				this._updateToolbarVisibility();
			}));
		},

		_selectionChanged: function() {
			if (this._selectionChangedTimeout) {
				clearTimeout(this._selectionChangedTimeout);
			}

			this._selectionChangedTimeout = setTimeout(lang.hitch(this, function() {
				this._updateContextActions();
				this._updateFooterContent();

				this._selectionChangedTimeout = null;
			}), 50);
		},

		_getContextActionItems: function() {
			return this._contextActionsToolbar.getChildren().concat(this._contextMenu.getChildren()).concat(this._contextActionsMenu.getChildren());
		},

		_updateContextActions: function() {
			var nItems = this.getSelectedIDs().length;

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
					if (item._action.enablingMode === 'some') {
						enablingFunction = array.some;
					}
					enabled = enabled && enablingFunction(this.getSelectedItems(), function(iitem) { return item._action.canExecute ? item._action.canExecute(iitem) : true; });
					item.set('disabled', !enabled);
				}
			}, this);

			this._updateToolbarVisibility();
		},

		_updateToolbarVisibility: function() {
			var itemsSelected = this.getSelectedIDs().length > 0;
			domClass.toggle(this._header.domNode, 'umcGridHeader--items-selected', itemsSelected);
			if (this.activeViewMode === 'tile') {
				domClass.toggle(this._toolbar.domNode, 'dijitDisplayNone', false);
				domClass.toggle(this._contextActionsToolbar.domNode, 'dijitDisplayNone', true);
			} else {
				if (this.hideGlobalActionsOnSelection) {
					domClass.toggle(this._toolbar.domNode, 'dijitDisplayNone', itemsSelected);
				}
				domClass.toggle(this._contextActionsToolbar.domNode, 'dijitDisplayNone', !itemsSelected);
			}
		},

		_updateContextItem: function(evt) {
			// when opening the context menu...
//TODO
//			var rowDisabled = this._grid.rowSelectCell.disabled(evt.rowIndex);
//			if (rowDisabled) {
//				return;
//			}

			var hasClickedOnDefaultAction = (evt.target !== evt.cellNode);
			var id = this._grid.row(evt).id;
			var isSelected = this._grid.get('selection')[id];
			if (!isSelected || hasClickedOnDefaultAction) {
				var newSelection = lang.mixin({}, this._grid.get('selection'));
				newSelection[id] = true;
				this._grid.set('selection', newSelection);
			}
		},

		_getDefaultActionForItem: function(item) {
			// returns the default action for a specified item if the action exists and can be executed
			var identity = item[this.moduleStore.idProperty];
			var defaultAction = typeof this.defaultAction === "function" ?
				this.defaultAction([identity], [item]) : this.defaultAction;

			if (defaultAction) {
				var action;
				array.forEach(this.actions, function(iaction) {
					if (iaction.name === defaultAction) {
						action = iaction;
						return false;
					}
				}, this);
				if (action && action.callback) {
					var isExecutable = typeof action.canExecute === "function" ? action.canExecute(item) : true;
					if (isExecutable && !this.getDisabledItem(identity)) {
						return action;
					}
				}
			}
		},

		_setDisabledAttr: function(disabled) {
			this.disabled = disabled;

			// disable items
			this._grid.collection.fetch().forEach(lang.hitch(this, function(item) {
				var id = item[this.moduleStore.idProperty];
				this.setDisabledItem(id, disabled);
			}));
			// re-disable explicitly disabled items
			//this._updateDisabledItems();

			// disable all actions
			array.forEach(this._toolbar.getChildren().concat(this._contextActionsToolbar), lang.hitch(this, function(widget) {
				if (widget instanceof Button || widget instanceof _DropDownButton) {
					widget.set('disabled', disabled);
				}
			}));
		},

		_updateFooterContent: function() {
			var nItems = this.getSelectedIDs().length;
			this._grid.collection.fetch().totalLength.then(lang.hitch(this, function(nItemsTotal) {
				var msg = '';
				var showCounter = !this.gridOptions || !this.gridOptions.selectionMode || this.gridOptions.selectionMode !== 'none';
				if (typeof this.footerFormatter === "function") {
					msg = this.footerFormatter(nItems, nItemsTotal);
				} else {
					if (showCounter) {
						msg = _('%(num)d entries of %(total)d selected', {num: nItems, total: nItemsTotal});
						if (1 === nItems) {
							msg = _('1 entry of %d selected', nItemsTotal);
						}
					} else {
						msg = _('%d entries found', nItemsTotal);
					}

					if (0 === nItemsTotal) {
						msg = _('No entries could be found');
					}
				}
				this._statusMessage.set('content', msg);
			}));
		},

		_updateHeaderSelectClass: function() {
			if (!this._grid._selectorColumns[0]) {
				return;
			}
			var selectorColumn = this._grid._selectorColumns[0];
			var checkbox = selectorColumn._selectorHeaderCheckbox;
			var selectNode = selectorColumn.headerNode;
			if (checkbox.checked) {
				domClass.remove(selectNode, "dgrid-indeterminate");
				domClass.add(selectNode, "dgrid-allSelected");
				return;
			} else if (checkbox.indeterminate) {
				domClass.remove(selectNode, "dgrid-allSelected");
				domClass.add(selectNode, "dgrid-indeterminate");
				return;
			} else {
				domClass.remove(selectNode, "dgrid-indeterminate");
				domClass.remove(selectNode, "dgrid-allSelected");
				return;
			}
		},

		_updateAllSelectedStatus: function() {
			// dgrid bug #292: the header checkbox doesn't work if all entries there selected manually
			this._grid.allSelected = array.every(this.getAllItems(), function(item) {
				return this._grid.isSelected(item);
			}, this);
		},

		_refresh: function() {
			this.filter(this.query);
		},

		update: function(force) {
			var updateNotPaused = false;
			if (this.getSelectedIDs().length === 0 || force) {
				updateNotPaused = true;
				var selectedIDs = this.getSelectedIDs();
				var pageScrollYBeforeUpdate = geometry.docScroll().y;
				var gridScrollYBeforeUpdate = this._grid.getScrollPosition().y;
				this._filter(this.query).then(lang.hitch(this, function() {
					window.scroll(0, pageScrollYBeforeUpdate);
					this._grid.scrollTo({y: gridScrollYBeforeUpdate});
				}));
				array.forEach(selectedIDs, function(selectedID) {
					this._grid.select(this._grid.row(selectedID));
				}, this);
			}
			return updateNotPaused;
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

		filter: function(query, options) {
			style.set(this._grid.headerNode, 'right', ''); // unset 'right' so that the grid resizes correctly
			domClass.add(this.domNode, this.baseClass + '--filtering');
			this.standby(true);
			return this._filter(query, options).then(lang.hitch(this, function() {
				this.standby(false);
				domClass.remove(this.domNode, this.baseClass + '--filtering');

				// Normally dgrid either has always a scrollbar or no scrollbar at all.
				// If a scrollbar is shown, dgrid adjust the right alignment of the header
				// so that the text in the cells and in the header align.
				// But we want to be able to show the scrollbar only when it is needed.
				// We adjusted the styling so that the scrollbar is only shown when needed.
				// Set the right alignment of the header to 0 manually when a scrollbar is shown.
				if (this._grid.bodyNode.scrollHeight <= this._grid.bodyNode.clientHeight) {
					style.set(this._grid.headerNode, 'right', '0');
				}
			}));
		},

		_filter: function(query, options) {
			var addedFieldsQuery = query;
			if (query && this._necessaryUdmValues.length > 0) {
				array.forEach(this._necessaryUdmValues, function(value) {
					if (array.indexOf(query.fields, value) === -1) {
						addedFieldsQuery.fields.push(value);
					}
				});
			}
			var onSuccess = lang.hitch(this, function(result) {
				this.collection.setData(result);
				this._grid.refresh();
				this._updateFooterContent();
				this.onFilterDone(true);
			});
			var onError = lang.hitch(this, function(error) {
				error = tools.parseError(error);
				this._statusMessage.set('content', _('Could not load search results'));
				this.collection.setData([]);
				this._grid.refresh();
				this._updateFooterContent();
			});
			// store the last query
			this.query = query;
			// umcpCommand doesn't know a range option -> need to cache
			// StoreAdapter doesn't work with fetchSync -> need to cache
			return this._store.filter(addedFieldsQuery, options).fetch().then(onSuccess, onError);
		},

		getAllItems: function() {
			// summary:
			//		Returns a list of all items
			var items = this._grid.collection.fetchSync();
			return items;
		},

		getSelectedItems: function() {
			// summary:
			//		Return the currently selected items.
			//		Filters disabled items.
			// returns:
			//		An array of dictionaries with all available properties of the selected items.
			var ids = this.getSelectedIDs();
			var filter = new this._grid.collection.Filter();
			var selectedItemsFilter = filter.in(this.moduleStore.idProperty, ids);
			var items = this._grid.collection.filter(selectedItemsFilter).fetchSync();
			return items;
		},

		getSelectedIDs: function() {
			return this._grid.getSelectedIDs();
		},

		getRowValues: function(row) {
			return row;
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
			return id;
		},

		getItem: function(id) {
			// summary:
			//		Returns the item for a given ID.
			// id: String

			var row = this._grid.row(id);
			if (row.id) {
				return row.data;
			}
			return null;
		},

		_getColumnByName: function(name) {
			var targetColumn;
			array.some(this.columns, function(column) {
				if (column.name === name) {
					targetColumn = column;
					return true;
				}
				return false;
			});
			return targetColumn;
		},

		//_updateDisabledItems: function() {
		//    // see how many items are disabled
		//    var nDisabledItems = 0;
		//    tools.forIn(this._disabledIDs, function() {
		//        ++nDisabledItems;
		//    });
		//    if (!nDisabledItems) {
		//        // nothing to do
		//        return;
		//    }

		//    // walk through all elements and make sure that their disabled state
		//    // is correctly set
		//    var idx, iitem, iid, disabled;
		//    for (idx = 0; idx < this._grid.rowCount; ++idx) {
		//        iitem = this._grid.getItem(idx);
		//        iid = iitem[this.moduleStore.idProperty];
		//        disabled = this._disabledIDs[iid] === true;
		//        if (disabled === (!this._grid.rowSelectCell.disabled(idx))) {
		//            this._grid.rowSelectCell.setDisabled(idx, disabled);
		//        }
		//    }
		//},

		allowSelect: function(row) {
			if (this._disabledIDs[row.id]) {
				return false;
			} else {
				return true;
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
				if (this._disabledIDs[id]) {
					this._grid.deselect(id);
				}
				var selectorColumn = '0';
				var selectorCell = this._grid.cell(id, selectorColumn);
				if (selectorCell.element) {
					var checkboxNode = selectorCell.element.firstChild;
					attr.set(checkboxNode, 'disabled', disable);
				}
			}, this);
		},

		getDisabledItem: function(_ids) {
			// summary:
			//		Returns an array (if input is an array) of Boolean or Boolean.
			//		If an item could not be resolved, returns null.
			// ids: String|String[]
			//		Item ID or list of IDs.

			var ids = tools.stringOrArray(_ids);
			var result = array.map(ids, function(id) {
				if (this._grid.row(id).element) {
					return this._grid.allowSelect(id);
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

			// enable all disabled items
			for (var id in this._disabledIDs) {
				if (this._disabledIDs[id] === true) {
					this.setDisabledItem(id, false);
				}
			}

			// perform rendering if requested
			if (undefined === doRendering || doRendering) {
				this._grid.refresh();
			}
		},

		canExecuteOnSelection: function(/* String|Object */action, /* Object[] */items) {
			// summary:
			//		returns a subset of the given items that are available for the action according to the canExecute function
			var actionObj = null;
			var executableItems = [];

			if (typeof action === "string") {
				var tmpActions = array.filter(this.actions, function(iaction) {
					return iaction.isMultiAction && iaction.name === action;
				});
				if (!tmpActions.length) {
					throw 'unknown action ' + action;
				}
				actionObj = tmpActions[0];
			}
			executableItems = array.filter(items, function(iitem) {
				return typeof actionObj.canExecute === "function" ? actionObj.canExecute(iitem) : true;
			});

			return executableItems;
		},

		onFilterDone: function(/*success*/) {
			// event stub
		}
	});
});
