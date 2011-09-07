/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.MultiInput");

dojo.require("dijit.form.Button");
dojo.require("umc.widgets.ContainerWidget");
//dojo.require("umc.widgets.HiddenInput");
dojo.require("umc.tools");
dojo.require("umc.render");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.widgets.MultiInput", [
	umc.widgets.ContainerWidget,
	umc.widgets._FormWidgetMixin,
	umc.widgets._WidgetsInWidgetsMixin,
	umc.i18n.Mixin
], {
	// summary:
	//		Widget for a small list of simple and complex entries. An entry can be one or
	//		multiple input fields (TextBox, ComboBox, etc.).

	// subtypes: Object[]
	//		Essentially an array of object that describe the widgets for one element
	//		of the MultiInput widget, the 'name' needs not to be specified, this
	//		property is passed to umc.render.widgets().
	subtypes: null,

	// the widget's class name as CSS class
	'class': 'umcMultiInput',

	name: '',

	value: null,

	delimiter: '',

	disabled: false,

	i18nClass: 'umc.app',

	_widgets: null,

	_nRenderedElements: 0,

	_rowContainers: null,

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

				// for dynamic combo boxes, we need to save the value as "initial value"
				if (this._widgets[irow][j].setInitialValue) {
					this._widgets[irow][j].setInitialValue(val, false);
				}
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
		var i, j, val, isSet, vals = [], rowVals = [];
		for (i = 0; i < this._widgets.length; ++i) {
			rowVals = [];
			isSet = false;
			for (j = 0; j < this._widgets[i].length; ++j) {
				val = this._widgets[i][j].get('value');
				isSet = isSet || ('' !== val);
				rowVals.push(val);
			}
			vals.push(isSet ? rowVals.join(this.delimiter) : '');
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
			this.orphan(this._newButton, true);
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
		var btn = this.adopt(dijit.form.Button, {
			disabled: this.disabled,
			label: '<b>+</b>',
			//iconClass: 'dijitIconNewTask',
			onClick: dojo.hitch(this, '_appendElements', 1)
		});

		// wrap a button with a LabelPane
		this._newButton = this.adopt(umc.widgets.LabelPane, {
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
					disabled: this.disabled,
					name: iname,
					value: ''
				}));

				// add the name of the widget to the list of widget names
				order.push(iname);
			}, this);

			// render the widgets and layout them
			var widgets = umc.render.widgets(widgetConfs);
			var visibleWidgets = dojo.map(order, function(iname) {
				return widgets[iname];
			});
			var rowContainer = this.adopt(umc.widgets.ContainerWidget, {});
			var hasSubTypeLabels = false;
			dojo.forEach(order, function(iname) {
				// add widget to row container (wrapped by a LabelPane)
				hasSubTypeLabels = hasSubTypeLabels || widgets[iname].label;
				rowContainer.addChild(new umc.widgets.LabelPane({
					disabled: this.disabled,
					content: widgets[iname],
					label: irow !== 0 ? '' : null // only keep the label for the first row
				}));

				// register to 'onChange' events
				this.connect(widgets[iname], 'onChange', 'onChange');
			}, this);

			// add a 'remove' button at the end of the row
			var button = this.adopt(dijit.form.Button, {
				disabled: this.disabled,
				label: '<b>-</b>',
				//iconClass: 'dijitIconDelete',
				onClick: dojo.hitch(this, '_removeElement', irow)
			});
			rowContainer.addChild(new umc.widgets.LabelPane({
				content: button,
				label: irow === 0 && hasSubTypeLabels ? '&nbsp;' : '' // only keep the label for the first row
			}));
			rowContainer.startup();

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
			this.orphan(this._rowContainers[irow], true);

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
	},

	isValid: function() {
		var areValid = true;
		var i, j;
		for (i = 0; i < this._widgets.length; ++i) {
			for (j = 0; j < this._widgets[i].length; ++j) {
				areValid = areValid && this._widgets[i][j].isValid();
			}
		}
		return areValid;
	},

	setValid: function(/*Boolean|Boolean[]*/ areValid, /*String?|String[]?*/ messages) {
		// summary:
		//		Set all child elements to valid/invalid.
		//		Parameters can be either simple values (Boolean/String) or arrays.
		//		Arrays indicate specific states for each element
		var i, j;
		for (i = 0; i < this._widgets.length; ++i) {
			var imessage = dojo.isArray(messages) ? messages[i] : messages;
			var iisValid = dojo.isArray(areValid) ? areValid[i] : areValid;
			for (j = 0; j < this._widgets[i].length; ++j) {
				this._widgets[i][j].setValid(iisValid, imessage);
			}
		}
	},

	_setBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		if (this._widget) {
			umc.tools.delegateCall(this, arguments, this._widget);
		}
	},

	_getBlockOnChangeAttr: function(/*Boolean*/ value) {
		// execute the inherited functionality in the widget's scope
		if (this._widget) {
			umc.tools.delegateCall(this, arguments, this._widget);
		}
	}
});


