/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.tools");

dojo.require("umc.app");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.LabelPane");
dojo.require("umc.widgets.Tooltip");

dojo.mixin(umc.tools, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}));
dojo.mixin(umc.tools, {
	umcpCommand: function(
		/*String*/ commandStr,
		/*Object?*/ dataObj,
		/*Boolean?*/ handleErrors,
		/*String?*/ flavor) {

		// summary:
		//		Encapsulates an AJAX call for a given UMCP command.
		// returns:
		//		A deferred object.

		// when logging in, ignore all except the AUTH command
		if (umc.app.loggingIn && !(/^auth$/i).test(commandStr)) {
			console.log(this._('WARNING: Ignoring command "%s" since user is logging in', commandStr));
			var deferred = new dojo.Deferred();
			deferred.errback();
			return deferred;
		}

		// set default values for parameters
		dataObj = dataObj || {};
		handleErrors = undefined === handleErrors || handleErrors;

		// build the URL for the UMCP command
		var url = '/umcp/command/' + commandStr;

		// check special case for 'get' and 'auth' commands .. there we don't
		// need to add 'command'
		if ((/^(get\/|set$|auth)/i).test(commandStr)) {
			url = '/umcp/' + commandStr;
		}

		var body = {
			 options: dataObj
		};
		if ( flavor !== undefined && flavor !== null ) {
			body.flavor = flavor;
		}

		// make the AJAX call
		var call = dojo.xhrPost({
			url: url,
			preventCache: true,
			handleAs: 'json',
			headers: { 
				'Content-Type': 'application/json' 
			},
			postData: dojo.toJson(body)
		});

		// handle XHR errors unless not specified otherwise
		if (handleErrors) {
			call = call.then(function(data) {
				// do not modify the data
				if ( data && data.message ) {
					if ( data.status == 200 ) {
						umc.app.notify( data.message );
					} else {
						umc.app.alert( data.message );
					}
				}

				return data; // Object
			}, function(error) {
				// handle errors
				umc.tools.handleErrorStatus(dojo.getObject('status', false, error), error);

				// propagate the error
				throw error;
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

	// _statusMessages:
	//		A dictionary that translates a status to an error message

	// Status( 'SUCCESS'						   , 200, ( 'OK, operation successful' ) ),
	// Status( 'SUCCESS_MESSAGE'				   , 204, ( 'OK, containing report message' ) ),
	// Status( 'SUCCESS_PARTIAL'				   , 206, ( 'OK, partial response' ) ),
	// Status( 'SUCCESS_SHUTDOWN'				  , 250, ( 'OK, operation successful ask for shutdown of connection' ) ),
	// 
	// Status( 'CLIENT_ERR_NONFATAL'			   , 301, ( 'A non-fatal error has occured processing may continue' ) ),
	// 
	// Status( 'BAD_REQUEST'					   , 400, ( 'Bad request' ) ),
	// Status( 'BAD_REQUEST_UNAUTH'				, 401, ( 'Unauthorized' ) ),
	// Status( 'BAD_REQUEST_FORBIDDEN'			 , 403, ( 'Forbidden' ) ),
	// Status( 'BAD_REQUEST_NOT_FOUND'			 , 404, ( 'Not found' ) ),
	// Status( 'BAD_REQUEST_NOT_ALLOWED'		   , 405, ( 'Command not allowed' ) ),
	// Status( 'BAD_REQUEST_INVALID_ARGS'		  , 406, ( 'Invalid command arguments' ) ),
	// Status( 'BAD_REQUEST_INVALID_OPTS'		  , 407, ( 'Invalid or missing command options' ) ),
	// Status( 'BAD_REQUEST_AUTH_FAILED'		   , 411, ( 'The authentication has failed' ) ),
	// Status( 'BAD_REQUEST_ACCOUNT_EXPIRED'	   , 412, ( 'The account is expired and can not be used anymore' ) ),
	// Status( 'BAD_REQUEST_ACCOUNT_DISABLED'	  , 413, ( 'The account as been disabled' ) ),
	// Status( 'BAD_REQUEST_UNAVAILABLE_LOCALE'	, 414, ( 'Specified locale is not available' ) ),
	//
	// Status( 'SERVER_ERR'						, 500, ( 'Internal error' ) ),
	// Status( 'SERVER_ERR_MODULE_DIED'			, 510, ( 'Module process died unexpectedly' ) ),
	// Status( 'SERVER_ERR_MODULE_FAILED'		  , 511, ( 'Connection to module process failed' ) ),
	// Status( 'SERVER_ERR_CERT_NOT_TRUSTWORTHY'   , 512, ( 'SSL server certificate is not trustworthy' ) ),
	//
	// Status( 'UMCP_ERR_UNPARSABLE_HEADER'		, 551, ( 'Unparsable message header' ) ),
	// Status( 'UMCP_ERR_UNKNOWN_COMMAND'		  , 552, ( 'Unknown command' ) ),
	// Status( 'UMCP_ERR_INVALID_NUM_ARGS'		 , 553, ( 'Invalid number of arguments' ) ),
	// Status( 'UMCP_ERR_UNPARSABLE_BODY'		  , 554, ( 'Unparsable message body' ) ),
	//
	// Status( 'MODULE_ERR'						, 600, ( 'Error occuried during command processing' ) ),
	// Status( 'MODULE_ERR_COMMAND_FAILED'		 , 601, ( 'The execution of a command caused an fatal error' ) )

	_statusMessages: {
		400: umc.tools._( 'Could not fulfill the request.' ),
		401: umc.tools._( 'Your session has expired, please login again.' ), // error occurrs only when user is not authenticated and a request is sent
		403: umc.tools._( 'You are not authorized to perform this action.' ),

		404: umc.tools._( 'Webfrontend error: The specified request is unknown.' ),
		406: umc.tools._( 'Webfrontend error: The specified UMCP command arguments of the request are invalid.' ),
		407: umc.tools._( 'Webfrontend error: The specified arguments for the UMCP module method are invalid or missing.'),

		411: umc.tools._( 'Authentication failed, please login again.' ),
		412: umc.tools._( 'The account is expired and can not be used anymore.' ),
		413: umc.tools._( 'The account as been disabled.' ),
		414: umc.tools._( 'Specified locale is not available.' ),

		500: umc.tools._( 'Internal server error.' ),
		510: umc.tools._( 'Internal server error: The module process died unexpectedly.' ),
		511: umc.tools._( 'Internal server error: Could not connect to the module process.' ),
		512: umc.tools._( 'Internal server error: The SSL server certificate is not trustworthy. Please check your SSL configurations.' ),

		551: umc.tools._( 'Internal UMC protocol error: The UMCP message header could not be parsed.' ),
		554: umc.tools._( 'Internal UMC protocol error: The UMCP message body could not be parsed.' ),

		590: umc.tools._( 'Internal module error: An error occured during command processing.' ),
		591: umc.tools._( 'Internal module error: The execution of a command caused an fatal error.' )
	},

	handleErrorStatus: function(status, error) {
		// handle the different status codes
		if (undefined !== status && status in this._statusMessages) {
			// special cases during login, only show a notification
			if (401 == status || 411 == status) {
				umc.app.login();
				umc.app.notify(this._statusMessages[status]);
			}
			// all other cases
			else {
				var errorMsg = dojo.getObject('responseText', false, error);
				umc.app.alert(this._statusMessages[status]);// + (errorMsg ? this._('<br>Error message from server: %s', errorMsg) : ''));
			}
		}
		else if (undefined !== status) {
			// unknown status code .. should not happen
			umc.app.alert(this._('An unknown error with status code %s occurred while connecting to the server, please try again later.', status));
		}
		else {
			// probably server timeout, could also be a different error
			umc.app.alert(this._('An error occurred while connecting to the server, please try again later.'));
		}
	},

	forIn: function(/*Object*/ obj, /*Function*/ callback, /*Object?*/ scope, /*Boolean?*/ inheritedProperties) {
		// summary:
		//		Iterate over all elements of an object.
		// description:
		//		Iterate over all elements of an object checking with hasOwnProperty()
		//		whether the element belongs directly to the object.
		//		Optionally, a scope can be defined.
		//		The callback function will be called with the parameters
		//		callback(/*String*/ key, /*mixed*/ value, /*Object*/ obj).
		//
		//		This method is similar to dojox.lang.functional.forIn wher no hasOwnProperty()
		//		check is carried out.

		scope = scope || dojo.global;
		for (var i in obj) {
			if (obj.hasOwnProperty(i) || inheritedProperties) {
				callback.call(scope, i, obj[i], obj);
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
			var errorMessage = this._('An assert statement failed');
			if(message){
				errorMessage += ':\n' + message;
			}
			
			// throw error
			var e = new Error(errorMessage);
			throw e;
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
			// ignore empty elements
			if (!iconf || !dojo.isObject(iconf)) {
				return true;
			}

			// copy the property 'id' to 'name'
			var conf = dojo.mixin({}, iconf);
			conf.name = iconf.id || iconf.name;

			// render the widget
			var widget = this.renderWidget(conf);
			if (widget) {
				widgets[conf.name] = widget;
			}
		}, this);

		return widgets; // Object
	},

	renderWidget: function(/*Object*/ widgetConf) {
		if (!widgetConf) {
			return undefined;
		}
		if (!widgetConf.type) {
			console.log(dojo.replace("WARNING in umc.tools.renderWidget: The type '{type}' of the widget '{name}' is invalid. Ignoring error.", widgetConf));
			return undefined;
		}

		// make a copy of the widget's config object and remove 'type'
		var conf = dojo.mixin({}, widgetConf);
		delete conf.type;

		// remove property 'id'
		delete conf.id;

		var WidgetClass = undefined;
		try {
			// include the corresponding module for the widget
			dojo['require']('umc.widgets.' + widgetConf.type);

			// create the new widget according to its type
			WidgetClass = dojo.getObject('umc.widgets.' + widgetConf.type);
		}
		catch (error) { }
		if (!WidgetClass) {
			console.log(dojo.replace("WARNING in umc.tools.renderWidget: The widget class 'umc.widgets.{type}' defined by widget '{name}' cannot be found. Ignoring error.", widgetConf));
			return undefined;
		}
		var widget = new WidgetClass(conf); // Widget

		// create a tooltip if there is a description
		if (widgetConf.description) {
			var tooltip = new umc.widgets.Tooltip({
				label: widgetConf.description,
				connectId: [ widget.domNode ]
			});
		}

		return widget; // dijit._Widget
	},

	renderButtons: function(/*Object[]*/ buttonsConf) {
		// summary:
		//		Renders an array of button config objects.
		// returns:
		//		A dictionary of button widgets.

		umc.tools.assert(dojo.isArray(buttonsConf), 'renderButtons: The list of buttons is expected to be an array.');

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
		dojo['require']('umc.widgets.' + buttonClassName);
		var ButtonClass = dojo.getObject('umc.widgets.' + buttonClassName);
		
		// render the button
		var button = new ButtonClass({
			label: buttonConf.label,
			callback: buttonConf.callback,
			iconClass: buttonConf.iconClass
		});

		// connect event handler for onClick .. yet only for normal buttons
		if ('Button' == buttonClassName) {
			button.connect(button, 'onClick', buttonConf.callback);
		}

		// done, return the button
		return button; // umc.widgets.Button
	},
	
	renderLayout: function(/*Array*/ layout, /*Object*/ widgets, /*Object?*/ buttons) {
		// summary:
		//		Render a widget containing a set of widgets as specified by the layout.
		//		The optional parameter cols specifies the number of columns.

		// create a container
		var globalContainer = new umc.widgets.ContainerWidget({});

		// check whether the parameters are correct
		umc.tools.assert(dojo.isArray(layout), 
				'umc.tools.renderLayout: Invalid layout configuration object!');

		// iterate through the layout elements
		for (var iel = 0; iel < layout.length; ++iel) {

			// element can be:
			//   String -> reference to widget
			//   Array  -> references to widgets
			//   Object -> grouped widgets -> recursive call of renderLayout()
			var el = layout[iel];
			var elList = null;
			if (dojo.isString(el)) {
				elList = [el];
			}
			else if (dojo.isArray(el)) {
				elList = el;
			}

			// for single String / Array
			if (elList) {
				// add current form widgets to layout
				var elContainer = new umc.widgets.ContainerWidget({});
				dojo.forEach(elList, function(jel) {
					// make sure the reference to the widget exists
					if (!(jel in widgets)) {
						console.log(dojo.replace("WARNING in umc.tools.renderLayout: The widget '{0}' is not defined in the argument 'widgets'. Ignoring error.", [jel]));
						return true;
					}

					// add the widget surrounded with a LabelPane
					var widget = widgets[jel];
					elContainer.addChild(new umc.widgets.LabelPane({
						label: widget.label,
						content: widget
					}));
				}, this);
				globalContainer.addChild(elContainer);
			}
			// for Object (i.e., a grouping box)
			else if (dojo.isObject(el) && el.layout) {
				//console.log('### renderLayout - recursive call');
				//console.log(el);
				globalContainer.addChild(new umc.widgets.GroupBox({
					legend: el.label,
					content: this.renderLayout(el.layout, widgets)
				}));
			}
		}

		// add buttons if specified
		if (buttons) {
			// add all buttons to a container in the correct order
			// (i.e., using the interal array field _order) 
			var buttonContainer = new umc.widgets.ContainerWidget({});
			dojo.forEach(buttons._order, function(ibutton) {
				buttonContainer.addChild(ibutton);
			});
			globalContainer.addChild(buttonContainer);
		}

		// start processing the layout information
		globalContainer.startup();

		// return the container
		return globalContainer; // dojox.layout.TableContainer
	},

	cmpObjects: function(/*mixed...*/) {
		// summary:
		//		Returns a comparison functor for Array.sort() in order to sort arrays of
		//		objects/dictionaries. 
		// description:
		//		The function arguments specify the sorting order. Each function argument
		//		can either be a string (specifying the object attribute to compare) or an
		//		object with 'attribute' specifying the attribute to compare. Additionally,
		//		the object may specify the attributes 'descending' (boolean), 'ignoreCase' 
		//		(boolean).
		//		In order to be useful for grids and sort options, the arguments may also
		//		be one single array.
		// example:
		//	|	var list = [ { id: '0', name: 'Bob' }, { id: '1', name: 'alice' } ];
		//	|	var cmp = umc.tools.cmpObjects({
		//	|		attribute: 'name', 
		//	|		descending: true, 
		//	|		ignoreCase: true
		//	|	});
		//	|	list.sort(cmp);
		// example:
		//	|	var list = [ { id: '0', val: 100, val2: 11 }, { id: '1', val: 42, val2: 33 } ];
		//	|	var cmp = umc.tools.cmpObjects('val', {
		//	|		attribute: 'val2', 
		//	|		descending: true
		//	|	});
		//	|	list.sort(cmp);
		//	|	var cmp2 = umc.tools.cmpObjects('val', 'val2');
		//	|	list.sort(cmp2);

		// in case we got a single array as argument, 
		var args = arguments;
		if (1 == arguments.length && dojo.isArray(arguments[0])) {
			args = arguments[0];
		}

		// prepare unified ordering property list
		var order = [];
		for (var i = 0; i < args.length; ++i) {
			// default values
			var o = {
				attr: '',
				desc: 1,
				ignCase: false
			};

			// entry for ordering can by a String or an Object
			if (dojo.isString(args[i])) {
				o.attr = args[i];
			}
			else if (dojo.isObject(args[i]) && 'attribute' in args[i]) {
				o.attr = args[i].attribute;
				o.desc = (args[i].descending ? -1 : 1);
				o.ignCase = args[i].ignoreCase;
			}
			else {
				// error case
				umc.tools.assert(false, 'Wrong parameter for umc.tools.cmpObjects(): ' + dojo.toJson(args));
			}

			// add order entry to list
			order.push(o);
		}

		// return the comparison function
		return function(_a, _b) {
			for (var i = 0; i < order.length; ++i) {
				var o = order[i];

				// make sure the attribute is specified in both objects
				if (!(o.attr in _a) || !(o.attr in _b)) {
					return 0;
				}

				// check for lowercase
				var a = _a[o.attr];
				var b = _b[o.attr];
				if (o.ignCase) {
					a = a.toLowerCase();
					b = b.toLowerCase();
				}

				// check for lower/greater
				if (a < b) {
					return -1 * o.desc;
				}				
				if (a > b) {
					return 1 * o.desc;
				}
			}
			return 0;		
		};
	}
});


