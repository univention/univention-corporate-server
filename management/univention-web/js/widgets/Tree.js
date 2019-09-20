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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/on",
	"dojo/mouse",
	"dojo/Evented",
	"dijit/Destroyable",
	"dgrid/OnDemandGrid",
	"dgrid/Tree",
	"dgrid/Selection",
	"dgrid/extensions/DijitRegistry",
	"dstore/Memory",
	"dstore/Trackable",
	"dstore/Tree",
	"umc/tools",
	"./ContainerWidget",
	"./_RegisterOnShowMixin"
], function(declare, lang, array, domClass, on, mouse, Evented, Destroyable, OnDemandGrid, Tree, Selection, DijitRegistry, Memory, Trackable, TreeDstore, tools, ContainerWidget, _RegisterOnShowMixin) {

	var GridTree = declare([OnDemandGrid, Tree, Selection, DijitRegistry, Destroyable]);
	var MemoryTree = declare([Memory, Trackable, TreeDstore]);

	return declare("umc.widgets.Tree", [ContainerWidget, _RegisterOnShowMixin, Evented], {
		'class': 'umcGridTree',
		showRoot: true,
		autoExpand: false,
		selectRootOnLoad: true,

		buildRendering: function() {
			this.inherited(arguments);
			this._gridTree = new GridTree(lang.mixin({
				collection: null,
				selectionMode: 'single',
				collapseOnRefresh: true,
				shouldExpand: lang.hitch(this, 'shouldExpand'),
				showHeader: false,
				treeIndentWidth: 24,
				columns: {
					label: {
						renderExpando: true,
						formatter: lang.hitch(this, 'columnsFormatter')
					}
				}
			}, {}));
			this.addChild(this._gridTree);
			this._gridTree.on('dgrid-select', lang.hitch(this, '_selectionChanged'));
			this._gridTree.on(on.selector('.dgrid-content .dgrid-row', mouse.enter), lang.hitch(this, function (event) {
				var row = this._gridTree.row(event);
				var legacyObject = {
					item: row.data
				};
				this._onNodeMouseEnter(legacyObject);
			}));
		},

		columnsFormatter: function(value, object) {
			return this.getRowIconHTML(object) + value;
		},

		getIconClass: function(object) {
			return tools.getIconClass(object.icon);
		},

		_getStore: function() {
			var store = new MemoryTree({
				getChildren: lang.hitch(this, function(parentItem) {
					var childrenStore = new MemoryTree();
					var rowElement = this._gridTree.row(parentItem).element;
					if (rowElement) {
						domClass.add(rowElement, 'childrenUnknown');
					}
					this.model.getChildren(parentItem, lang.hitch(this, function(items){
						if (rowElement) {
							domClass.replace(rowElement, (items.length ? 'hasChildren' : 'noChildren'), 'childrenUnknown');
						}
						items.forEach(lang.hitch(this, function(item) {
							item.parentId = parentItem.id;
							childrenStore.put(item);
						}));
					}));
					return childrenStore;
				}),
				mayHaveChildren: lang.hitch(this, function(item) {
					return this.model.mayHaveChildren(item);
				})
			});
			if (this.showRoot) {
				this.model.getRoot(lang.hitch(this, function(item) {
					store.put(item);
					this.emit("load", {});
					this.onLoad();
				}));
			} else {
				this.model.getRoot(lang.hitch(this, function(rootItem) {
					this.model.getChildren(rootItem, lang.hitch(this, function(items){
						items.forEach(lang.hitch(this, function(item) {
							store.put(item);
							this.emit("load", {});
							this.onLoad();
						}));
					}));
				}));
			}
			return store;
		},

		postCreate: function() {
			this.inherited(arguments);
			if (this.selectRootOnLoad) {
				on.once(this, 'load', lang.hitch(this, function() {
					// if the tree has been loaded successfully, model.root
					// is set and we can select the root as active node
					if (this.model.root) {
						this.set('path', [this.model.root]);
					}
				}));
			}
		},

		startup: function() {
			this.inherited(arguments);
			this._loadGridTreeData();
			this._registerAtParentOnShowEvents(lang.hitch(this._gridTree, 'resize'));
		},

		_loadGridTreeData: function() {
			this._gridTree.set('collection', this._getStore());
		},

		reload: function() {
			this._loadGridTreeData();
		},

		shouldExpandAndSelect: function(row) {
			var isItemOnPath = array.some(this.path, function(itemOnPath) {
				return itemOnPath.id === row.id;
			});
			if (this.path && row.id === this.path[this.path.length - 1].id) {
				this._gridTree.select(row.id);
			}
			return isItemOnPath;
		},

		shouldExpand: function(row) {
			if (this.autoExpand) {
				return true;
			}
			return this.shouldExpandAndSelect(row);
		},

		getRowIconHTML: function(object) {
			var html = lang.replace('<span role="presentation" class="dgrid-tree-icon dijitInline {iconClass}"></span>', {
				iconClass: this.getIconClass(object)
			});
			return html;
		},

		path: [],

		_selectionChanged: function() {
			var selectedObject = this._getSelectedObjects()[0];
			var path = [];
			var objectOnPath = selectedObject;
			var parentObject = null;
			path.unshift(objectOnPath);
			while (objectOnPath.parentId) {
				parentObject = this._getObject(objectOnPath.parentId);
				path.unshift(parentObject);
				objectOnPath = parentObject;
			}
			this._set('path', path);
		},

		selectedItems: null,

		_getSelectedItemsAttr: function() {
			this.selectedItems = this._getSelectedObjects();
			return this.selectedItems;
		},

		_getSelectedIds: function() {
			return array.filter(Object.keys(this._gridTree.selection), function(id) {
				return this._gridTree.selection[id];
			}, this);
		},

		_getSelectedObjects: function() {
			var selectedIds = this._getSelectedIds();
			return array.map(selectedIds, function(id) {
				return this._getObject(id);
			}, this);
		},

		_getObject: function(id) {
			var row = this._gridTree.row(id);
			return row.data;
		},

		_setPathAttr: function(pathTemp) {
			var path = [];
			var pathChanged = false;
			array.forEach(pathTemp, lang.hitch(this, function(_location) {
				if (typeof(_location) === 'object') {
					path.push(_location);
				} else {
					var objectOnLocation = this._getObject(_location);
					if (objectOnLocation) {
						path.push(objectOnLocation);
					} else {
						path.push({id: _location});
					}
				}
			}));
			if (path.length === this.path.length) {
				pathChanged = !array.every(path, function(_location, i) {
					return _location === this.path[i];
				}, this);
			} else {
				pathChanged = true;
			}
			if (pathChanged) {
				this._set('path', path);
				this._gridTree.refresh();
			}
		},

		_onNodeMouseEnter: function() {
			return;
		},

		dndController: {
			singular: true
		},

		indentDetector: {
			style: ''
		},

		_getFirst: function() {
			return {item: this._gridTree.collection.fetchSync()[0]};
		},

		_getLast: function() {
			var items = this._gridTree.collection.fetchSync();
			return {item: items[items.length - 1]};
		},

		onLoad: function() {
			return;
		}
	});
});
