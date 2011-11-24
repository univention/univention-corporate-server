/*
 * Copyright 2011 Univention GmbH
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
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.MultiSelect");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets._SelectMixin");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.tools");
dojo.require("dojox.grid.EnhancedGrid");
dojo.require("dojox.grid.cells");
dojo.require("dojox.grid.enhanced.plugins.IndirectSelection");

dojo.declare("umc.widgets.MultiSelect", [ dojox.grid.EnhancedGrid, umc.widgets._FormWidgetMixin, umc.widgets._SelectMixin, umc.widgets.StandbyMixin ], {
	// summary:
	//		This class represents a MultiSelect widget. Essentially, it adapts a DataGrid
	//		to the behaviour expected from a MultiSelect widget.

	// size: Integer
	//		The attribute 'size' is mapped to 'autoHeight'.

	// value: String[]
	//		The widgets value, an array of strings containing all elements that are selected.
	value: [],

	_loadingDeferred: null,

	// we need the plugin for selection via checkboxes
	plugins : {
		indirectSelection: {
			headerSelector: true,
			name: 'Selection',
			width: '25px',
			styles: 'text-align: center;'
		}
	},

	// simple grid structure, only one column
	structure: [{
		field: 'label',
		name: 'Name',
		width: '100%'
	}],


	// the widget's class name as CSS class
	'class': 'umcMultiSelect',

	// force the height of the widget
	height: '110px',

	postMixInProperties: function() {
		this.inherited(arguments);

		// in case 'value' is not specified, generate a new array
		if (!dojo.isArray(this.value)) {
			this.value = [];
		}

		// initiate a new Deferred object
		this._loadingDeferred = new dojo.Deferred();
	},

	postCreate: function() {
		this.inherited(arguments);

		// hide the header
		dojo.query('.dojoxGridHeader', this.domNode).style('height', '0px');

		// send an onChange event when the selection has changed
		dojo.connect(this, 'onSelectionChanged', function() {
			this.onChange(this.get('value'));
		});
	},

	_getSizeAttr: function() {
		return this.get('autoHeight');
	},

	_setSizeAttr: function(newVal) {
		this.set('autoHeight', newVal);
	},

	_setValueAttr: function(/*String|String[]*/ values) {
		// in case we have a string, assume it is a comma separated list of values
		// and transform it into an array
		if (dojo.isString(values)) {
			values = values.split(',');
		}

		// ignore anything that is not an array at this point
		if (!dojo.isArray(values)) {
			values = [];
		}

		// cache results
		this.value = values;

		// in case the values are loading, we need to postpone the manipulation
		// of the selection after the grid has been loaded
		this._loadingDeferred.then(dojo.hitch(this, function() {
			// map all selected items into a dict for faster access
			var _map = {};
			dojo.forEach(values, function(i) {
				_map[i] = true;
			});

			// deselect all elements and update the given selection according to the values
			this.selection.clear();
			this.store.fetch({
				onItem: dojo.hitch(this, function(iitem) {
					// check whether the item has been selected
					var iid = this.store.getValue(iitem, 'id');
					if (iid in _map) {
						// item in in the given list, activate the selection
						var idx = this.getItemIndex(iitem);
						this.selection.addToSelection(idx);
					}
				})
			});
		}));
	},

	_getValueAttr: function() {
		// if the grid is loading, return the cached value
		if (this._loadingDeferred.fired < 0) {
			return this.value; // String[]
		}

		// otherwise get all selected items
		var items = this.selection.getSelected();
		var vars = [];
		for (var iitem = 0; iitem < items.length; ++iitem) {
			vars.push(this.store.getValue(items[iitem], 'id'));
		}
		return vars; // String[]
	},

	getSelectedItems: function() {
		// summary:
		//		Returns all select items is array of dicts (with id and label entries)
		var vals = this.get('value');
		if (!dojo.isArray(vals)) {
			return [];
		}

		// create a map of the selected ids
		var map = {};
		dojo.forEach(vals, function(iid) {
			map[iid] = true;
		});

		// get all store items and find the labels for the selected ones
		var items = dojo.filter(this.getAllItems(), function(iitem) {
			return iitem.id in map;
		});
		return items;
	},

	onLoadDynamicValues: function() {
		this.inherited(arguments);

		// initiate a new Deferred, if the current one has already been resolved
		if (this._loadingDeferred.fired >= 0) {
			this._loadingDeferred = new dojo.Deferred();
		}

		// start standby animation
		this.standby(true);
	},

	onValuesLoaded: function(values) {
		this.inherited(arguments);

		// resolve the Deferred
		if (this._loadingDeferred.fired < 0) {
			this._loadingDeferred.resolve();
		}

		// stop standby animation and re-render
		this.standby(false);
		this.render();
	},

	onChange: function(newValues) {
		// event stub
	}

	/*adaptHeight: function() {
		this.inherited(arguments);
		console.log('# adaptHeight');
		if (this.height) {
			console.log('# height', this.height, parseInt(this.height, 10));
			this.scroller.windowHeight = parseInt(this.height, 10);
		}
	}*/
});


