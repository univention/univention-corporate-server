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
	"dojo/promise/all",
	"dojo/dom-class",
	"umc/tools",
	"umc/render",
	"umc/widgets/Button",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_FormWidgetMixin",
	"umc/widgets/LabelPane",
	"umc/i18n!"
], function(declare, lang, array, Deferred, all, domClass, tools, render, Button, ContainerWidget, _FormWidgetMixin, LabelPane, _) {
	return declare("umc.widgets.MultiInput", [ ContainerWidget, _FormWidgetMixin ], {
		// summary:
		//		Widget for a small list of simple and complex entries. An entry can be one or
		//		multiple input fields (TextBox, ComboBox, etc.).

		// subtypes: Object[]
		//		Essentially an array of object that describe the widgets for one element
		//		of the MultiInput widget, the 'name' needs not to be specified, this
		//		property is passed to render.widgets().
		subtypes: null,

		// max: Number
		//		Maximal number of elements.
		max: Infinity,

		// the widget's class name as CSS class
		baseClass: 'umcMultiInput',

		depends: null,

		name: '',

		value: null,

		delimiter: '',

		disabled: false,

		displayLabel: false,

		newEntryButtonLabel: _('New entry'),

		newEntryButtonIconClass: 'dijitNoIcon',

		_widgets: null,

		_nRenderedElements: 0,

		_rowContainers: null,

		_newEntryButton: null,

		_lastDepends: null,

		_valuesLoaded: false,

		// deferred for overall process (built + loaded dependencies)
		_readyDeferred: null,

		_pendingDeferreds: null,

		// deferred for built process
		_allWidgetsBuiltDeferred: null,

		_startupDeferred: null,

		_blockChangeEvents: false,

		_hasSubtypeLabel: false,

		_createHandler: function(ifunc) {
			// This handler will be called by all subwidgets of the MultiInput widget.
			// When the first request comes in, we will execute the function to compute
			// the dynamic values. Request within a small time interval will get the
			// same result in order to have a caching mechanism for multiple queries.
			var _valueOrDeferred = null;
			var _lastCall = 0;
			var _lastOptions = undefined;

			return function(iname, options) {
				// current timestamp
				var currentTime = (new Date()).getTime();
				var elapsedTime = Math.abs(currentTime - _lastCall);
				var optionsChanged = !tools.isEqual(options, _lastOptions);
				_lastCall = currentTime;
				_lastOptions = options;

				// if the elapsed time is too big, or we have not a Deferred object (i.e., value
				// are directly computed by a function without AJAX calls), execute the function
				if (elapsedTime > 100 || !(lang.getObject('then', false, _valueOrDeferred) && lang.getObject('cancel', false, _valueOrDeferred)) || optionsChanged) {
					_valueOrDeferred = ifunc(options);
				}
				//console.log('# new deferred: ', iname, ' elapsedTime: ', elapsedTime, ' options: ', json.stringify(options), ' values: ', _valueOrDeferred);

				// return the value
				return _valueOrDeferred;
			};
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// delete the size class
			this.sizeClass = null;

			// the _readyDeferred is being resolved as soon as everything has been set up
			this._readyDeferred = new Deferred();

			this._startupDeferred = new Deferred();
			this._allWidgetsBuiltDeferred = new Deferred();

			// check the property 'subtypes'
			tools.assert(this.subtypes instanceof Array,
					'umc/widgets/ContainerWidget: The property subtypes needs to be a string or an array of strings: ' + this.subtypes);

			this._hasSubtypeLabel = array.some(this.subtypes, function(iwidget) {
				return iwidget.label;
			});

			// overwrite label with subtypes label
			if (this._hasSubtypeLabel) {
				this.label = [];
				array.forEach(this.subtypes, function(itype, i) {
					this.label.push(itype.label || '&nbsp;');
				}, this);
			}

			// initiate other properties
			this._rowContainers = [];
			this._widgets = [];
			this._pendingDeferreds = {};

			// we need to rewire the dependencies through this widget to the row widgets
			this.depends = [];
			array.forEach(this.subtypes, function(iwidget) {
				// gather all dependencies so form can notify us
				array.forEach(tools.stringOrArray(iwidget.depends), function(idep) {
					if (array.indexOf(this.depends, idep) < 0) {
						this.depends.push(idep);
					}
				}, this);

				// parse the dynamic value function and create a handler
				var ifunc = tools.stringOrFunction(iwidget.dynamicValues, this.umcpCommand || lang.hitch(tools, 'umcpCommand'));
				var handler = lang.hitch(this, this._createHandler(ifunc));

				// replace the widget handler for dynamicValues with our version
				iwidget.dynamicValues = handler;

				if (iwidget.dynamicValuesInfo) {
					// UDM syntax/choices/info
					var jfunc = tools.stringOrFunction(iwidget.dynamicValuesInfo, this.umcpCommand || lang.hitch(tools, 'umcpCommand'));
					var thresholdHandler = lang.hitch(this, this._createHandler(jfunc));
					iwidget.dynamicValuesInfo = thresholdHandler;
				}
			}, this);
		},

		startup: function() {
			this.inherited(arguments);

			this._startupDeferred.resolve();
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._renderNewEntryButton();
			this._appendRows(); // empty row
		},

		_loadValues: function(depends) {
			// delegate the call to _loadValues to all widgets
			this._lastDepends = depends;
			array.forEach(this._widgets, function(iwidgets) {
				array.forEach(iwidgets, function(jwidget) {
					if (jwidget && '_loadValues' in jwidget) {
						jwidget._loadValues(depends);
					}
				});
			});
		},

		_setAllValues: function(_valList) {
			this._blockChangeEvents = true;
			var valList = lang.clone(_valList);
			if (!(valList instanceof Array)) {
				valList = [];
			}

			// adjust the number of rows
			var diff = valList.length - this._nRenderedElements;
			if (diff > 0) {
				this._appendRows(diff);
			}
			else if (diff < 0) {
				this._popElements(-diff);
			}

			this._allWidgetsBuiltDeferred.then(lang.hitch(this, function() {
				// set all values
				array.forEach(valList, function(ival, irow) {
					if (irow >= this._widgets.length) {
						return;
					}

					var rowVals = [];
					if (typeof ival == "string") {
						// entry is string .. we need to parse it if we have a delimiter
						if (this.delimiter) {
							rowVals = ival.split(this.delimiter);
						}
						else {
							rowVals = [ ival ];
						}
					}
					else if (ival instanceof Array) {
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
				this._set('value', this.get('value'));
				this._blockChangeEvents = false;
			}));
		},

		_setValueAttr: function(_vals) {
			// remove all empty elements
			var vals = array.filter(_vals, function(ival) {
				return (typeof ival == "string" && '' !== ival) || (ival instanceof Array && ival.length);
			});

			if (!this.disabled || !vals.length) {
				// append an empty element
				vals.push([]);
			}

			// set the values
			this._setAllValues(vals);
		},

		_setLabelAttr: function(_label) {
			// make sure label is treated as an array
			var label = _label;
			if (!(label instanceof Array)) {
				label = [];
				array.forEach(this.subtypes, function(itype, i) {
					label.push(i === 0 && _label ? _label : '&nbsp;');
				}, this);
			}

			this._allWidgetsBuiltDeferred.then(lang.hitch(this, function() {
				// prepare an array with labels for all widgets
				var allLabels = [];
				var i, j;
				for (i = 0; i < this._widgets.length; ++i) {
					allLabels.push(label);
				}

				// set all labels at once
				this._setAllLabels(allLabels);

				// notify observers
				this._set('label', _label);
			}));
		},

		_setDescriptionAttr: function(_description) {
			var description = _description;
			if (!(description instanceof Array)) {
				description = [];
				array.forEach(this.subtypes, function(itype, i) {
					description.push(i === 0 ? itype.description || _description || '' : itype.description || '');
				}, this);
			}

			this._allWidgetsBuiltDeferred.then(lang.hitch(this, function() {
				// prepare an array with descriptions for all widgets
				var allDescriptions = [];
				var i, j;
				for (i = 0; i < this._widgets.length; ++i) {
					allDescriptions.push(description);
				}

				// set all descriptions at once
				this._setAllDescriptions(allDescriptions);

				// notify observers
				this._set('description', _description);
			}));
		},


		_setAllLabels: function(labels) {
			this._allWidgetsBuiltDeferred.then(lang.hitch(this, function() {
				var i, j, jwidget, label;
				for (i = 0; i < this._widgets.length; ++i) {
					for (j = 0; j < this._widgets[i].length; ++j) {
						jwidget = this._widgets[i][j];
						if (jwidget) {
							label = i < labels.length && j < labels[i].length ? labels[i][j] : '';
							jwidget.set('label', label);
						}
					}
				}
			}));
		},

		_setAllDescriptions: function(descriptions) {
			this._allWidgetsBuiltDeferred.then(lang.hitch(this, function() {
				var i, j, jwidget, label;
				for (i = 0; i < this._widgets.length; ++i) {
					for (j = 0; j < this._widgets[i].length; ++j) {
						jwidget = this._widgets[i][j];
						if (jwidget) {
							description = i < descriptions.length && j < descriptions[i].length ? descriptions[i][j] : '';
							if (! ((description === '') || (description === ' ') || (typeof description == 'undefined')) ) {
								jwidget.set('description', description);
							} else {
								jwidget.set('description', null);
							}
						}
					}
				}
			}));
		},

		_setDisabledAttr: function ( value ) {
			domClass.toggle(this.domNode, 'umcMultiInputDisabled', value);
			this._allWidgetsBuiltDeferred.then(lang.hitch(this, function() {
				var i;
				for (i = 0; i < this._rowContainers.length; ++i) {
					var irow = this._rowContainers[i];
					array.forEach(irow ? irow.getChildren() : [], function(widget) {
						widget.set('disabled', value);
					});
				}
			}));
			this._set('disabled', value);
		},

		_getAllValues: function() {
			var i, j, jwidget, val, isSet, vals = [], rowVals = [];
			for (i = 0; i < this._widgets.length; ++i) {
				rowVals = [];
				isSet = false;
				for (j = 0; j < this._widgets[i].length; ++j) {
					jwidget = this._widgets[i][j];
					if (!jwidget) {
						continue;
					}
					val = jwidget.get('value');
					isSet = isSet || ('' !== val);
					if (!this._widgets[i][j].isInstanceOf(Button)) {
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
			array.forEach(this._getAllValues(), lang.hitch(this, function(ival) {
				if (typeof ival == "string" && this._hasContent(ival)) {
					vals.push(ival);
				} else if (Array.isArray(ival) && this._hasContent(ival)) {
					// if we only have one subtype, do not use arrays as representation
					vals.push(1 == ival.length ? ival[0] : ival);
				}
			}));
			return vals;
		},

		_hasContent: function(val) {
			var hasContent = false;
			if (Array.isArray(val)) {
				array.forEach(val, lang.hitch(this, function(ival) {
					hasContent = hasContent || this._hasContent(ival);
				}));
			} else {
				hasContent = hasContent || val !== '';
			}
			return hasContent;
		},

		_updateNewEntryButton: function() {
			var isActive = this._nRenderedElements < this.max && !this.disabled;
			this._newEntryButton.set('visible', isActive);
			this._newEntryButton.set('disabled', !isActive);
		},

		_renderNewEntryButton: function() {
			this._newEntryButton = new Button({
				label: this.newEntryButtonLabel,
				iconClass: this.newEntryButtonIconClass,
				disabled: this.disabled,
				visible: !this.disabled,
				onClick: lang.hitch(this, '_appendRows', 1),
				'class': 'umcMultiInputAddButton umcOutlinedButton'
			});
			this.addChild(this._newEntryButton);

			// hide the button when the MultiInput widget is being deactivated
			this.watch('disabled', lang.hitch(this, '_updateNewEntryButton'));
		},

		_updateReadyDeferred: function() {
			// check all current elements whether they are ready
			var nReady = 0;
			var nNoReadyElements = 0; // num of elements that do not have a ready method
			var nElements = 0;
			var nBuiltElements = 0;
			var i, j;
			for (i = 0; i < this._widgets.length; ++i) {
				for (j = 0; j < this._widgets[i].length; ++j, ++nElements) {
					var jwidget = this._widgets[i][j];
					nBuiltElements += jwidget ? 1 : 0;
					var jreadyDeferred = jwidget && jwidget.ready ? jwidget.ready() : null;
					if (!jreadyDeferred) {
						++nNoReadyElements;
					}
					else if (jreadyDeferred.isFulfilled()) {
						++nReady;
					}
					else if (!this._pendingDeferreds[jwidget.name]) {
						// deferred has not yet been resolved -> re-trigger _updateReadyDeferred() upon resolution
						// via _pendingDeferreds we are sure that we do not register at the widget's Deferred
						// object multiple times
						(lang.hitch(this, function(widgetName) {
							// encapsulate in closure, otherwise we cannot access jwidget.name within
							// the deferred callback anymore (it changes with the for loop)
							this._pendingDeferreds[widgetName] = true;
							jreadyDeferred.then(lang.hitch(this, function() {
								this._pendingDeferreds[widgetName] = false;
								this._updateReadyDeferred();
							}));
						}))(jwidget.name);
					}
				}
			}


			// initiate new Deferred objects if none is pending
			var overallProcess = (nReady + nBuiltElements) / (2 * nElements - nNoReadyElements);
			if (overallProcess < 1 && this._readyDeferred.isFulfilled()) {
				this._readyDeferred = new Deferred();
			}
			if (nBuiltElements < nElements && this._allWidgetsBuiltDeferred.isFulfilled()) {
				this._allWidgetsBuiltDeferred = new Deferred();
			}

			// update the deferred's progress
			if (!this._readyDeferred.isFulfilled()) {
				this._readyDeferred.progress({
					percentage: 100 * overallProcess
				});
			}

			if (nBuiltElements == nElements && !this._allWidgetsBuiltDeferred.isFulfilled()) {
				// all elements have been built
				this._allWidgetsBuiltDeferred.resolve();
			}

			if (overallProcess >= 1 && this._allWidgetsBuiltDeferred.isFulfilled() && !this._readyDeferred.isFulfilled()) {
				// all elements are ready
				this._readyDeferred.resolve();
				this.onValuesLoaded();
			}
		},

		__appendRow: function(irow) {
			var order = [], widgetConfs = [];

			// if the subwidgets have no label on their own,
			//   remove the LabelPane wrapper to horizontally align with other
			//   non-MultiInput widgets. See Bug #25389
			array.forEach(this.subtypes, function(iwidget, i) {
				// add the widget configuration dict to the list of widgets
				var iname = '__' + this.name + '-' + irow + '-' + i;
				var iconf = lang.mixin(lang.clone(iwidget), {
					disabled: this.disabled,
					threshold: this.threshold, // for UDM-threshold
					name: iname,
					value: '',
					dynamicValues: lang.partial(iwidget.dynamicValues, iname)
				});

				// if no label and description is given, set the main label/description as label/description
				// of the first subwidget
				iconf.label = iconf.label || (i === 0 && this.label ? this.label : '&nbsp;');
				iconf.description = iconf.description || (i === 0 && this.description ? this.description : '');

				if (iwidget.dynamicValuesInfo) {
					iconf.dynamicValuesInfo = lang.partial(iwidget.dynamicValuesInfo, iname);
				}
				widgetConfs.push(iconf);

				// add the name of the widget to the list of widget names
				order.push(iname);
			}, this);

			// render the widgets
			var widgets = render.widgets(widgetConfs);

			// if we have a button, we need to pass the value and index of the
			// current element
			tools.forIn(widgets, function(ikey, iwidget) {
				var myrow = irow;
				if (iwidget.isInstanceOf(Button) && typeof iwidget.callback == "function") {
					var callbackOrg = iwidget.callback;
					iwidget.callback = lang.hitch(this, function() {
						callbackOrg(this.get('value')[myrow], myrow);
					});
				}
			}, this);

			// layout widgets
			var visibleWidgets = array.map(order, function(iname) {
				return widgets[iname];
			});
			var rowContainer = new ContainerWidget({
				baseClass: 'umcMultiInputContainer',
				visibleWidgets: visibleWidgets,
				irow: irow
			});
			array.forEach(order, function(iname, idx) {
				// add widget to row container (wrapped by a LabelPane)
				// only keep the label for the first row
				var iwidget = widgets[iname];
				rowContainer.addChild(new LabelPane({
					disabled: this.disabled,
					content: iwidget,
					usesHoverTooltip: iwidget.usesHoverTooltip || false,
					// mark last element in a row
					'class': idx == order.length - 1 ? 'umcMultiInputLastRowEntry' : null
				}));

				// register to value changes
				this.own(iwidget.watch('value', lang.hitch(this, function() {
					if (!this._blockChangeEvents) {
						this._set('value', this.get('value'));
					}
				})));
			}, this);

			// add a 'remove' button
			var button = new Button({
				disabled: this.disabled,
				visible: !this.disabled,
				iconClass: 'umcTrashIcon',
				showLabel: false,
				onClick: lang.hitch(this, function() {
					this._removeElement(rowContainer.irow);
				}),
				'class': 'umcMultiInputRemoveButton umcOutlinedButton',
				description: _('Remove entry')
			});
			rowContainer.addChild(button);

			// hide the button when the MultiInput widget is being deactivated
			button.own(this.watch('disabled', function(attr, oldVal, disabled) {
				button.set('visible', !disabled);
				button.set('disabled', disabled);
			}));

			// add row
			this._widgets[irow] = visibleWidgets;
			this._rowContainers[irow] = rowContainer;
			this._startupDeferred.then(lang.hitch(rowContainer, 'startup'));
			this.addChild(rowContainer, irow);

			// call the _loadValues method by hand
			array.forEach(order, function(iname) {
				var iwidget = widgets[iname];
				if ('_loadValues' in iwidget) {
					iwidget._loadValues(this._lastDepends);
				}
			}, this);

			// update the ready deferred know and when the widget itself is ready
			this._updateReadyDeferred();
			var allReady = [];
			tools.forIn(widgets, function(ikey, iwidget) {
				allReady.push(iwidget.ready ? iwidget.ready() : null);
			});
			all(allReady).then(lang.hitch(this, '_updateReadyDeferred'));
		},

		_appendRows: function(n) {
			n = n || 1;
			if (n < 1) {
				return;
			}

			var nFinal = this._nRenderedElements + n;
			var newRows = [];
			for (var irow = this._nRenderedElements; irow < nFinal && irow < this.max; ++irow, ++this._nRenderedElements) {
				newRows.push(irow);

				// allocate indices in 2D array _widget this allows _updateReadyDeferred()
				// to know how many entries there will be at the end
				this._rowContainers[irow] = null;
				this._widgets[irow] = [];
				for (var jsubWidget = 0; jsubWidget < this.subtypes.length; ++jsubWidget) {
					this._widgets[irow][jsubWidget] = null;
				}
			}

			// force the ready deferred to be updated
			this._updateReadyDeferred();

			// perform adding rows asynchronously
			tools.forEachAsync(newRows, this.__appendRow, this, 5, 50).then(lang.hitch(this, function() {
				// all elements have been added to the DOM
				// add the new button
				this._updateNewEntryButton();
				this._updateReadyDeferred();
			}));
		},

		_popElements: function(n) {
			if (n < 1) {
				return;
			}

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
			this._updateNewEntryButton();
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

		focus: function(/* TODO make specific widget in specific row focusable via parameter ? */) {
			this._widgets.some(function(widgetRow) {
				return widgetRow.some(function(widget) {
					if (!widget.get('disabled')) {
						widget.focus();
						return true;
					}
				});
			});
		},

		focusInvalid: function() {
			this._widgets.some(function(widgetRow) {
				return widgetRow.some(function(widget) {
					if (!widget.get('disabled') && !widget.isValid()) {
						widget.focusInvalid();
						return true;
					}
				});
			});
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
				var imessage = messages instanceof Array ? messages[i] : messages;
				var iisValid = areValid instanceof Array ? areValid[i] : areValid;
				for (j = 0; j < this._widgets[i].length; ++j) {
					this._widgets[i][j].setValid(iisValid, imessage);
				}
			}
		},

		_setBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			if (this._widget) {
				tools.delegateCall(this, arguments, this._widget);
			}
		},

		_getBlockOnChangeAttr: function(/*Boolean*/ value) {
			// execute the inherited functionality in the widget's scope
			if (this._widget) {
				tools.delegateCall(this, arguments, this._widget);
			}
		},

		onValuesLoaded: function(values) {
			// summary:
			//		This event is triggered when all values (static and dynamic) have been loaded.
			// values:
			//		Array containing all dynamic and static values.
		},

		// ready:
		//		Similar to `umc/widgets/_FormWidgetMixin:ready`.
		ready: function() {
			return this._readyDeferred;
		}
	});
});

