/*
 * Copyright 2014-2019 Univention GmbH
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
	"dojo/aspect",
	"dojox/timing/_base",
	"dijit/Destroyable"
], function(declare, lang, array, aspect, timing, Destroyable) {
	return declare("umc.modules.uvmm.GridUpdater", [Destroyable], {
		grid: null, // reference to the grid
		tree: null, // reference to the tree
		interval: null, // interval in seconds
		_childrenAdvicer: null,

		constructor: function(kwArgs) {
			lang.mixin(this, kwArgs);
			this.interval = parseInt(this.interval, 10);
			var milliseconds = 1000 * this.interval;
			this._treeStoreCache = {};
			this._renewChildrenAdvicer();
			this.own(aspect.after(this.tree, 'reload', lang.hitch(this, '_renewChildrenAdvicer')));
			this._timer = new timing.Timer(1000 * this.interval);
			this._timer.onTick = lang.hitch(this, function() {
				this.grid.update();
				this._treeUpdate();
			});
			if (milliseconds > 0) {
				// else: interval=0 or interval=NaN
				this._timer.start();
			}
		},

		_renewChildrenAdvicer: function() {
			if (this._childrenAdvicer) {
				this._childrenAdvicer.remove();
			}
			this._childrenAdvicer = aspect.after(
				this.tree._gridTree.collection,
				'getChildren',
				lang.hitch(this, '_setUpTreeCache')
			);
			this.own(this._childrenAdvicer);
		},

		_treeUpdate: function() {
			var commands = {default: 'uvmm/node/query', cloudconnections: 'uvmm/cloud/query'};
			for (var type in this._treeStoreCache) {
				this.tree.model.getNodes(commands[type], lang.hitch(this, '_updateTreeStore', type));
			}
		},

		_updateTreeStore: function(type, nodes) {
			array.forEach(nodes, function(node) {
				this._treeStoreCache[type].put(node);
			}, this);
		},

		_setUpTreeCache: function(store, parentItems) {
			var parentItem = parentItems[0];
			if (parentItem.type !== "group") {
				return store;
			}
			this._treeStoreCache[parentItem.id] = store;
			return store;
		},

		_treeStoreCache: null,

		destroy: function() {
			this._timer.stop();
		}

	});
});
