/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.MultiInput");

dojo.require("umc.widgets.ContainerWidget");

dojo.declare("umc.widgets.MultiInput", [ umc.widgets.ContainerWidget, umc.i18n.Mixin ], {
	// summary:
	//		Simple widget that displays a widget/HTML code with a label above.

	// subTypes: Object[]
	//		Essentially an array of object that describe the widgets for one element
	//		of the MultiInput widget, the 'name' needs not to be specified, this
	//		property is passed to umc.tools.renderWidgets().
	subTypes: null,

	name: '',

	value: null,

	delimiter: '',

	i18nClass: 'umc.app',

	_nTypes: 0,

	_widgets: null,

	_nRenderedElements: 0,

	_widgetContainer: null,

	_toolbarContainer: null,

	_rowContainers: null,

	_hiddenInputs: null,

	_widgets: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// cache the number of specified subtypes
		umc.tools.assert(dojo.isString(this.subTypes) || dojo.isArray(this.subTypes), 
				'umc.widgets.ContainerWidget: The property subTypes needs to be a string or an array of strings: ' + this.subTypes);
		this._nTypes = dojo.isString(this.subTypes) ? 1 : this.subTypes.length;

		// initiate other properties
		this._rowContainers = [];
		this._hiddenInputs = [];
		this._widgets = [];
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create basic containers for layout
		this._widgetContainer = new umc.widgets.ContainerWidget({});
		this._toolbarContainer = new umc.widgets.ContainerWidget({});
		this.addChild(this._widgetContainer);
		this.addChild(this._toolbarContainer);

		// add 'new element' button
		this._toolbarContainer.addChild(new dijit.form.Button({
			label: this._('Add new element'),
			onClick: dojo.hitch(this, function() {
				this._appendElements(1);
			}, this)
		}));

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
		console.log('# _setValueAttr: diff=' + diff);
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
				// entry is string .. we need to parse it
				rowVals = ival.split(this.delimiter);
			}
			else if (dojo.isArray(ival)) {
				rowVals = ival;
			}

			// set values
			for (var j = 0; j < this._nTypes; ++j) {
				var val = j >= rowVals.length ? '' : rowVals[j];
				this._widgets[irow][j].set('value', val);
			}
		}, this);
	},
	
	_setValueAttr: function(valList) {
		// append an empty element
		console.log('# _setValueAttr: ' + valList);
		this._setAllValues(valList.concat(['']));
	},

	_getAllValues: function() {
		var vals = [];
		dojo.forEach(this._hiddenInputs, function(iwidget) {
			vals.push(iwidget.get('value'));
		});
		console.log('# _getAllValues: ' + vals);
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

	_updateHiddenInput: function(hiddenWidget, visibleWidgets) {
		var vals = dojo.map(visibleWidgets, function(iwidget) {
			return iwidget.get('value');
		});
		var valuesSet = false;
		dojo.forEach(vals, function(ival) {
			valuesSet = valuesSet || ival;
		});
		if (!valuesSet) {
			vals = [];
		}
		hiddenWidget.set('value', vals.join(this.delimiter));
	},

	_appendElements: function(n) {
		for (var irow = this._nRenderedElements; irow < this._nRenderedElements + n; ++irow) {
			// add a hidden element that contains the value that is passed over to the server
			var hiddenWidgetName = this.name + '[' + irow + ']';
			var widgetConfs = [{
				type: 'HiddenInput',
				name: hiddenWidgetName
			}];

			// add all other elements with '__' such that they will be ignored by umc.widgets.form
			var order = [];
			dojo.forEach(this.subTypes, function(iwidget, i) {
				// add the widget configuration dict to the list of widgets
				var iname = '__' + this.name + '-' + irow + '-' + i;
				widgetConfs.push(dojo.mixin({}, iwidget, {
					name: iname
				}));

				// add the name of the widget to the list of widget names
				order.push(iname);
			}, this);

			// render the widgets, layout them, and connect to onChange events in order to
			// update the hidden input field
			var widgets = umc.tools.renderWidgets(widgetConfs);
			var hiddenWidget = widgets[hiddenWidgetName];
			var visibleWidgets = dojo.map(order, function(iname) {
				return widgets[iname];
			});
			var rowContainer = new umc.widgets.ContainerWidget({});
			rowContainer.addChild(hiddenWidget);
			dojo.forEach(order, function(iname) {
				// add widget to row container (wrapped by a LabelPane)
				rowContainer.addChild(new umc.widgets.LabelPane({
					content: widgets[iname]
				}));

				// connect to widget's onChange event
				dojo.connect(widgets[iname], 'onChange', dojo.hitch(this, '_updateHiddenInput', hiddenWidget, visibleWidgets));
			}, this);

			// add a 'remove' button at the end of the row
			var button = new dijit.form.Button({
				label: this._('Remove'),
				onClick: dojo.hitch(this, '_removeElement', irow)
			});
			rowContainer.addChild(new umc.widgets.LabelPane({
				content: button
			}));

			// register the hidden input field
			this.onWidgetAdd(hiddenWidget);

			// add row
			this._widgetContainer.addChild(rowContainer);
			this._rowContainers.push(rowContainer);
			this._hiddenInputs.push(hiddenWidget);
			this._widgets.push(visibleWidgets);
		}

		// update the number of render elements
		this._nRenderedElements += n;
	},

	_popElements: function(n) {
		for (var irow = this._nRenderedElements - 1; irow >= this._nRenderedElements - n; --irow) {
			// register removal of hidden input infield
			this.onWidgetRemove(this._hiddenInputs[irow]);

			// destroy the row container
			this._rowContainers[irow].destroyRecursive();

			// clean up internal arrays
			this._rowContainers.pop();
			this._hiddenInputs.pop();
			this._widgets.pop();
		}

		// update the number of render elements
		this._nRenderedElements -= n;
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

	onWidgetAdd: function(widget) {
		// event stub
	},

	onWidgetRemove: function(widget) {
		// event stub
	}
});


