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
/*global define,require,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/Deferred",
	"dojo/when",
	"dojo/promise/all",
	"dojo/dom-class",
	"dijit/form/Form",
	"umc/tools",
	"umc/render",
	"umc/i18n!"
], function(declare, lang, array, kernel, Deferred, when, all, domClass, Form, tools, render, _) {

	// in order to break circular dependencies (umc.dialog needs a Form and
	// Form needs umc/dialog), we define umc/dialog as an empty object and
	// require it explicitly
	var dialog = {
		notify: function() {}
	};
	require(['umc/dialog'], function(_dialog) {
		// register the real umc/dialog module in the local scope
		dialog = _dialog;
	});

	return declare("umc.widgets.Form", [ Form ], {
		// summary:
		//		Encapsulates a complete form, offers unified access to elements as
		//		well as some convenience methods.
		// description:
		//		This class has some extra assumptions for get('value').
		//		Elements that start with '__' will be ignored. Elements that have
		//		a name such as 'myname[1]' or 'myname[2]' will be converted into
		//		arrays or dicts, respectively. Two-dimensional arrays/dicts are
		//		also possible.

		// widgets: Object[]|dijit/form/_FormWidget[]|Object
		//		Array of config objects that specify the widgets that are going to
		//		be used in the form. Can also be a list of dijit/form/_FormWidget
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

		// content: dijit/_WidgetBase?
		//		Widget that contains all form elements already laid out.
		//		If given, `widgets` is expected to be a list of already initiated
		//		dijit/form/_FormWidget instances that occur in the manually laid out
		//		content.
		content: null,

		// moduleStore: store.UmcpModuleStore
		//		Object store for module requests using UMCP commands. If given, form data
		//		can be loaded/saved by the form itself.
		moduleStore: null,

		_widgets: null,

		_buttons: null,

		_container: null,

		_dependencyMap: null,

		_loadedID: null,

		//'class': 'umcNoBorder',

		_allReadyNamed: null,

		progressDeferred: null,

		// standby functionality. If given, dependency loading triggers standby animation
		standby: null,
		standbyDuring: null,

		addNotification: function(/*innerHTML*/ message, /*function (optional)*/ action, /*String*/ actionLabel) {
			dialog.contextNotify(message, action, actionLabel);
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// initialize with empty list and empty object
			this._allReadyNamed = {};
			this.progressDeferred = new Deferred();

			// in case no layout is specified and no content, either, create one automatically
			if ((!this.layout || !this.layout.length) && !this.content) {
				this.layout = [];
				array.forEach(this.widgets, function(iwidget) {
					// add the name (or undefined) to the row
					this.layout.push(lang.getObject('name', false, iwidget));
				}, this);
			}

			// in case no submit button has been defined, we define one and hide it
			// this allows us to connect to the onSubmit event in any case
			this.submitButtonDefined = false;
			array.forEach(this.buttons, lang.hitch(this, function(ibutton) {
				if ('submit' == ibutton.name) {
					this.submitButtonDefined = true;
					return false; // break loop
				}
			}));
			if (!this.submitButtonDefined) {
				// no submit button defined, add a hidden one :)
				this.buttons = this.buttons instanceof Array ? this.buttons : [];
				this.buttons.push({
					label: 'submit',
					name: 'submit',
					'class': 'dijitOffScreen',
					tabindex: '-1' // to not focus hidden button when tabbing
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
			if (!(widget_name in this._widgets)) {
				//console.log( 'Form.showWidget: could not find widget ' + widget_name );
				return;
			}
			this._widgets[ widget_name ].set( 'visible', visibility );
		},

		buildRendering: function() {
			this.inherited(arguments);

			// render the widgets and the layout if no content is given
			if (!this.content) {
				this._widgets = render.widgets(this.widgets, this);
				this._buttons = render.buttons(this.buttons || [], this);
				this._container = render.layout(this.layout, this._widgets, this._buttons);
				// if the submit button was not defined and no other buttons are in the same
				// layout row then we hide the layout row
				if (!this.submitButtonDefined && this._buttons.submit.getParent().getChildren().length === 1) {
					domClass.add(this._buttons.submit.getParent().domNode, 'dijitOffScreen');
				}

				// start processing the layout information
				this._container.placeAt(this.containerNode);
			}
			// otherwise, register content and create an internal dictionary of widgets
			else {
				var errMsg = "umc.widgets.Form: As 'content' is specified, the property 'widgets' is expected to be an array of widgets.";

				// register content
				tools.assert(this.content.domNode && this.content.declaredClass, errMsg);
				this.content.placeAt(this.containerNode);

				// create internal dictionary of widgets
				if (this.widgets instanceof Array) {
					array.forEach(this.widgets, function(iwidget) {
						// make sure the object looks like a widget
						tools.assert(iwidget.domNode && iwidget.declaredClass, errMsg);
						tools.assert(iwidget.name, "umc.widgets.Form: Each widget needs to specify the property 'name'.");

						// add entry to dictionary
						this._widgets[iwidget.name] = iwidget;
					}, this);
				}
				// `widgets` is already a dictionary
				else if (typeof this.widgets == "object") {
					this._widgets = this.widgets;
				}
			}

			this._updateAllReady();
		},

		postCreate: function() {
			this.inherited(arguments);

			// prepare registration of onChange events
			tools.forIn(this._widgets, function(iname, iwidget) {
				// check whether the widget has a `depends` field
				if (!iwidget.depends) {
					return;
				}

				// loop over all dependencies and cache the dependencies as a map from
				// publishers -> receivers
				var depends = tools.stringOrArray(iwidget.depends);
				array.forEach(depends, lang.hitch(this, function(idep) {
					this._dependencyMap[idep] = this._dependencyMap[idep] || [];
					this._dependencyMap[idep].push(iwidget);
				}));
			}, this);

			// register all necessary onChange events to handle dependencies
			tools.forIn(this._dependencyMap, function(iname) {
				if (iname in this._widgets) {
					var widget = this.getWidget(iname);
					this.own(widget.watch('value', lang.hitch(this, function() {
						this._updateDependencies(iname);
					})));
					if (widget.ready) {
						// needed (only) for initial loading,
						// so it does not need to be updated
						// with every new _readyDeferred
						widget.ready().then(lang.hitch(this, function() {
							this._updateDependencies(iname);
						}));
					}
				}
			}, this);

			// register callbacks for onSubmit and onReset events
			array.forEach(['submit', 'reset'], function(ievent) {
				var orgCallback = lang.getObject(ievent + '.callback', false, this._buttons);
				if (orgCallback) {
					this._buttons[ievent].callback = function() { };
				}
				this.on(ievent, lang.hitch(this, function(e) {
					// prevent standard form submission
					if (e && e.preventDefault) {
						e.preventDefault();
					}

					// if there is a custom callback, call it with all form values
					if (typeof orgCallback == "function") {
						orgCallback(this.get('value'));
					}
				}));
			}, this);
		},

		startup: function() {
			//console.log('### Form: startup - container:', this._container);
			this.inherited(arguments);

			// trigger initial dependencies
			tools.forIn(this._widgets, function(iname, iwidget) {
				// check whether the widget has a `depends` field
				if (!iwidget.depends) {
					return;
				}

				if (!iwidget._loadValues) {
					return;
				}

				// collect ready-deferreds from all dependencies
				var depends = tools.stringOrArray(iwidget.depends);
				var deferreds = array.map(depends, function(jdep) {
					var jwidget = this.getWidget(jdep);
					if (jwidget) {
						return jwidget.ready ? jwidget.ready() : null;
					}
					return null;
				}, this);

				// trigger the widget as soon as all its dependencies are resolved
				all(deferreds).then(lang.hitch(this, function() {
					var values = this.get('value');
					iwidget._loadValues(values);
				}));
			}, this);

			// call the containers startup function if necessary
			if (this._container) {
				this._container.startup();
			}

			// send event valuesInitialized when ready
			this.ready().then(lang.hitch(this, function() {
				//console.log('### Form: all ready');
				this.onValuesInitialized();

				// update all dependencies when all widgets are ready
				tools.forIn(this._dependencyMap, function(iname) {
					if (iname in this._widgets) {
						this._updateDependencies(iname);
					}
				}, this);
			}));
		},

		gatherFormValues: function() {
			kernel.deprecated('umc/widgets/Form:gatherFormValues()', 'use umc/widgets/Form:get("value") instead');
			return this.get('value');
		},

		_getValueAttr: function() {
			// gather values from all registered widgets
			var vals = {};
			tools.forIn(this._widgets, function(iname, iwidget) {
				var val = iwidget.get('value');
				if (val !== undefined) {
					// ignore undefined values
					vals[iname] = val;
				}
			}, this);

			// add item ID to the dictionary in case it is not already included
			if (this.moduleStore && this.moduleStore.idProperty) {
				var idProperty = this.moduleStore.idProperty;
				if (!(idProperty in vals) && null !== this._loadedID) {
					vals[idProperty] = this._loadedID;
				}
			}

			return vals;
		},

		clearFormValues: function() {
			// clear all values based on a list of widgets
			tools.forIn(this._widgets, function(iname, iwidget) {
				// value could be a string, an array, or a dict... query first the value
				// and reset the value accordingly
				var val = iwidget.get('value');
				if (typeof val == "string") {
					iwidget.set('value', '');
				}
				else if (val instanceof Array) {
					iwidget.set('value', []);
				}
				else if (typeof val == "object") {
					iwidget.set('value', {});
				}
				else if (typeof val == 'number') {
					iwidget.set('value', 0);
				}
			}, this);
			if (this._loadedID) {
				this._loadedID = null;
			}
		},

		setFormValues: function(values) {
			// set all values based on a list of widgets
			tools.forIn(values, function(iname, ival) {
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

		_updateDependencies: function(/*String*/ publisherName) {
			// summary:
			//		This method is called when the value of the specified form widget
			//		has changed. All widgets that have registered a dependency on
			//		this particular widget are being update.

			//var tmp = [];
			//array.forEach(this._dependencyMap[publisherName], function(i) {
			//	tmp.push(i.name);
			//});
			//var json = require("dojo/json");
			//console.log(lang.replace('# _updateDependencies: publisherName={0} _dependencyMap[{0}]={1}', [publisherName, json.stringify(tmp)]));

			if (publisherName in this._dependencyMap) {
				var values = this.get('value');
				var readyInfo = this._allReadyNamed;
				array.forEach(this._dependencyMap[publisherName], lang.hitch(this, function(ireceiver) {
					if (ireceiver && ireceiver._loadValues) {
						ireceiver._loadValues(values, readyInfo);
						if (this.standbyDuring) {
							this.standbyDuring(this.ready(), this.standbyContent, this.standbyOptions);
						}
					}
				}));
			}
		},

		load: function(/*String*/ itemID) {
			// summary:
			//		Send off an UMCP query to the server for querying the data for the form.
			//		For this the field umcpGetCommand needs to be set.
			// itemID: String
			//		ID of the object that should be loaded.

			tools.assert(this.moduleStore, 'In order to load form data from the server, the umc.widgets.Form.moduleStore needs to be set.');
			tools.assert(itemID, 'The specifid itemID for umc.widgets.Form.load() must be valid.');

			// query data from server
			var deferred = new Deferred();
			this.moduleStore.get(itemID).then(lang.hitch(this, function(data) {
				var values = this.get('value');
				var newValues = {};

				// copy all the fields that exist in the form
				tools.forIn(data, function(ikey, ival) {
					if (ikey in values) {
						newValues[ikey] = ival;
					}
				}, this);

				// set all values at once
				this.setFormValues(newValues);
				this._loadedID = itemID;

				// fire event
				this.onLoaded(true);
				// resolve a deferred instead of returning moduleStore.get() directly (also a deferred)
				//   because this.setFormValues may take some time (MultiInput!)
				deferred.resolve(data);
			}), lang.hitch(this, function() {
				// fire event also in error case
				this.onLoaded(false);
				deferred.cancel();
			}));

			return deferred;
		},

		save: function() {
			// summary:
			//		Gather all form values and send them to the server via UMCP.
			//		For this, the field umcpSetCommand needs to be set.

			tools.assert(this.moduleStore, 'In order to save form data to the server, the umc.widgets.Form.moduleStore needs to be set');

			// sending the data to the server
			var values = this.get('value');
			var deferred = null;
			if (this._loadedID === null || this._loadedID === undefined || this._loadedID === '') {
				deferred = this.moduleStore.add(values, undefined, this);
			}
			else {
				// prepare an options dict containing the original id of the object
				// (in case the object id is being changed)
				var options = {};
				var idProperty = lang.getObject('moduleStore.idProperty', false, this);
				if (idProperty) {
					options[idProperty] = this._loadedID;
				}
				deferred = this.moduleStore.put(values, options, this);
			}
			deferred = deferred.then(lang.hitch(this, function(data) {
				// fire event
				this.onSaved(true);
				return data;
			}), lang.hitch(this, function() {
				// fire event also in error case
				this.onSaved(false);
			}));

			return deferred;
		},

		setValid: function(obj) {
			if (!obj) {
				tools.forIn(this._widgets, function(name, widget) {
					if (widget.setValid) {
						widget.setValid(null);
					}
				});
			} else {
				tools.forIn(obj, lang.hitch(this, function(name, value) {
					var widget = this.getWidget(name);
					if (widget.setValid) {
						widget.setValid(value.isValid, value.message);
					}
				}));
			}
		},

		// TODO this shouls be called in validate. Make sure there are no side-effects if doing so
		focusFirstInvalidWidget: function() {
			var widgetNamesInOrder = tools.flatten(this.layout);
			widgetNamesInOrder.some(lang.hitch(this, function(widgetName) {
				var widget = this.getWidget(widgetName);
				if (widget && widget.get('visible') && !widget.get('disabled') && !widget.isValid()) {
					widget.focusInvalid();
					return true;
				}
			}));
		},

		validate: function() {
			return this.getInvalidWidgets().length === 0;
		},

		getInvalidWidgets: function() {
			var widgets = [];

			tools.forIn(this._widgets, function(iname, iwidget) {
				if (!iwidget.get('visible')) {
					// ignore hidden widgets
					return;
				}
				// need to set _hasBeenBlurred such that the state is displayed correctly
				iwidget._hasBeenBlurred = true;
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
		},

		onSubmit: function() {
			// prevent page reload
			return false;
		},

		onValidationError: function(/*String*/message, /*Object*/ data) {
			// naive implementation
			var focus_set = false;
			tools.forIn(data, lang.hitch(this, function(iwidget, error_msg) {
				var worked = false;
				try {
					// TODO: return true in setValid
					// except for our checkBox
					// or (better) implement setValid for checkBox
					var widget = this.getWidget(iwidget);
					if (widget && widget.setValid) {
						worked = widget.setValid(false, error_msg) !== false;
					}
				} catch(e) {
					console.log(iwidget, e);
				}
				if (!worked) {
					this.addNotification(error_msg);
				}
			}));
		},

		_updateAllReady: function() {
			// wait for all widgets to be ready
			this._allReadyNamed = {};
			var deferreds = [];
			var nWidgets = 0;
			var lastLabel = null;
			var widgetProgressInPercent = {};

			var _getOverallProgress = function() {
				var overallPercentage = 0;
				tools.forIn(widgetProgressInPercent, function(iname, ipercent) {
					overallPercentage += ipercent;
				});
				return overallPercentage / nWidgets;
			};

			tools.forIn(this._widgets, function() { ++nWidgets; });
			tools.forIn(this._widgets, function(iname, iwidget) {
				var iwidgetReadyDeferred = iwidget.ready ? iwidget.ready() : null;
				widgetProgressInPercent[iname] = 0;
				when(iwidgetReadyDeferred,
					lang.hitch(this, function() {
						widgetProgressInPercent[iname] = 100;
						lastLabel = iwidget.label || lastLabel || iwidget.name;
						var progress = {
							percentage: _getOverallProgress(),
							message: _('%s loaded', lastLabel)
						};
						this.progressDeferred._lastProgress = progress; // to be able to get current progress if one missed the beginning
						this.progressDeferred.progress(progress);
					}),
					undefined, // cancelled
					lang.hitch(this, function(iprogress) { // progress
						var label = iwidget.label || iwidget.name;
						var message = '';
						if ('percentage' in iprogress) {
							widgetProgressInPercent[iname] = iprogress.percentage;
							if (iprogress.percentage < 100) {
								message = _('%s (%.1f%)', label, iprogress.percentage);
							}
							else {
								// 'loaded' message for 100%
								message = _('%s loaded', label);
							}
						}
						if (iprogress.message) {
							message = _('%(label)s: %(message)s', {label: label, message: iprogress.message});
						}
						var progress = {
							percentage: _getOverallProgress(),
							message: message
						};
						this.progressDeferred.progress(progress);
					})
				);
				this._allReadyNamed[iname] = iwidgetReadyDeferred;
				deferreds.push(iwidgetReadyDeferred);
			}, this);
			all(deferreds).then(lang.hitch(this, function() {
				this.progressDeferred.resolve();
			}));
		},

		ready: function() {
			// update the internal list in order to wait until everybody is ready
			if (this.progressDeferred.isFulfilled()) {
				this.progressDeferred = new Deferred();
				this._updateAllReady();
			}
			return this.progressDeferred;
		}
	});
});

