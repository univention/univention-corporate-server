/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Form");

dojo.require("dijit.form.Form");
dojo.require("dojox.form.manager._Mixin");
dojo.require("dojox.form.manager._ValueMixin");
dojo.require("dojox.form.manager._EnableMixin");
dojo.require("dojox.form.manager._DisplayMixin");
dojo.require("dojox.form.manager._ClassMixin");
dojo.require("umc.tools");
dojo.require("umc.render");

dojo.declare("umc.widgets.Form", [
		dijit.form.Form,
		dojox.form.manager._Mixin,
		dojox.form.manager._ValueMixin,
		dojox.form.manager._EnableMixin,
		dojox.form.manager._DisplayMixin,
		dojox.form.manager._ClassMixin
], {
	// summary:
	//		Encapsulates a complete form, offers unified access to elements as
	//		well as some convenience methods.
	// description:
	//		This class has some extra assumptions for gatherFormValues().
	//		Elements that start with '__' will be ignored. Elements that have
	//		a name such as 'myname[1]' or 'myname[2]' will be converted into
	//		arrays or dicts, respectively. Two-dimensional arrays/dicts are
	//		also possible.

	// widgets: Object[]|dijit.form._FormWidget[]|Object
	//		Array of config objects that specify the widgets that are going to
	//		be used in the form. Can also be a list of dijit.form._FormWidget
	//		instances or a dictionary with name->Widget entries in which case
	//		no layout is rendered and `content` is expected to be specified.
	widgets: null,

	// buttons: Object[]?
	//		Array of config objects that specify the buttons that are going to
	//		be used in the form. Buttons with the name 'submit' and 'reset' have
	//		standard handlers unless
	buttons: null,

	// layout: String[][]?
	//		Array of strings that specifies the position of each element in the
	//		layout. If not specified, the order of the widgets is used directly.
	//		You may specify a widget entry as `undefined` or `null` in order
	//		to leave a place free.
	layout: null,

	// content: dijit._Widget?
	//		Widget that contains all form elements already layed out.
	//		If given, `widgets` is expected to be a list of already initiated
	//		dijit.form._FormWidget instances that occur in the manually layed out
	//		content.
	content: null,

	// moduleStore: umc.store.UmcpModuleStore
	//		Object store for module requests using UMCP commands. If given, form data
	//		can be loaded/saved by the form itself.
	moduleStore: null,

	// the widget's class name as CSS class
	'class': 'umcForm',

	_widgets: null,

	_buttons: null,

	_container: null,

	_dependencyMap: null,

	_loadedID: null,

	'class': 'umcNoBorder',

	_initializingElements: 0,

	postMixInProperties: function() {
		this.inherited(arguments);

		// in case no layout is specified and no content, either, create one automatically
		if ((!this.layout || !this.layout.length) && !this.content) {
			this.layout = [];
			dojo.forEach(this.widgets, function(iwidget) {
				// add the name (or undefined) to the row
				this.layout.push(dojo.getObject('name', false, iwidget));
			}, this);
		}

		// initiate _dependencyMap
		this._dependencyMap = {};
	},

	getWidget: function( /*String*/ widget_name) {
		// summary:
		//		Return a reference to the widget with the specified name.
		return this._widgets[widget_name]; // Widget|undefined
	},

	showWidget: function( widget_name, /* bool? */ visibility ) {
		if ( ! widget_name in this._widgets ) {
			console.log( 'Form.showWidget: could not find widget ' + widget_name );
			return;
		}
		this._widgets[ widget_name ].set( 'visible', visibility );
	},

	buildRendering: function() {
		this.inherited(arguments);

		// render the widgets and the layout if no content is given
		if (!this.content) {
			this._widgets = umc.render.widgets(this.widgets);
			this._buttons = umc.render.buttons(this.buttons || []);
			this._container = umc.render.layout(this.layout, this._widgets, this._buttons);

			// start processing the layout information
			this._container.placeAt(this.containerNode);
			this._container.startup();
		}
		// otherwise, register content and create an internal dictionary of widgets
		else {
			var errMsg = "umc.widgets.Form: As 'content' is specified, the property 'widgets' is expected to be an array of widgets.";

			// register content
			umc.tools.assert(this.content.domNode && this.content.declaredClass, errMsg);
			this.content.placeAt(this.containerNode);

			// create internal dictionary of widgets
			if (dojo.isArray(this.widgets)) {
				dojo.forEach(this.widgets, function(iwidget) {
					// make sure the object looks like a widget
					umc.tools.assert(iwidget.domNode && iwidget.declaredClass, errMsg);
					umc.tools.assert(iwidget.name, "umc.widgets.Form: Each widget needs to specify the property 'name'.");

					// add entry to dictionary
					this._widgets[iwidget.name] = iwidget;
				}, this);
			}
			// `widgets` is already a dictionary
			else if (dojo.isObject(this.widgets)) {
				this._widgets = this.widgets;
			}
		}

		// send an event when all dynamic elements have been initialized
		this._initializingElements = 0;
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			// only consider elements that load values dynamically
			if ('onValuesLoaded' in iwidget && !iwidget._valuesLoaded) {
				//console.log('iwidget:', iwidget.name);
				++this._initializingElements;
				var handle = this.connect(iwidget, 'onValuesLoaded', dojo.hitch(this, function() {
					//console.log('onValuesLoaded:', iwidget.name, iwidget.get('value'));
					// disconnect from the signal
					this.disconnect(handle);

					// decrement the internal counter
					--this._initializingElements;

					// send event when the last element has been initialized
					if (0 === this._initializingElements) {
						this.onValuesInitialized();
					}
				}));
			}
		}, this);

		// maybe all elements are already initialized
		if (!this._initializingElements) {
			this.onValuesInitialized();
		}
	},

	postCreate: function() {
		this.inherited(arguments);

		// prepare registration of onChange events
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			// check whether the widget has a `depends` field
			if (!iwidget.depends) {
				return;
			}

			// loop over all dependencies and cache the dependencies as a map from
			// publishers -> receivers
			var depends = dojo.isArray(iwidget.depends) ? iwidget.depends : [ iwidget.depends ];
			dojo.forEach(depends, dojo.hitch(this, function(idep) {
				this._dependencyMap[idep] = this._dependencyMap[idep] || [];
				this._dependencyMap[idep].push(iwidget);
			}));
		}, this);

		// register all necessary onChange events to handle dependencies
		umc.tools.forIn(this._dependencyMap, function(iname) {
			if (iname in this._widgets) {
				this.connect(this._widgets[iname], 'onChange', function() {
					this._updateDependencies(iname);
				});
			}
		}, this);

		// register callbacks for onSubmit and onReset events
		umc.tools.forIn({ 'submit': 'onSubmit', 'reset': 'onReset' }, function(ibutton, ievent) {
			var customCallback = dojo.getObject(ibutton + '.callback', false, this._buttons);
			if (customCallback) {
				this.connect(this, ievent, function(e) {
					// prevent standard form submission
					e.preventDefault();

					// if there is a custom callback, call it with all form values
					customCallback(this.gatherFormValues());
				});
			}
		}, this);
	},

	// regexp for matching 1D and 2D array-like names
	gatherFormValues: function() {
		// gather values from all registered widgets
		var vals = {};
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			// ignore elements that start with '__'
			if ('__' != iname.substr(0, 2)) {
				vals[iname] = iwidget.get('value');
			}
		}, this);

		// add item ID to the dictionary in case it is not already included
		var idProperty = dojo.getObject('moduleStore.idProperty', false, this);
		if (idProperty && !(idProperty in vals) && null !== this._loadedID) {
			vals[idProperty] = this._loadedID;
		}

		return vals;
	},

	setFormValues: function(values) {
		// set all values based on or list of widgets
		umc.tools.forIn(values, function(iname, ival) {
			if (this._widgets[iname]) {
				this._widgets[iname].set('value', ival);
				if (this._widgets[iname].setInitialValue) {
					this._widgets[iname].setInitialValue(ival, false);
				}
			}
			else {
				console.log(dojo.replace("WARNING: Could not set the property '{0}': {1}", [iname, ival]));
			}
		}, this);
	},

	_updateDependencies: function(publisherName) {
		var tmp = [];
		dojo.forEach(this._dependencyMap[publisherName], function(i) {
			tmp.push(i.name);
		});
		//console.log(dojo.replace('# _updateDependencies: publisherName={0} _dependencyMap[{0}]={1}', [publisherName, dojo.toJson(tmp)]));
		if (publisherName in this._dependencyMap) {
			var values = this.gatherFormValues();
			dojo.forEach(this._dependencyMap[publisherName], function(ireceiver) {
				if (ireceiver && ireceiver._loadValues) {
					ireceiver._loadValues(values);
				}
			});
		}
	},

	load: function(/*String*/ itemID) {
		// summary:
		//		Send off an UMCP query to the server for querying the data for the form.
		//		For this the field umcpGetCommand needs to be set.
		// itemID: String
		//		ID of the object that should be loaded.

		umc.tools.assert(this.moduleStore, 'In order to load form data from the server, the umc.widgets.Form.moduleStore needs to be set.');
		umc.tools.assert(itemID, 'The specifid itemID for umc.widgets.Form.load() must valid.');

		// query data from server
		var deferred = this.moduleStore.get(itemID).then(dojo.hitch(this, function(data) {
			var values = this.gatherFormValues();
			var newValues = {};

			// copy all the fields that exist in the form
			umc.tools.forIn(data, function(ikey, ival) {
				if (ikey in values) {
					newValues[ikey] = ival;
				}
			}, this);

			// set all values at once
			this.setFormValues(newValues);
			this._loadedID = itemID;

			// fire event
			this.onLoaded(true);

			return newValues;
		}), dojo.hitch(this, function(error) {
			// fire event also in error case
			this.onLoaded(false);
		}));

		return deferred;
	},

	save: function() {
		// summary:
		//		Gather all form values and send them to the server via UMCP.
		//		For this, the field umcpSetCommand needs to be set.

		umc.tools.assert(this.moduleStore, 'In order to save form data to the server, the umc.widgets.Form.moduleStore needs to be set');

		// sending the data to the server
		var values = this.gatherFormValues();
		var deferred = this.moduleStore.put(values).then(dojo.hitch(this, function() {
			// fire event
			this.onSaved(true);
		}), dojo.hitch(this, function() {
			// fire event also in error case
			this.onSaved(false);
		}));

		return deferred;
	},

	onSaved: function(/*Boolean*/ success) {
		// event stub
	},

	onLoaded: function(/*Boolean*/ success) {
		// event stub
	},

	onValuesInitialized: function() {
		// event stub
	}
});







