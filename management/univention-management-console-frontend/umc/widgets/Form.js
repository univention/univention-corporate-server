/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Form");

dojo.require("dijit.form.Form");
dojo.require("dojox.form.manager._Mixin");
dojo.require("dojox.form.manager._ValueMixin");
dojo.require("dojox.form.manager._EnableMixin");
dojo.require("dojox.form.manager._DisplayMixin");
dojo.require("dojox.form.manager._ClassMixin");
dojo.require("umc.tools");

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

	_widgets: null,

	_buttons: null,

	_container: null,

	_dependencyMap: null,

	'class': 'umcNoBorder',

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

	buildRendering: function() {
		this.inherited(arguments);

		// render the widgets and the layout if no content is given
		if (!this.content) {
			this._widgets = umc.tools.renderWidgets(this.widgets);
			this._buttons = umc.tools.renderButtons(this.buttons || []);
			this._container = umc.tools.renderLayout(this.layout, this._widgets, this._buttons);

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

		// register for dynamically changing Widgets
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			if (iwidget.onWidgetAdd) {
				this.connect(iwidget, 'onWidgetAdd', function(widget) {
					this.registerWidget(widget);
				});
				this.connect(iwidget, 'onWidgetRemove', function(widget) {
					this.unregisterWidget(widget.name);
				});
			}
		}, this);
	},

	// regexp for matching 1D and 2D array-like names
	_arrayRegExp: /^([^\[\]]+)\[([^\[\]]+)\](\[([^\[\]]+)\])?$/,
	gatherFormValues: function() {
		var vals = this.inherited(arguments);

		// now we might have elements with names such as 'myname[2]' or 'myname[dd]',
		// these indicate array/dict elements .. parse these elements into a real 
		// arrays/dicts
		var parsedVals = {};
		umc.tools.forIn(vals, function(ikey, ival) {
			// ignore elements that start with '__'
			if ('__' == ikey.substr(0, 2)) {
				return true;
			}

			// check whether we have an array expression
			var m = this._arrayRegExp.exec(ikey);
			if (!m) {
				// normal value
				parsedVals[ikey] = ival;
			}
			else {
				// get the key and parse the indeces
				var key = m[1];
				var idx = [ key, m[2] ]; // list of 'string' indeces
				if (undefined !== m[4]) {
					idx.push(m[4]);
				}
				var nidx = dojo.map(idx, function(i) { // list of integer indeces
					return parseInt(i, 10);
				});

				// get the object that is referenced
				var path = parsedVals;
				var lastIdx = null;
				for (var i = 0; i < idx.length - 1; ++i) {
					// check the next level
					var subPath = path[ nidx[i] || idx[i] ];

					if (!subPath) {
						// object does not exist, create dict or array depending on whehter 
						// we got a number or string as index
						subPath = path[ nidx[i] || idx[i] ] = isNaN(nidx[i + 1]) ? {} : [];
					}
					path = subPath;
					lastIdx = nidx[i + 1] || idx[i + 1];
				}
				path[ nidx[idx.length - 1] || idx[idx.length - 1] ] = ival;
			}
		}, this);

		// for arrays, remove last elements that are empty
		var objList = [ parsedVals ]; // LIFO of elements to examine
		while (objList.length) {
			// take next element in list
			var iobj = objList.pop();

			if (dojo.isArray(iobj)) {
				// element is an array, remove last elements that are empty
				while (iobj.length && !iobj[vals.length - 1]) {
					iobj.pop();
				}
			}
			else if (dojo.isObject(iobj)) {
				// element is an object, it may contain arrays .. add all objects to the list
				var newObjs = [];
				umc.tools.forIn(iobj, function(jkey, jobj) {
					newObjs.push(jobj);
				});
				objList = objList.concat(newObjs);
			}
		}

		return parsedVals;
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
		this.moduleStore.get(itemID).then(dojo.hitch(this, function(data) {
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

			// fire event
			this.onLoaded(true);
		}), dojo.hitch(this, function(error) {
			// fire event also in error case
			this.onLoaded(false);
		}));
	},

	save: function() {
		// summary:
		//		Gather all form values and send them to the server via UMCP.
		//		For this, the field umcpSetCommand needs to be set.

		umc.tools.assert(this.moduleStore, 'In order to save form data to the server, the umc.widgets.Form.moduleStore needs to be set');

		// sending the data to the server
		var values = this.gatherFormValues();
		this.moduleStore.put(values).then(dojo.hitch(this, function() {
			// fire event
			this.onSaved(true);
		}), dojo.hitch(this, function() {
			// fire event also in error case
			this.onSaved(false);
		}));
	},

	onSaved: function(/*Boolean*/ success) {
		// event stub
	},

	onLoaded: function(/*Boolean*/ success) {
		// event stub
	}
});







