/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.tools");

dojo.require("dojox.layout.TableContainer");
dojo.require("umc.widgets.ContainerWidget");

dojo.mixin(umc.tools, {
	umcpCommand: function(
		/*String*/ commandStr, 
		/*Object?*/ dataObj, 
		/*Boolean?*/ handleErrors) {

		// summary:
		//		Encapsulates an AJAX call for a given UMCP command.
		// returns:
		//		A deferred object.

		// set default values for parameters
		dataObj = dataObj || {};
		handleErrors = undefined === handleErrors || handleErrors;

		// build the URL for the UMCP command
		var url = '/umcp/command/' + commandStr;
		
		// check special case for 'get' and 'auth' commands .. there we don't
		// need to add 'command'
		if ((/^(get\/|auth)/).test(commandStr)) {
			url = '/umcp/' + commandStr;
		}

		// make the AJAX call
		var call = dojo.xhrPost({
			url: url,
			preventCache: true,
			handleAs: 'json',
			headers: { 
				'Content-Type': 'application/json' 
			},
			postData: dojo.toJson(dataObj)
		});

		// handle XHR errors unless not specified otherwise
		if (handleErrors) {
			call = call.then(function(data) {
				// do not modify the data
				return data; // Object
			}, function(error) {
				// handle errors
				umc.tools.handleErrorStatus(dojo.getObject('status', false, error));

				// return the error
				return error; // Error
			});
		}

		// return the Deferred object
		return call; // Deferred
	},

	xhrPostJSON: function(/*Object*/ dataObj, /*String*/ url, /*function*/ xhrHandler, /*Boolean?*/ handleErrors) {
		// perpare XHR property object with our standard JSON configuration
		var xhrArgs = {
			url: url,
			preventCache: true,
			handleAs: 'json',
			headers: { 
				'Content-Type': 'application/json' 
			},
			postData: dojo.toJson(dataObj),
			handle: function(dataOrError, ioargs) {
				// handle XHR errors unless not specified otherwise
				if (undefined === handleErrors || handleErrors) {
					umc.tools.handleErrorStatus(dojo.getObject('xhr.status', false, ioargs));
				}

				// call custom callback
				xhrHandler(dataOrError, ioargs);
			}
		};

		// send off the data
		var xhrs = dojo.xhrPost(xhrArgs);
	},

	handleErrorStatus: function(status) {
		if (undefined !== status) {
			// handle the different status codes
			switch (status) {
				case 200: // evertything is ok :)
					return;
				case 401:
					umc.app.loginDialog.show();
					if (umc.app.loggingIn) {
						umc.app.alert('Wrong credentials, please try again!');
					}
					else {
						umc.app.loggingIn = true;
						umc.app.alert('Your session has expired, please log in again!');
					}
					return;
				case 403:
					umc.app.alert('You are not authorized to perform this action!');
					return;
				case 503:
					umc.app.alert('This service is temporarily not available (status: 503)!');
					return;
				default:
					umc.app.alert('An unexpected HTTP-error occurred (status: ' + status + ')');
					return;
			}
		}
		
		// probably server timeout, could also be a different error
		umc.app.alert('An error occurred while connecting to the server, please try again later.');
	},

	forIn: function(/*Object*/ obj, /*Function*/callback, /*Object?*/scope) {
		// summary:
		//		Iterate over all elements of an object checking with hasOwnProperty()
		//		whether the element belongs directly to the object.
		//		Optionally, a scope can be defined.
		//
		//		This method is similar to dojox.lang.functional.forIn wher no hasOwnProperty()
		//		check is carried out.

		scope = scope || dojo.global;
		for (var i in obj) {
			if (obj.hasOwnProperty(i)) {
				callback.call(scope, obj[i], i, obj);
			}
		}
	},

	assert: function(/* boolean */ booleanValue, /* string? */ message){
		// summary: 
		// 		Throws an exception if the assertion fails.
		// description: 
		// 		If the asserted condition is true, this method does nothing. If the
		// 		condition is false, we throw an error with a error message. 
		// booleanValue: 
		//		Must be true for the assertion to succeed.
		// message: 
		//		A string describing the assertion.

		// throws: Throws an Error if 'booleanValue' is false.
		if(!booleanValue){
			var errorMessage = "An assert statement failed";
			if(message){
				errorMessage += ':\n' + message;
			}
			
			// throw error
			throw new Error(errorMessage);
		}
	},

	renderWidgets: function(/*Object[]*/ widgetsConf) {
		// summary:
		//		Renders an array of widget config objects.
		// returns:
		//		A dictionary of widget objects.

		// iterate over all widget config objects
		var widgets = { };
		dojo.forEach(widgetsConf, function(iconf) {
			// render the widget
			var widget = this.renderWidget(iconf);
			if (widget) {
				widgets[iconf.name] = widget;
			}
		}, this);
		return widgets; // Object
	},

	renderWidget: function(/*Object*/ widgetConf) {
		// make a copy of the widget's config object and remove 'type'
		var conf = dojo.clone(widgetConf);
		delete conf.type;

		// include the corresponding module for the widget
		dojo.require('umc.widgets.' + widgetConf.type);

		// create the new widget according to its type
		var WidgetClass = dojo.getObject('umc.widgets.' + widgetConf.type);
		if (!WidgetClass) {
			return undefined; // undefined
		}
		return new WidgetClass(conf); // Widget
	},

	renderButtons: function(/*Object[]*/ buttonsConf) {
		// summary:
		//		Renders an array of button config objects.
		// returns:
		//		A dictionary of button widgets.

		umc.tools.assert(dojo.isArray(buttonsConf), 'renderLayout: The list of buttons is expected to be an array.');

		// render all buttons
		var buttons = { 
			_order: [] // internal field to store the correct order of the buttons
		};
		dojo.forEach(buttonsConf, function(i) {
			var btn = umc.tools.renderButton(i);
			buttons[i.name] = btn;
			buttons._order.push(btn);
		});

		// return buttons
		return buttons; // Object
	},
			
	renderButton: function(/*Object*/ buttonConf) {
		// specific button types need special care: submit, reset
		var buttonClassName = 'Button';
		if ('submit' == buttonConf.name) {
			buttonClassName = 'SubmitButton';
		}
		if ('reset' == buttonConf.name) {
			buttonClassName = 'ResetButton';
		}

		// load the java script code for the button class
		dojo.require('umc.widgets.' + buttonClassName);
		var ButtonClass = dojo.getObject('umc.widgets.' + buttonClassName);
		
		// render the button
		var button = new ButtonClass({
			label: buttonConf.label,
			callback: buttonConf.callback
		});

		// connect event handler for onClick .. yet only for normal buttons
		if ('Button' == buttonClassName) {
			dojo.connect(button, 'onClick', buttonConf.callback);
		}

		// done, return the button
		return button; // umc.widgets.Button
	},
	
	renderLayout: function(/*String[][]*/ layout, /*Object*/ widgets, /*Object?*/ buttons, /*Integer?*/ cols) {
		// summary:
		//		Render a widget containing a set of widgets as specified by the layout.
		//		The optional parameter cols specifies the number of columns.

		// setup default parameters
		cols = cols || 2;

		// create a layout manager (TableContainer)
		var container = new dojox.layout.TableContainer({
			cols: cols,
			showLabels: true,
			orientation: 'vert'
		});

		// check whether the parameters are correct
		umc.tools.assert(dojo.isArray(layout) &&
				layout.length &&
				dojo.isArray(layout[0]),
				'Invalid layout configuration object!');

		// iterate through the layout elements and the widgets at the correct position
		for (var irow = 0; irow < layout.length; ++irow) {
			for (var icol = 0; icol < cols; ++icol) {
				var name = layout[irow][icol];
				if (name) {
					// if a string is given, try to insert the widget
					umc.tools.assert(name in widgets, 'The widget "' + name + '" requested in the layout has not been specified.');
					container.addChild(widgets[name]);
				}
				else {
					// otherwise insert an empty widget at the position
					container.addChild(new dijit._Widget({}));
				}
			}
		}

		// add buttons if specified
		if (buttons) {
			// create a container for all buttons since they need a different layout
			var buttonContainer = new umc.widgets.ContainerWidget({ });

			// add all buttons to the container in the correct order
			// (i.e., using the interal array field _order) 
			dojo.forEach(buttons._order, function(ibutton) {
				buttonContainer.addChild(ibutton);
			});

			// add button container to main layout into the second column
			container.addChild(new dijit._Widget({}));
			container.addChild(buttonContainer);
		}

		// start processing the layout information
		container.startup();

		// return the container
		return container; // dojox.layout.TableContainer
	}
});


