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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.MultiInput");

dojo.require("dijit.form.Button");
dojo.require("umc.widgets.ContainerWidget");
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

	// max: Number
	//		Maximal number of elements.
	max: Infinity,

	// the widget's class name as CSS class
	'class': 'umcMultiInput',

	depends: null,

	name: '',

	value: null,

	delimiter: '',

	disabled: false,

	i18nClass: 'umc.app',

	_widgets: null,

	_nRenderedElements: 0,

	_rowContainers: null,

	_newButton: null,

	_lastDepends: null,

	_createHandler: function(ifunc) {
		// This handler will be called by all subwidgets of the MultiInput widget.
		// When the first request comes in, we will execute the function to compute
		// the dynamic values. Request within a small time interval will get the
		// same result in order to have a caching mechanism for multiple queries.
		var _valueOrDeferred = null;
		var _lastCall = 0;

		return function(iname, options) {
			// current timestamp
			var currentTime = (new Date()).getTime();
			var elapsedTime = Math.abs(currentTime - _lastCall);
			_lastCall = currentTime;

			// if the elapsed time is too big, or we have not a Deferred object (i.e., value
			// are directly computed by a function without AJAX calls), execute the function
			if (elapsedTime > 100 || !(dojo.getObject('then', false, _valueOrDeferred) && dojo.getObject('cancel', false, _valueOrDeferred))) {
				_valueOrDeferred = ifunc(options);
			}
			//console.log('# new deferred: ', iname, ' elapsedTime: ', elapsedTime, ' options: ', dojo.toJson(options), ' values: ', _valueOrDeferred);

			// return the value
			return _valueOrDeferred;
		};
	},

	postMixInProperties: function() {
		this.inherited(arguments);

		this.sizeClass = null;

		// check the property 'subtypes'
		umc.tools.assert(dojo.isArray(this.subtypes),
				'umc.widgets.ContainerWidget: The property subtypes needs to be a string or an array of strings: ' + this.subtypes);

		// initiate other properties
		this._rowContainers = [];
		this._widgets = [];

		// we need to rewire the dependencies through this widget to the row widgets
		this.depends = [];
		dojo.forEach(this.subtypes, function(iwidget, i) {
			// gather all dependencies so form can notify us
			dojo.forEach(umc.tools.stringOrArray(iwidget.depends), function(idep) {
				if (dojo.indexOf(this.depends, idep) < 0) {
					this.depends.push(idep);
				}
			}, this);

			// parse the dynamic value function and create a handler
			var ifunc = umc.tools.stringOrFunction(iwidget.dynamicValues, this.umcpCommand || umc.tools.umcpCommand);
			var handler = dojo.hitch(this, this._createHandler(ifunc, iwidget));

			// replace the widget handler for dynamicValues with our version
			iwidget.dynamicValues = handler;
		}, this);
	},

	buildRendering: function() {
		this.inherited(arguments);

		// add empty element
		this._appendElements(1);
	},

	_loadValues: function(depends) {
		// delegate the call to _loadValues to all widgets
		this._lastDepends = depends;
		dojo.forEach(this._widgets, function(iwidgets) {
			dojo.forEach(iwidgets, function(jwidget) {
				if ('_loadValues' in jwidget) {
					jwidget._loadValues(depends);
				}
			});
		});
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
			if (irow >= this._widgets.length) {
				// break
				return false;
			}

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

	_setValueAttr: function(_vals) {
		// remove all empty elements
		var vals = dojo.filter(_vals, function(ival) {
			return (dojo.isString(ival) && '' !== ival) || (dojo.isArray(ival) && ival.length);
		});

		// append an empty element
		vals.push([]);

		// set the values
		this._setAllValues(vals);
	},

	_setDisabledAttr: function ( value ) {
		var i;
		for ( i = 0; i < this._rowContainers.length; ++i) {
			dojo.forEach( this._rowContainers[ i ].getChildren(), function( widget ) {
				widget.set( 'disabled', value );
			} );
		}
		this.disabled = value;
	},

	_getAllValues: function() {
		var i, j, val, isSet, vals = [], rowVals = [];
		for (i = 0; i < this._widgets.length; ++i) {
			rowVals = [];
			isSet = false;
			for (j = 0; j < this._widgets[i].length; ++j) {
				val = this._widgets[i][j].get('value');
				isSet = isSet || ('' !== val);
				if (!umc.tools.inheritsFrom(this._widgets[i][j], 'umc.widgets.Button')) {
					rowVals.push(val);
				}
			}
			if (this.delimiter) {
				// delimiter is given, represent rows as strings 
				// ... and empty rows as empty string
				vals.push(isSet ? rowVals.join(this.delimiter) : '');
			}
			else {
				// delimiter is not given, represent rows as arrays
				// ... and empty rows as empty array
				vals.push(isSet ? rowVals : []);
			}
		}
		return vals;
	},

	_getValueAttr: function() {
		// only return non-empty entries
		var vals = [];
		dojo.forEach(this._getAllValues(), function(ival) {
			if (dojo.isString(ival) && '' !== ival) {
				vals.push(ival);
			}
			else if (dojo.isArray(ival) && ival.length) {
				// if we only have one subtype, do not use arrays as representation
				vals.push(1 == ival.length ? ival[0] : ival);
			}
		});
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
			iconClass: 'umcIconAdd',
			onClick: dojo.hitch(this, '_appendElements', 1),
			'class': 'umcMultiInputAddButton'
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

		var nFinal = this._nRenderedElements + n;
		for (var irow = this._nRenderedElements; irow < nFinal && irow < this.max; ++irow, ++this._nRenderedElements) {
			// add all other elements with '__' such that they will be ignored by umc.widgets.form
			var order = [], widgetConfs = [];
			dojo.forEach(this.subtypes, function(iwidget, i) {
				// add the widget configuration dict to the list of widgets
				var iname = '__' + this.name + '-' + irow + '-' + i;
				var iconf = dojo.mixin({}, iwidget, {
					disabled: this.disabled,
					name: iname,
					value: '',
					dynamicValues: dojo.partial(iwidget.dynamicValues, iname)
				});
				widgetConfs.push(iconf);

				// add the name of the widget to the list of widget names
				order.push(iname);
			}, this);


			// render the widgets
			var widgets = umc.render.widgets(widgetConfs);

			// if we have a button, we need to pass the value and index if the
			// current element
			umc.tools.forIn(widgets, function(ikey, iwidget) {
				var myrow = irow;
				if (umc.tools.inheritsFrom(iwidget, 'umc.widgets.Button') && dojo.isFunction(iwidget.callback)) {
					var callbackOrg = iwidget.callback;
					iwidget.callback = dojo.hitch(this, function() {
						callbackOrg(this.get('value')[myrow], myrow);
					});
				}
			}, this);

			// find out whether all items do have a label
			var hasSubTypeLabels = dojo.filter(this.subtypes, function(iwidget) {
				return iwidget.label;
			}).length > 0;

			// layout widgets
			var visibleWidgets = dojo.map(order, function(iname) {
				return widgets[iname];
			});
			var rowContainer = this.adopt(umc.widgets.ContainerWidget, {});
			dojo.forEach(order, function(iname) {
				// add widget to row container (wrapped by a LabelPane)
				// only keep the label for the first row
				var iwidget = widgets[iname];
				var label = irow !== 0 ? '' : null;
				if (umc.tools.inheritsFrom(iwidget, 'umc.widgets.Button')) {
					label = irow !== 0 ? '' : '&nbsp;';
				}
				rowContainer.addChild(new umc.widgets.LabelPane({
					disabled: this.disabled,
					content: iwidget,
					label: label
				}));

				// register to 'onChange' events
				this.connect(iwidget, 'onChange', function() {
					this.onChange(this.get('value'));
				});
			}, this);

			// add a 'remove' button at the end of the row
			var button = this.adopt(dijit.form.Button, {
				disabled: this.disabled,
				iconClass: 'umcIconDelete',
				onClick: dojo.hitch(this, '_removeElement', irow),
				'class': 'umcMultiInputRemoveButton'
			});
			rowContainer.addChild(new umc.widgets.LabelPane({
				content: button,
				label: irow === 0 && hasSubTypeLabels ? '&nbsp;' : '' // only keep the label for the first row
			}));

			// add row
			this._widgets.push(visibleWidgets);
			this._rowContainers.push(rowContainer);
			rowContainer.startup();
			this.addChild(rowContainer);

			// call the _loadValues method by hand
			dojo.forEach(order, function(iname) {
				var iwidget = widgets[iname];
				if ('_loadValues' in iwidget) {
					iwidget._loadValues(this._lastDepends);
				}
			}, this);
		}

		// add the new button 
		if (this._nRenderedElements < this.max) {
			this._addNewButton();
		}
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
				areValid = areValid && (!this._widgets[i][j].isValid || this._widgets[i][j].isValid());
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
	},

	onChange: function(newValue) {
		// stub for onChange event
	}
});


