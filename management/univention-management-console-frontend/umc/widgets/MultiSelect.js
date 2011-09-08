/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.MultiSelect");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets._SelectMixin");
dojo.require("umc.tools");
dojo.require("dojox.grid.EnhancedGrid");
dojo.require("dojox.grid.cells");
dojo.require("dojox.grid.enhanced.plugins.IndirectSelection");

dojo.declare("umc.widgets.MultiSelect", [ dojox.grid.EnhancedGrid, umc.widgets._SelectMixin, umc.widgets.StandbyMixin ], {
	// summary:
	//		This class represents a MultiSelect widget. Essentially, it adapts a DataGrid
	//		to the behaviour expected from a MultiSelect widget.

	// size: Integer
	//		The attribute 'size' is mapped to 'autoHeight'.

	// value: String[]
	//		The widgets value, an array of strings containing all elements that are selected.
	value: [],

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

	postCreate: function() {
		this.inherited(arguments);

		// hide the header
		dojo.query('.dojoxGridHeader', this.domNode).style('height', '0px');
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
	},

	_getValueAttr: function() {
		// get all selected items
		var items = this.selection.getSelected();
		var vars = [];
		for (var iitem = 0; iitem < items.length; ++iitem) {
			vars.push(this.store.getValue(items[iitem], 'id'));
		}
		return vars; // String[]
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


