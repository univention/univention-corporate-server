/*
 * Copyright 2011-2016 Univention GmbH
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
/*global define, require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/mouse",
	"dojo/Evented",
	"dojo/Deferred",
	"dijit/Destroyable",
	"dgrid/OnDemandGrid",
	"dgrid/Tree",
	"dgrid/Selection",
	"dgrid/extensions/DijitRegistry",
	"dstore/Memory",
	"dstore/Trackable",
	"dstore/Tree",
	"./ContainerWidget",
	"./_RegisterOnShowMixin",
	"xstyle/css!../../dgrid/css/dgrid.css"
], function(declare, lang, array, on, mouse, Evented, Deferred, Destroyable, OnDemandGrid, Tree, Selection, DijitRegistry, Memory, Trackable, TreeDstore, ContainerWidget, _RegisterOnShowMixin) {
	return declare("umc.widgets.Tree", [ContainerWidget, _RegisterOnShowMixin, Evented], {
		postMixInProperties: function() {
			this.inherited(arguments);
		},
		buildRendering: function() {
			this.inherited(arguments);
			var GridTree = declare([OnDemandGrid, Tree, Selection, DijitRegistry, Destroyable]);
			this._gridTree = new GridTree(lang.mixin({
				collection: null,
				collapseOnRefresh: true,
				shouldExpand: lang.hitch(this, 'shouldExpandAndSelect'),
				showHeader: false,
				columns: {
					label: {
						label: 'DN',
						renderExpando: true,
						formatter: lang.hitch(this, function(value, object) {
							return this.getRowIconHTML(object.icon) + value;
						})
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
		_getStore: function() {
			var MemoryTree = declare([Memory, Trackable, TreeDstore]);
			var store = new MemoryTree({
				getChildren: lang.hitch(this, function(parentItem) {
					var childrenStore = new MemoryTree();
					this.model.getChildren(parentItem, lang.hitch(this, function(items){
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
			this.model.getRoot(lang.hitch(this, function(item) {
				store.put(item);
				this.emit("load", {});
			}));
			return store;
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
		getRowIconHTML: function(icon) {
			var html = lang.replace('<img src="{url}/umc/icons/16x16/{icon}.png" role="presentation" class="dgrid-tree-icon"/>', {
				icon: icon,
				url: require.toUrl('dijit/themes')
			});
			return html;
		},
		path: null,
		_selectionChanged: function() {
			var selectedObject = this._getSelectedObjects()[0];
			var path = [];
			var objectOnPath = selectedObject;
			var parentObject = null;
			while (objectOnPath.parentId) {
				parentObject = this._getObject(objectOnPath.parentId);
				path.push(parentObject);
				objectOnPath = parentObject;
			}
			path.push(selectedObject);
			this._set('path', path);
		},
		selectedItems: null,
		_getSelectedItemsAttr: function() {
			this.selectedItems = this._getSelectedObjects();
			return this.selectedItems;
		},
		_getSelectedObjects: function() {
			var selectedItems = [];
			for (var id in this._gridTree.selection) {
				if (this._gridTree.selection[id]) {
					selectedItems.push(this._getObject(id));
				}
			}
			return selectedItems;
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
					path.push(this._getObject(_location));
				}
			}));
			if (this.path && path.length === this.path.length) {
				for (var i = 0; i < path.length; i++) {
					if (this.path[i].id !== path[i].id) {
						pathChanged = true;
						break;
					}
				}
			} else {
				pathChanged = true;
			}
			if (pathChanged) {
				this.path = path;
				this._gridTree.refresh();
			}
		},
		_onNodeMouseEnter: function() {
			return;
		},
		indentDetector: {
			style: ''
		}
	});
});
