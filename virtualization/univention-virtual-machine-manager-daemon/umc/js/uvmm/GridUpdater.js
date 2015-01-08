/*
 * Copyright 2014-2015 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"dojox/timing/_base",
	"dijit/Destroyable"
], function(declare, lang, array, all, timing, Destroyable) {
	return declare("umc.modules.uvmm.GridUpdater", [Destroyable], {
		grid: null, // reference to the grid
		interval: null, // interval in seconds
		intervalStartsWhenFinishedUpdate: false, // whether the timer should continue while one update process is running ("predictable") or not
		numUpdateAtOnce: -1, // number of items to update at once. <= 0: all at once
		_index: 0, // internal counter which items we updated last

		constructor: function(kwArgs) {
			lang.mixin(this, kwArgs);
			this.interval = parseInt(this.interval, 10);
			var milliseconds = 1000 * this.interval;
			this._timer = new timing.Timer(1000 * this.interval);
			this._timer.onTick = lang.hitch(this, 'updateItems');
			if (milliseconds > 0) {
				// else: interval=0 or interval=NaN
				this._timer.start();
			}
		},

		updateItems: function() {
			var items = this.getItemsForUpdate(true);
			var getItemsFromServer = this.getItemsFromServer(items);
			if (getItemsFromServer === null) {
				return;
			}
			getItemsFromServer.then(lang.hitch(this, function(newItems) {
				array.forEach(newItems, lang.hitch(this, function(newItem) {
					var id = this.grid.moduleStore.getIdentity(newItem);
					var oldItem = this.grid.getItem(id);
					if (oldItem) {
						lang.mixin(oldItem, newItem);
					}
				}));
				if (this._shallGetAllItems()) {
					var oldItems = this.grid.getAllItems();
					if (oldItems.length != newItems.length) {
						this.onItemCountChanged(oldItems.length, newItems.length);
					}
				}
				this.grid._grid.update();
				this.grid._updateContextActions();
			}));
			if (this._shallGetAllItems()) {
				this._timer.stop();
				getItemsFromServer.always(lang.hitch(this, function() {
					this._timer.start();
				}));
			}
		},

		getItemsForUpdate: function(updateIndex) {
			var items = this.grid.getAllItems();
			var lastIndex = this._index + this.numUpdateAtOnce;
			if (this._shallGetAllItems()) {
				lastIndex = items.length;
			}
			if (updateIndex) {
				this._index += this.numUpdateAtOnce;
				if (lastIndex >= items.length) {
					this._index = 0;
				}
			}
			return items.slice(this._index, lastIndex);
		},

		getQuery: function(items) {
			if (this._shallGetAllItems()) {
				return this.grid.query;
			}
		},

		_shallGetAllItems: function() {
			return this.numUpdateAtOnce <= 0;
		},

		getItemsFromServer: function(items) {
			if (this._shallGetAllItems()) {
				var query = this.getQuery(items);
				if (query) {
					return this.grid.moduleStore.query(this.getQuery(items));
				} else {
					return null;
				}
			} else {
				var deferreds = array.map(items, lang.hitch(this, function(item) {
					return this.grid.moduleStore.get(this.getSingle(item));
				}));
				return all(deferreds).then(function(results) {
					return results;
				});
			}
		},

		onItemCountChanged: function(oldCount, newCount) {
		},

		destroy: function() {
			this._timer.stop();
		}
	});
});
