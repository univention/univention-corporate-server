/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.MultiInput");

dojo.require("umc.widgets.ContainerWidget");
//dojo.require("umc.widgets.HiddenInput");
dojo.require("umc.tools");

dojo.declare("umc.widgets.MultiInput", [ umc.widgets.ContainerWidget, umc.i18n.Mixin ], {
	// summary:
	//		Simple widget that displays a widget/HTML code with a label above.

	// subtypes: Object[]
	//		Essentially an array of object that describe the widgets for one element
	//		of the MultiInput widget, the 'name' needs not to be specified, this
	//		property is passed to umc.tools.renderWidgets().
	subtypes: null,

	name: '',

	value: null,

	delimiter: '',

	i18nClass: 'umc.app',

	_widgets: null,

	_nRenderedElements: 0,

	_rowContainers: null,

	_widgets: null,

	_newButton: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// check the property 'subtypes'
		umc.tools.assert(dojo.isArray(this.subtypes), 
				'umc.widgets.ContainerWidget: The property subtypes needs to be a string or an array of strings: ' + this.subtypes);

		// initiate other properties
		this._rowContainers = [];
		this._widgets = [];
	},

	buildRendering: function() {
		this.inherited(arguments);

		// add empty element
		this._appendElements(1);
	},

	_setAllValues: function(_valList) {
		var valList = _valList;
		if (!dojo.isArray(valList)) {
			valList = [];
		}

		// adjust the number of rows
		var diff = valList.length - this._nRenderedElements;
		if (diff > 0) {
			this._appendElements(diff);
		}
		else if (diff < 0) {
			this._popElements(-diff);
		}

		// set all values
		dojo.forEach(valList, function(ival, irow) {
			var rowVals = [];
			if (dojo.isString(ival)) {
				// entry is string .. we need to parse it if we have a delimiter
				if (this.delimiter) {
					rowVals = ival.split(this.delimiter);
				}
				else {
					rowVals = [ ival ];
				}
			}
			else if (dojo.isArray(ival)) {
				rowVals = ival;
			}

			// set values
			for (var j = 0; j < this.subtypes.length; ++j) {
				var val = j >= rowVals.length ? '' : rowVals[j];
				this._widgets[irow][j].set('value', val);
			}
		}, this);
	},
	
	_setValueAttr: function(vals) {
		// remove all empty elements at the end
		while (vals.length && !vals[vals.length - 1]) {
			vals.pop();
		}

		// append an empty element
		this._setAllValues(vals.concat(['']));
	},

	_getAllValues: function() {
		var i, j, vals = [], rowVals = [];
		for (i = 0; i < this._widgets.length; ++i) {
			rowVals = [];
			for (j = 0; j < this._widgets[i].length; ++j) {
				rowVals.push(this._widgets[i][j].get('value'));
			}
			vals.push(rowVals.join(this.delimiter));
		}
		return vals;
	},

	_getValueAttr: function() {
		// remove the last empty entries
		var vals = this._getAllValues();
		while (vals.length && !vals[vals.length - 1]) {
			vals.pop();
		}
		return vals;
	},

	_removeNewButton: function() {
		if (this._newButton) {
			this._newButton.destroyRecursive();
			this._newButton = null;
		}
	},

	_addNewButton: function() {
		// add the 'new' button to the last row
		if (this._nRenderedElements < 1) {
			return;
		}

		// verify whether label information for subtypes are given
		var hasSubTypeLabels = false;
		dojo.forEach(this.subtypes, function(iwidget) {
			hasSubTypeLabels = hasSubTypeLabels || iwidget.label;
		});

		// create 'new' button
		var btn = new dijit.form.Button({
			label: '<b>+</b>',
			//iconClass: 'dijitIconNewTask',
			onClick: dojo.hitch(this, '_appendElements', 1)
		});

		// wrap a button with a LabelPane
		this._newButton = new umc.widgets.LabelPane({
			content: btn,
			label: this._nRenderedElements === 1 && hasSubTypeLabels ? '&nbsp;' : '' // only keep the label for the first row
		});

		// add button to last row
		this._rowContainers[this._rowContainers.length - 1].addChild(this._newButton);
	},

	_appendElements: function(n) {
		if (n < 1) {
			return;
		}

		// remove the 'new' button
		this._removeNewButton();

		for (var irow = this._nRenderedElements; irow < this._nRenderedElements + n; ++irow) {
			// add all other elements with '__' such that they will be ignored by umc.widgets.form
			var order = [], widgetConfs = [];
			dojo.forEach(this.subtypes, function(iwidget, i) {
				// add the widget configuration dict to the list of widgets
				var iname = '__' + this.name + '-' + irow + '-' + i;
				widgetConfs.push(dojo.mixin({}, iwidget, {
					name: iname
				}));

				// add the name of the widget to the list of widget names
				order.push(iname);
			}, this);

			// render the widgets and layout them
			var widgets = umc.tools.renderWidgets(widgetConfs);
			var visibleWidgets = dojo.map(order, function(iname) {
				return widgets[iname];
			});
			var rowContainer = new umc.widgets.ContainerWidget({});
			var hasSubTypeLabels = false;
			dojo.forEach(order, function(iname) {
				// add widget to row container (wrapped by a LabelPane)
				hasSubTypeLabels = hasSubTypeLabels || widgets[iname].label;
				rowContainer.addChild(new umc.widgets.LabelPane({
					content: widgets[iname],
					label: irow !== 0 ? '' : null // only keep the label for the first row
				}));
			}, this);

			// add a 'remove' button at the end of the row
			var button = new dijit.form.Button({
				label: '<b>-</b>',
				//iconClass: 'dijitIconDelete',
				onClick: dojo.hitch(this, '_removeElement', irow)
			});
			rowContainer.addChild(new umc.widgets.LabelPane({
				content: button,
				label: irow === 0 && hasSubTypeLabels ? '&nbsp;' : '' // only keep the label for the first row
			}));

			// add row
			this.addChild(rowContainer);
			this._rowContainers.push(rowContainer);
			this._widgets.push(visibleWidgets);
		}

		// update the number of render elements
		this._nRenderedElements += n;

		// add the new button
		this._addNewButton();
	},

	_popElements: function(n) {
		if (n < 1) {
			return;
		}

		// remove the 'new' button
		this._removeNewButton();
		
		for (var irow = this._nRenderedElements - 1; irow >= this._nRenderedElements - n; --irow) {
			// destroy the row container
			this._rowContainers[irow].destroyRecursive();

			// clean up internal arrays
			this._rowContainers.pop();
			this._widgets.pop();
		}

		// update the number of render elements
		this._nRenderedElements -= n;

		// add the new button
		this._addNewButton();
	},

	_removeElement: function(idx) {
		var vals = this._getAllValues();
		vals.splice(idx, 1);

		// add an empty line in case we removed the last element
		if (!vals.length) {
			vals.push('');
		}
		this._setAllValues(vals);
	}
});


