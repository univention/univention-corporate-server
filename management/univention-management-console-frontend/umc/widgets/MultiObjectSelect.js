/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.MultiObjectSelect");

dojo.require("umc.widgets.Button");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.MultiSelect");
dojo.require("umc.widgets.SearchForm");
dojo.require("umc.tools");
dojo.require("umc.render");
dojo.require("umc.widgets._FormWidgetMixin");
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.widgets.MultiObjectSelect", [ umc.widgets.ContainerWidget, umc.i18n.Mixin, umc.widgets._FormWidgetMixin ], {
	// summary:
	//		???

	queryWidgets: [],

	queryCommand: '',

	queryOptions: {},

	// 'javascript:functionName'
	// function(ids) { ... }
	// may return dojo.Deferred
	formatter: function(ids) { return ids; },

	autoSearch: true,

	name: '',

	value: null,

	i18nClass: 'umc.app',

	// the widget's class name as CSS class
	'class': 'umcMultiObjectSelect',

	// internal reference to all values
	_values: [],

	// internal reference to the parsed formatter function
	_formatter: function(ids) { return ids; },

	// reference to the MultiSelect widget
	_multiSelect: null,

	// reference to the detail dialog
	_detailDialog: null,

	postMixInProperties: function() {
		this.inherited(arguments);

		// in case 'value' is not specified, generate a new array
		if (!dojo.isArray(this.value)) {
			this.value = [];
		}

		// if 'formatter' is a string, parse it
		if (dojo.isString(this.formatter)) {
			// string may start with 'javascript:'
			if (0 === this.formatter.indexOf('javascript:')) {
				// evaluate string as javascript code
				var str = this.formatter.substr(11);
				this._formatter = eval(str);
			}
			else {
				console.log('ERROR: The attribute umc.widgets.MultiObjectSelect.formatter could not been evaluated. Ignoring error: ' + this.formatter);
			}
		}
		else if (dojo.isFunction(this.formatter)) {
			this._formatter = this.formatter;
		}
	},

	buildRendering: function() {
		this.inherited(arguments);

		// add the MultiSelect widget
		this._multiSelect = new umc.widgets.MultiSelect({});
		var container = new umc.widgets.ContainerWidget({});
		container.addChild(this._multiSelect);
		this.addChild(container);

		// add the Buttons
		container = new umc.widgets.ContainerWidget({});
		container.addChild(new umc.widgets.Button({
			label: this._('Add'),
			//iconClass: 'dijitIconNewTask',
			onClick: dojo.hitch(this, function() {
				if (!this._detailDialog) {
					// dialog does not exist, create a new one
					this._detailDialog = new umc.widgets._MultiObjectSelectDetailDialog({
						widgets: this.queryWidgets,
						queryCommand: this.queryCommand,
						queryOptions: this.queryOptions || {},
						autoSearch: this.autoSearch
					});

					// register the event handler
					this.connect(this._detailDialog, 'onAdd', '_addElements');
				}
				this._detailDialog.show();
			})
		}));
		container.addChild(new umc.widgets.Button({
			label: this._('Remove'),
			//iconClass: 'dijitIconDelete',
			onClick: dojo.hitch(this, '_removeSelectedElements')
		}));
		this.addChild(container);
	},

	_setValueAttr: function(_values) {
		// handle possible dojo.Deferred object returned by the formatter
		dojo.when(this._formatter(_values), dojo.hitch(this, function(values) {
			// sort the array according to the labels
			values.sort(umc.tools.cmpObjects('label'));

			// callback handler
			this._multiSelect.set('staticValues', values);
		}));

		// cache the specified values for any case
		this._values = _values;
	},

	_getValueAttr: function() {
		// return a copy
		return dojo.clone(this._values);
	},

	_addElements: function(values) {
		// get all current entries
		var newValues = this._values;
		var map = {};
		dojo.forEach(newValues, function(iid) {
			map[iid] = true;
		});

		// only add elements that do not exist already
		dojo.forEach(values, function(iid) {
			if (!(iid in map)) {
				newValues.push(iid);
			}
		});

		// save the new values
		this.set('value', newValues);
	},

	_removeSelectedElements: function() {
		// create a dict for all selected elements
		var selection = {};
		dojo.forEach(this._multiSelect.get('value'), function(iid) {
			selection[iid] = true;
		});

		// get all items
		var newValues = dojo.filter(this.get('value'), function(iid) {
			return !(iid in selection);
		});

		// set the new values
		this.set('value', newValues);
	},

	uninitialize: function() {
		if (this._detailDialog) {
			this._detailDialog.destroy();
		}
	}
});

dojo.declare("umc.widgets._MultiObjectSelectDetailDialog", [ dijit.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	widgets: [],

	queryCommand: '',

	queryOptions: {},

	autoSearch: true,

	i18nClass: 'umc.app',

	'class': 'umcMultiObjectSelectDetailDialog',

	_form: null,

	_multiSelect: null,

	_container: null,

	uninitialize: function() {
		// make sure that the container widget is destroyed correctly
		this._container.destroyRecursive();
	},

	postMixInProperties: function() {
		this.inherited(arguments);
		this.title = this._('Add new object');
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create a container for all widgets
		this._container = new umc.widgets.ContainerWidget({});
		this._container.placeAt(this.containerNode);

		// for the layout, all Elements should be below each other
		var layout = dojo.map(this.widgets, function(iwidget) {
			return iwidget.name;
		});
		this._form = new umc.widgets.SearchForm({
			widgets: this.widgets,
			layout: layout,
			onSearch: dojo.hitch(this, 'search'),
			onValuesInitialized: dojo.hitch(this, function() {
				// trigger the search if autoSearch is specified and as soon as all form
				// elements have been initialized
				if (this.autoSearch) {
					this.search(this._form.gatherFormValues());
				}
			})
		});
		this._container.addChild(this._form);

		// for visualizing the search results, use a MultiSelect
		this._multiSelect = new umc.widgets.MultiSelect({});
		this._container.addChild(this._multiSelect);

		// add the final buttons to close the dialog
		this._container.addChild(new umc.widgets.Button({
			label: this._('Add'),
			onClick: dojo.hitch(this, function() {
				// get all elements an trigger onAdd event
				var ids = this._multiSelect.get('value');
				if (ids.length) {
					// only trigger event if there are more then 0 entries
					this.onAdd(ids);
				}

				// hide the dialog
				this.hide();

				// unselect all elements
				this._multiSelect.set('value', []);
			})
		}));
		this._container.addChild(new umc.widgets.Button({
			label: this._('Close'),
			onClick: dojo.hitch(this, function() {
				// hide the dialog
				this.hide();

				// unselect all elements
				this._multiSelect.set('value', []);

			})
		}));
	},

	search: function(_values) {
		// set dynamicOptions which will trigger a reload
		var values = dojo.mixin({}, this.queryOptions, _values);
		this._multiSelect.set('dynamicOptions', values);

		if (!this._multiSelect.dynamicValues) {
			// the first time we need to set dynamicValues
			this._multiSelect.set('dynamicValues', this.queryCommand);
		}
	},

	onAdd: function(ids) {
		// event stub
	}
});


