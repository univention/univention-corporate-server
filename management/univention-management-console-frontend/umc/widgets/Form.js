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
		dijit.form.Form
/*		dojox.form.manager._Mixin,
		dojox.form.manager._ValueMixin,
		dojox.form.manager._EnableMixin,
		dojox.form.manager._DisplayMixin,
		dojox.form.manager._ClassMixin*/
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

	// scrollable: Boolean
	//		If set to true, the container will set its width/height to 100% in order
	//		to enable scrollbars.
	scrollable: false,

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

		// in case no submit button has been defined, we define one and hide it
		// this allows us to connect to the onSubmit event in any case
		var submitButtonDefined = false;
		dojo.forEach(this.buttons, function(ibutton) {
			if ('submit' == ibutton.name) {
				submitButtonDefined = true;
				return false; // break loop
			}
		});
		if (!submitButtonDefined) {
			// no submit button defined, add a hidden one :)
			this.buttons = dojo.isArray(this.buttons) ? this.buttons : [];
			this.buttons.push({
				label: 'submit',
				name: 'submit',
				style: 'height: 0; overflow: hidden; margin: 0; padding: 0;' // using display=none will prevent button from being called
			});
		}

		// initiate _dependencyMap
		this._dependencyMap = {};
	},

	getButton: function( /*String*/ button_name) {
		// summary:
		//			  Return a reference to the button with the specified name.
		return this._buttons[button_name]; // Widget|undefined
	},

	getWidget: function( /*String*/ widget_name) {
		// summary:
		//		Return a reference to the widget with the specified name.
		return this._widgets[widget_name]; // Widget|undefined
	},

	showWidget: function( widget_name, /* bool? */ visibility ) {
		if ( ! widget_name in this._widgets ) {
			//console.log( 'Form.showWidget: could not find widget ' + widget_name );
			return;
		}
		this._widgets[ widget_name ].set( 'visible', visibility );
	},

	buildRendering: function() {
		this.inherited(arguments);

		if (this.scrollable) {
			dojo.style(this.containerNode, {
				overflow: 'auto'
			});
		}

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
			if ('onValuesLoaded' in iwidget && !(iwidget._valuesLoaded && !iwidget._deferredOrValues)) {
				// widget values have not been loaded completely so far
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
			var depends = umc.tools.stringOrArray(iwidget.depends);
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
			var orgCallback = dojo.getObject(ibutton + '.callback', false, this._buttons);
			if (orgCallback) {
				this._buttons[ibutton].callback = function() { };
			}
			this.connect(this, ievent, function(e) {
				// prevent standard form submission
				if (e && e.preventDefault) {
					e.preventDefault();
				}

				// if there is a custom callback, call it with all form values
				if (dojo.isFunction(orgCallback)) {
					orgCallback(this.gatherFormValues());
				}
			});
		}, this);
	},

	// regexp for matching 1D and 2D array-like names
	gatherFormValues: function() {
		// gather values from all registered widgets
		var vals = {};
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			// ignore elements that start with '__'
			if ('__' != iname.substr(0, 2)) {
				var val = iwidget.get('value');
				if (val !== undefined) {
					// ignore undefined values
					vals[iname] = val;
				}
			}
		}, this);

		// add item ID to the dictionary in case it is not already included
		var idProperty = dojo.getObject('moduleStore.idProperty', false, this);
		if (idProperty && !(idProperty in vals) && null !== this._loadedID) {
			vals[idProperty] = this._loadedID;
		}

		return vals;
	},

	clearFormValues: function() {
		// clear all values based on or list of widgets
		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			// value could be a string, an array, or a dict... query first the value
			// and reset the value accordingly
			var val = iwidget.get('value');
			if (dojo.isString(val)) {
				iwidget.set('value', '');
			}
			else if (dojo.isArray(val)) {
				iwidget.set('value', []);
			}
			else if (dojo.isObject(val)) {
				iwidget.set('value', {});
			}
			else if (typeof val == 'number') {
				iwidget.set('value', 0);
			}
		}, this);
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
		}, this);
	},

	elementValue: function(element, newVal) {
		// summary:
		//		Get or set the value for the specified form element.
		var widget = this.getWidget(element);
		if (!widget) {
			return undefined;
		}

		if (undefined === newVal) {
			// no value defined, return the current value
			return widget.get('value');
		}

		// otherwise set the value
		widget.set('value', newVal);
		return widget;
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

			return data;
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

	validate: function() {
		return this.getInvalidWidgets().length === 0;
	},

	getInvalidWidgets: function() {
		var widgets = [];

		umc.tools.forIn(this._widgets, function(iname, iwidget) {
			if ( iwidget.validate !== undefined ) {
				if ( iwidget._maskValidSubsetError !== undefined ) {
					iwidget._maskValidSubsetError = false;
				}
				if ( ! iwidget.validate() ) {
					widgets.push( iname );
				}
			}
		} );

		return widgets;
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







