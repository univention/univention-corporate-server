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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/dom-class",
	"dojox/grid/EnhancedGrid",
	"../tools",
	"./_SelectMixin",
	"./_FormWidgetMixin",
	"./StandbyMixin",
	"./_RegisterOnShowMixin",
	"umc/i18n!",
	"dojox/grid/enhanced/plugins/IndirectSelection",
	"dojox/grid/cells"
], function(declare, lang, array, Deferred, domClass, EnhancedGrid, tools, _SelectMixin, _FormWidgetMixin, StandbyMixin, _RegisterOnShowMixin, _) {
	return declare("umc.widgets.MultiSelect", [ EnhancedGrid, _FormWidgetMixin, _SelectMixin, StandbyMixin, _RegisterOnShowMixin ], {
		// summary:
		//		This class represents a MultiSelect widget. Essentially, it adapts a DataGrid
		//		to the behavior expected from a MultiSelect widget.

		// size: Integer
		//		The attribute 'size' is mapped to 'autoHeight'.

		// value: String[]
		//		The widgets value, an array of strings containing all elements that are selected.
		value: null,

		_loadingDeferred: null,

		// display the labe above the widget
		labelPosition: 'top',

		// bool whether a header to select all entries should be shown
		showHeader: false,
		// label of select all entries header
		headerLabel: _('Select all'),

		// we need the plugin for selection via checkboxes
		plugins : {
			indirectSelection: {
				headerSelector: true,
				name: 'Selection',
				width: '25px',
				styles: 'text-align: center;'
			}
		},

		// the widget's class name as CSS class
		baseClass: EnhancedGrid.prototype.baseClass + ' umcMultiSelect',

		// force the height of the widget
		height: '110px',

		postMixInProperties: function() {
			// initiate a new Deferred object
			this._loadingDeferred = new Deferred();

			this.inherited(arguments);

			// simple grid structure, only one column
			this.structure = [{
				field: 'label',
				name: this.headerLabel,
				width: '100%'
			}];

			// in case 'value' is not specified, generate a new array
			if (!(this.value instanceof Array)) {
				this.value = [];
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			// hide header if showHeader is false
			domClass.toggle(this.domNode, 'umcMultiSelectNoHeader', !this.showHeader);

			// send an onChange event when the selection has changed
			this.on('selectionChanged', lang.hitch(this, function() {
				if (array.some(this.selection.getSelected(), function(v) { return v === null; })) {
					// not yet startup'ed
					return;
				}
				this._set('value', this.get('value'));
			}));
		},

		startup: function() {
			this.inherited(arguments);
			this.resize();
			this._registerAtParentOnShowEvents(lang.hitch(this, 'resize'));
		},

		_setCustomValue: function() {
			// overwrite handling of _SelectMixin
			this.value = null; // force notification of watch handlers
			this.set('value', this._initialValue);
			this._resetValue = this._initialValue;
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
			if (typeof values == "string") {
				values = values.split(',');
			}

			// ignore anything that is not an array at this point
			if (!(values instanceof Array)) {
				values = [];
			}

			if (tools.isEqual(values, this.get('value'))) {
				// value did not change
				return;
			}

			// cache results
			this.value = values;

			// in case the values are loading, we need to postpone the manipulation
			// of the selection after the grid has been loaded
			this._loadingDeferred.then(lang.hitch(this, function() {
				// map all selected items into a dict for faster access
				var _map = {};
				array.forEach(values, function(i) {
					_map[i] = true;
				});

				// deselect all elements and update the given selection according to the values
				this.selection.clear();
				this.store.fetch({
					onItem: lang.hitch(this, function(iitem) {
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
			if (!this._loadingDeferred.isFulfilled()) {
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
			if (!(vals instanceof Array)) {
				return [];
			}

			// create a map of the selected ids
			var map = {};
			array.forEach(vals, function(iid) {
				map[iid] = true;
			});

			// get all store items and find the labels for the selected ones
			var items = array.filter(this.getAllItems(), function(iitem) {
				return iitem.id in map;
			});
			return items;
		},

		onLoadDynamicValues: function() {
			this.inherited(arguments);

			// initiate a new Deferred, if the current one has already been resolved
			if (this._loadingDeferred.isFulfilled()) {
				this._loadingDeferred = new Deferred();
			}

			// start standby animation
			this.standby(true);
		},

		onValuesLoaded: function(values) {
			this.inherited(arguments);

			// resolve the Deferred
			if (!this._loadingDeferred.isFulfilled()) {
				this._loadingDeferred.resolve();
			}

			// stop standby animation and re-render
			this.standby(false);
			this.render();
		},

		/*adaptHeight: function() {
			this.inherited(arguments);
			console.log('# adaptHeight');
			if (this.height) {
				console.log('# height', this.height, parseInt(this.height, 10));
				this.scroller.windowHeight = parseInt(this.height, 10);
			}
		}*/

		render: function() {
			domClass.toggle(this.domNode, 'umcMultiSelectWithContent', this.get('rowCount'));
			this.inherited(arguments);
		}
	});
});

