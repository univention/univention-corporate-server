/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.tools");

dojo.require("dojox.layout.TableContainer");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.app");
dojo.require("umc.i18n");

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
			deferred = new dojo.Deferred();
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

	// Status( 'SUCCESS'                           , 200, ( 'OK, operation successful' ) ),
	// Status( 'SUCCESS_MESSAGE'                   , 204, ( 'OK, containing report message' ) ),
	// Status( 'SUCCESS_PARTIAL'                   , 206, ( 'OK, partial response' ) ),
	// Status( 'SUCCESS_SHUTDOWN'                  , 250, ( 'OK, operation successful ask for shutdown of connection' ) ),
	// 
	// Status( 'CLIENT_ERR_NONFATAL'               , 301, ( 'A non-fatal error has occured processing may continue' ) ),
	// 
	// Status( 'BAD_REQUEST'                       , 400, ( 'Bad request' ) ),
	// Status( 'BAD_REQUEST_UNAUTH'                , 401, ( 'Unauthorized' ) ),
	// Status( 'BAD_REQUEST_FORBIDDEN'             , 403, ( 'Forbidden' ) ),
	// Status( 'BAD_REQUEST_NOT_FOUND'             , 404, ( 'Not found' ) ),
	// Status( 'BAD_REQUEST_NOT_ALLOWED'           , 405, ( 'Command not allowed' ) ),
	// Status( 'BAD_REQUEST_INVALID_ARGS'          , 406, ( 'Invalid command arguments' ) ),
	// Status( 'BAD_REQUEST_INVALID_OPTS'          , 407, ( 'Invalid or missing command options' ) ),
	// Status( 'BAD_REQUEST_AUTH_FAILED'           , 411, ( 'The authentication has failed' ) ),
	// Status( 'BAD_REQUEST_ACCOUNT_EXPIRED'       , 412, ( 'The account is expired and can not be used anymore' ) ),
	// Status( 'BAD_REQUEST_ACCOUNT_DISABLED'      , 413, ( 'The account as been disabled' ) ),
	// Status( 'BAD_REQUEST_UNAVAILABLE_LOCALE'    , 414, ( 'Specified locale is not available' ) ),
	//
	// Status( 'SERVER_ERR'                        , 500, ( 'Internal error' ) ),
	// Status( 'SERVER_ERR_MODULE_DIED'            , 510, ( 'Module process died unexpectedly' ) ),
	// Status( 'SERVER_ERR_MODULE_FAILED'          , 511, ( 'Connection to module process failed' ) ),
	// Status( 'SERVER_ERR_CERT_NOT_TRUSTWORTHY'   , 512, ( 'SSL server certificate is not trustworthy' ) ),
	//
	// Status( 'UMCP_ERR_UNPARSABLE_HEADER'        , 551, ( 'Unparsable message header' ) ),
	// Status( 'UMCP_ERR_UNKNOWN_COMMAND'          , 552, ( 'Unknown command' ) ),
	// Status( 'UMCP_ERR_INVALID_NUM_ARGS'         , 553, ( 'Invalid number of arguments' ) ),
	// Status( 'UMCP_ERR_UNPARSABLE_BODY'          , 554, ( 'Unparsable message body' ) ),
	//
	// Status( 'MODULE_ERR'                        , 600, ( 'Error occuried during command processing' ) ),
	// Status( 'MODULE_ERR_COMMAND_FAILED'         , 601, ( 'The execution of a command caused an fatal error' ) )

	_statusMessages: {
		400: umc.tools._( 'Could not fulfill the request.' ),
		401: umc.tools._( 'Your session has expired, please login again.' ), // error occurrs only when user is not authenticated and a request is sent
		403: umc.tools._( 'You are not authorized to perform this action.' ),
		
		404: umc.tools._( 'Webfrontend error: The specified request is unknown.' ),
		405: umc.tools._( 'Webfrontend error: The specified request is not allowed.' ), // difference to 403 not clear?
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
		552: umc.tools._( 'Internal UMC protocol error: The UMCP command is not known.' ), // difference to 404 not clear?
		553: umc.tools._( 'Internal UMC protocol error: The specified number of arguments for the UMCP command is not valid.' ), // difference to 406 not clear?
		554: umc.tools._( 'Internal UMC protocol error: The UMCP message body could not be parsed.' ),

		600: umc.tools._( 'Internal module error: An error occured during command processing.' ),
		601: umc.tools._( 'Internal module error: The execution of a command caused an fatal error.' )
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
				umc.app.alert(this._statusMessages[status] + (errorMsg ? this._('<br>Error message from server: %s', errorMsg) : ''));
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

	forIn: function(/*Object*/ obj, /*Function*/callback, /*Object?*/scope) {
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
			if (obj.hasOwnProperty(i)) {
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
		dojo['require']('umc.widgets.' + widgetConf.type);

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
			dojo.connect(button, 'onClick', buttonConf.callback);
		}

		// done, return the button
		return button; // umc.widgets.Button
	},
	
	renderLayout: function(/*String[][]*/ layout, /*Object*/ widgets, /*Object?*/ buttons, /*Object?*/ tableContainerCfg) {
		// summary:
		//		Render a widget containing a set of widgets as specified by the layout.
		//		The optional parameter cols specifies the number of columns.

		// create a layout manager (TableContainer)
		var cfg = dojo.mixin({
			cols: 2,
			showLabels: true,
			orientation: 'vert'
		}, tableContainerCfg || {});
		var container = new dojox.layout.TableContainer(cfg);

		// check whether the parameters are correct
		umc.tools.assert(dojo.isArray(layout) &&
				layout.length &&
				dojo.isArray(layout[0]),
				'Invalid layout configuration object!');

		// iterate through the layout elements and the widgets at the correct position
		for (var irow = 0; irow < layout.length; ++irow) {
			for (var icol = 0; icol < cfg.cols; ++icol) {
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


