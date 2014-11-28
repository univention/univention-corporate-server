/*
 * Copyright 2012-2014 Univention GmbH
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
/*global define console window setTimeout*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/_base/window",
	"dojo/on",
	"dojo/has",
	"dojo/query",
	"dojo/dom-class",
	"dojo/dom-style",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/Destroyable",
	"../tools",
	"./Tooltip",
	"dgrid/List",
	"dgrid/extensions/DijitRegistry",
	"put-selector/put"
], function(declare, lang, array, kernel, win, on, has, query, domClass, domStyle, domConstruct, domGeometry, Menu, MenuItem, Destroyable, tools, Tooltip, List, DijitRegistry, put) {
	return declare("umc.widgets.GalleryPane", [ List, DijitRegistry, Destroyable ], {
		style: "",

		baseClass: 'umcGalleryPane',

		bounceDuration: 50,

		query: {},

		queryOptions: {},

		_defaultActionHandle: null,

		_resizeDeferred: null,

		_setStore: function(value) {
			this.store = value;
			this._renderQuery();
		},

		_setQuery: function(value) {
			this.query = value;
			this._renderQuery();
		},

		_setQueryOptions: function(value) {
			this.queryOptions = value;
			this._renderQuery();
		},

		_renderQuery: function() {
			this.refresh();
			this.renderArray(this.store.query(this.query, this.queryOptions));
			this._resizeItemNames();
		},

		_setActions: function(actions) {
			this._set('actions', actions);
			if (this._defaultActionHandle) {
				this._defaultActionHandle.remove();
				this._defaultActionHandle = null;
			}
			var hasContextActions = false;
			array.forEach(actions, lang.hitch(this, function(action) {
				if (action.isContextAction !== false) {
					hasContextActions = true;
				}
				if (action.isDefaultAction) {
					if (this._defaultActionHandle) {
						console.warn('More than one defaultAction specified. Overwriting old one, taking new one:', action.name);
						this._defaultActionHandle.remove();
						this._defaultActionHandle = null;
					}
					this._defaultActionHandle = this.on('.umcGalleryItem:click', lang.hitch(this, function(evt) {
						evt.stopImmediatePropagation();
						var item = this.row(evt).data;
						var id = item.id;
						action.callback(id, item);
					}));
				}
			}));
			this._destroyContextMenu();
			if (hasContextActions) {
				this._createContextMenu();
			}
		},

		_destroyContextMenu: function() {
			if (this._contextMenu) {
				this._contextMenu.destroyRecursive();
				this._contextMenu = null;
			}
		},

		_closeContextMenu: function() {
			if (this._contextMenu) {
				this._contextMenu.onCancel();
			}
		},

		_createContextMenu: function() {
			this._contextMenu = new Menu({
				targetNodes: [ this.id ],
				selector: '.umcGalleryItem'
			});
			this.own(this._contextMenu);
			array.forEach(this.actions, lang.hitch(this, function(action) {
				if (action.isContextAction === false) {
					return;
				}
				var label = action.label;
				if (typeof label == 'function') {
					label = 'Placeholder';
				}
				this._contextMenu.addChild(new MenuItem({
					label: label,
					iconClass: action.iconClass,
					onClick: lang.hitch(this, function() {
						var item = this._contextItem;
						var canExecute = typeof action.canExecute == "function" ? action.canExecute(item) : true;
						if (canExecute && action.callback) {
							var id = item.id;
							action.callback(id, item);
						}
					}),
					_action: action
				}));
			}));
			this._contextMenu.startup();
		},

		_openContextMenu: function(item, node, x, y) {
			this._closeContextMenu();
			this._contextItem = item;

			if (!this._contextMenu) {
				return;
			}
			array.forEach(this._contextMenu.getChildren(), function(menuItem) {
				var action = menuItem._action;
				var disabled = action.canExecute && !action.canExecute(item);
				var iconClass = typeof action.iconClass == "function" ? action.iconClass(item) : action.iconClass;
				var label = typeof action.label == "function" ? action.label(item) : action.label;
				menuItem.set('disabled', disabled);
				menuItem.set('label', label);
				menuItem.set('iconClass', iconClass);
			}, this);

			domClass.add(node, 'umcGalleryItemActive');

			this._contextMenu._openMyself({
				target: node,
				coords: {x: x, y: y}
			});
			on.once(this._contextMenu, 'close', lang.hitch(this, function() {
				domClass.remove(node, 'umcGalleryItemActive');
			}));
		},

		postCreate: function() {
			this.inherited(arguments);

			// TODO: this changes with Dojo 2.0
			this.domNode.setAttribute("widgetId", this.id);

			// add specific DOM classes
			if (this.baseClass) {
				domClass.add(this.domNode, this.baseClass);
			}

			// add specific CSS style given as string
			if (lang.isObject(this.style)){
				domStyle.set(this.domNode, this.style);
			}
			else {
				if (this.domNode.style.cssText){
					this.domNode.style.cssText += "; " + this.style;
				}
				else {
					this.domNode.style.cssText = this.style;
				}
			}

			// set handlers
			this.on('scroll', lang.hitch(this, '_closeContextMenu'));
			this.on('.umcGalleryContextIcon:click', lang.hitch(this, function(evt) {
				evt.stopImmediatePropagation();
				var row = this.row(evt);
				this._openContextMenu(row.data, row.element, evt.pageX, evt.pageY);
			}));
			this.on('.umcGalleryItem:contextmenu', lang.hitch(this, function(evt) {
				evt.preventDefault();
				var row = this.row(evt);
				this._openContextMenu(row.data, row.element, evt.pageX, evt.pageY);
			}));
			if (has('touch')) {
				var _contextTouchTimeout = null;
				var _cancelContextTouch = function() {
					if (_contextTouchTimeout !== null) {
						window.clearTimeout(_contextTouchTimeout);
						_contextTouchTimeout = null;
						return true;
					}
					return false;
				};

				this.on('.umcGalleryItem:touchstart', lang.hitch(this, function(evt) {
					_contextTouchTimeout = setTimeout(lang.hitch(this, function() {
						var row = this.row(evt);
						this._openContextMenu(row.data, row.element, evt.pageX, evt.pageY);
						_contextTouchTimeout = null;
					}), 1000);
				}));
				this.on('.umcGalleryItem:touchend', lang.hitch(this, function(evt) {
					if (!_cancelContextTouch()) {
						evt.preventDefault();
					}
				}));
			}

			if (this.actions) {
				this._setActions(this.actions);
			}
			// set the store
			if (this.store) {
				this.set('store', this.store);
			}
		},

		startup: function() {
			this.inherited(arguments);
			if (this.store) {
				this._renderQuery();
			}
			this.own(on(kernel.global, 'resize', lang.hitch(this, '_handleResize')));
			this.own(on(win.doc, 'resize', lang.hitch(this, '_handleResize')));
		},

		_getItemNameHeight: function(node) {
			var nameNode = query('.umcGalleryName', node)[0];
			return domGeometry.position(nameNode).h;
		},

		_getDefaultItemNameHeight: function() {
			// render empty gallery item
			var node = this.renderRow({
				name: '*',
				description: '*'
			});
			domClass.add(node, 'dijitOffScreen');
			domConstruct.place(node, this.contentNode);
			var height = this._getItemNameHeight(node);
			domConstruct.destroy(node);
			return height;
		},

		_resizeItemNames: function() {
			var defaultHeight = this._getDefaultItemNameHeight();
			query('.umcGalleryName', this.contentNode).forEach(lang.hitch(this, function(inode) {
				domStyle.set(inode, 'fontSize', '');
				var iheight = domGeometry.position(inode).h;
				var fontSize = 1.5;
				while (iheight > defaultHeight + 0.5 && fontSize > 0.5) {
					domStyle.set(inode, 'fontSize', fontSize + 'em');
					iheight = domGeometry.position(inode).h;
					fontSize *= 0.9;
				}
			}));
		},

		_handleResize: function() {
			if (this._resizeDeferred && !this._resizeDeferred.isFulfilled()) {
				this._resizeDeferred.cancel();
			}
			this._resizeDeferred = tools.defer(lang.hitch(this, '_resizeItemNames'), 200);
			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		isLeftToRight: function() {
			// needed for Dojo 1.9
			return true;
		},

		getItemDescription: function(item) {
			return item.description || '';
		},

		getItemName: function(item) {
			return item.name || '';
		},

		bootstrapClasses: "col-xxs-12.col-xs-6.col-sm-6.col-md-4.col-lg-3",

		renderRow: function(item) {
			// create gallery item with bootstrap size classes
			var wrapperDiv = put(lang.replace('div.umcGalleryWrapperItem.{bootstrapClasses}[moduleID={moduleID}]', {
				moduleID: item.$id$,
				bootstrapClasses: this.bootstrapClasses
			}));
			var div = put(wrapperDiv, lang.replace('div.umcGalleryItem', item));
			var description = this.getItemDescription(item);
			var iconClass = this.getIconClass(item);
			if (iconClass) {
				put(div, 'div.umcGalleryIcon.' + iconClass);
			}
			put(div, 'div.umcGalleryName', this.getItemName(item));
			put(div, 'div.umcGalleryDescription', description);
			if (this._contextMenu) {
				put(div, 'div.umcGalleryContextIcon');
			}

			// create status icon
			var statusIconClass = this.getStatusIconClass(item);
			if (statusIconClass) {
				var statusIconDiv = domConstruct.create('div', {'class': 'umcGalleryStatusIcon ' + statusIconClass}, div);
				var statusIconLabel = this.getStatusIconTooltip(item);
				if (statusIconLabel) {
					var statusIconTooltip = new Tooltip({
						label: statusIconLabel,
						connectId: [ statusIconDiv ]
					});
					this.own(statusIconTooltip);
				}
			}

			return wrapperDiv;
		},

		getIconClass: function(item) {
			if (item.icon) {
				return tools.getIconClass(item.icon, 50);
			}
			return '';
		},

		getStatusIconClass: function(item) {
			return '';
		},

		getStatusIconTooltip: function(item) {
			return '';
		}
	});
});

