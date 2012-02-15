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
/*global console MyError dojo dojox dijit umc setTimeout */

dojo.provide("umc.tools");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("dijit.Dialog");
dojo.require("dojox.timing");
dojo.require("dojox.html.styles");

dojo.mixin(umc.tools, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}));
dojo.mixin(umc.tools, {

	// default value for the session timeout
	// it will be replaced by the ucr variable 'umc/http/session/timeout' onLogin
	_sessionTimeout: 300,

	_status: {
		username: null,
		hostname: '',
		domainname: '',
		overview: true,
		displayUsername: true,
		width: null,
		setupGui: false,
		loggingIn: false
	},

	status: function(/*String?*/ key, /*Mixed?*/ value) {
		// summary:
		//		Sets/gets status information. With no parameters given,
		//		returns a dict with status information (username, domainname,
		//		hostname, isSetUpGUI, ...). 
		//		With one parameter given, returns the value of the specified key.
		//		With two parameters, sets the value of the specified key.
		//		Also contains the properties given
		//		to `umc.app.start()`. The following properties exist:
		//		* username (String): The username of the authenticated user.
		//		* hostname (String): The hostname on which the UMC is running.
		//		* domainname (String): The domainname on which the UMC is running.
		//		* overview (Boolean): Specifies whether or not the overview is visible.
		//		* displayUsername (Boolean): Specifies whether the username is displayed or not.
		//		* width (Integer): Forces a width for the frontend.
		// key: String?
		//		If given, only the value for the specified property is returned.

		if (undefined === key) {
			// return the whole dictionary
			return this._status;
		}
		if (dojo.isString(key)) {
			if (undefined === value) {
				// return the specified key
				return this._status[key];
			}
			// set the value
			this._status[key] = value;
		}
		return undefined;
	},

	closeSession: function() {
		// summary:
		//		Reset the session cookie in order to close the session from the client side.
		dojo.cookie('UMCSessionId', null, {
			expires: -1,
			path: '/'
		});
	},

	holdSession: function() {
		// summary:
		//		Set the expiration time of the current session cookie in to 24 hours.
		var date = new Date((new Date()).getTime() + 1000 * 60 * 60 * 24);
		dojo.cookie('UMCSessionId', dojo.cookie('UMCSessionId'), {
			expires: date.toUTCString(),
			path: '/'
		});
	},

	_renewIESession : function() {
		// summary:
		//		Reset the Internet Explorer Session. Internet Explorer can not handle max-age cookies.
		//		This is required for automatically show the login dialogue when the session is expired.
		if(dojo.isIE !== undefined) {
			var date = new Date((new Date()).getTime() + 1000 * this._sessionTimeout);
			dojo.cookie('UMCSessionId', dojo.cookie('UMCSessionId'), {
				expires: date.toUTCString(),
				path: '/'
			});
		}
	},

	_checkSessionTimer: null,

	checkSession: function(enable) {
		// summary:
		//		Create a background process that checks each second the validity of the session
		//		cookie. As soon as the session is invalid, the login screen will be shown.
		if (enable === false) {
			// stop session checking
			if (this._checkSessionTimer && this._checkSessionTimer.isRunning) {
				this._checkSessionTimer.stop();
			}
			return;
		}

		if (!this._checkSessionTimer) {
			// create a new timer instance
			this._checkSessionTimer = new dojox.timing.Timer(1000);
			this._checkSessionTimer.onTick = function() {
				if (!dojo.isString(dojo.cookie('UMCSessionId'))) {
					umc.tools._checkSessionTimer.stop();
					if (umc.tools.status['loggingIn']) {
						// login dialog is already running
						return;
					}

					// try to login
					umc.dialog.login().then(function() {
						if (!umc.tools._checkSessionTimer.isRunning) {
							umc.tools._checkSessionTimer.start();
						}
					});
				}
			};
		}

		// start session checking
		if (!this._checkSessionTimer.isRunning) {
			this._checkSessionTimer.start();
		}
	},

	// handler class for long polling scenario
	_PollingHandler: function(url, content, finishedDeferred, opts) {
		return {
			finishedDeferred: finishedDeferred,

			// url to which 
			url: url,

			// JSON data that is being sent
			content: content,

			// in seconds, timeout that will be passed over to the XHR post command
			xhrTimeout: dojo.getObject('xhrTimeout', false, opts) || 300,

			// in seconds, will be multiplied with the number of retries
			timeoutRetry: dojo.getObject('timeoutRetry', false, opts) || 2,

			// in seconds, maximal time interval to wait between reestablishing a connection
			maxTimeoutRetry: dojo.getObject('maxTimeoutRetry', false, opts) || 30,

			// in seconds, specifies the time interval in which a request is considered
			// to have failed
			failureInterval: dojo.getObject('failureInterval', false, opts) || 10,

			// number of seconds after which an information ist displayed to the user
			// in case the connection could not be established; if negative, no message
			// will be shown.
			messageInterval: dojo.getObject('messageInterval', false, opts) || 120,

			// message that is displayed to the user in case the 
			message: dojo.getObject('message', false, opts) || umc.tools._('So far, the connection to the server could not be established after {time} seconds. This can be a normal behavior. In any case, the process will continue to establish the connection.'),

			// set to true, the _PollingHandler will not try a login
			noLogin: false,

			_startTime: (new Date()).getTime(),

			_lastRequestTime: 0,

			_firstErrorTime: 0,

			_nErrors: 0,

			// information dialog to display to the user
			_dialog: new dijit.Dialog({
				title: umc.tools._('Information'),
				style: 'max-width: 400px'
			}),

			sendRequest: function() {
				// switch off the automatic check for session timeout...
				// the proble here is as follows, we do not receive a response,
				// therefore the cookie is not updated (which is checked for the
				// session timeout), however, the server will renew the session
				// with each valid request that it receives
				umc.tools.holdSession();

				// send AJAX command
				this._lastRequestTime = (new Date()).getTime();
				dojo.xhrPost({
					url: this.url,
					preventCache: true,
					handleAs: 'json',
					headers: {
						'Content-Type': 'application/json'
					},
					postData: this.content,
					timeout: 1000 * this.xhrTimeout
				}).then(dojo.hitch(this, function(data) {
					// request finished
					umc.tools._renewIESession();
					this._dialog.hide();
					this._dialog.destroyRecursive();
					this.finishedDeferred.resolve(data);
				}), dojo.hitch(this, function(error) {
					var result = umc.tools.parseError(error);

					if (!this.noLogin) {
						// handle login cases
						if (401 == result.status) {
							// command was rejected, user is not authorized... continue to poll after successful login
							umc.dialog.login().then(dojo.hitch(this, 'sendRequest'));
							return;
						}
						if (411 == result.status) {
							// login failed... continue to poll after successful login
							umc.dialog.login().then(dojo.hitch(this, 'sendRequest'));
							umc.dialog.notify(umc.tools._statusMessages[result.status]);
							return;
						}
					}

					// error case
					var elapsedTime = ((new Date()).getTime() - this._lastRequestTime) / 1000.0;
					if (elapsedTime < this.failureInterval) {
						// the server could not been reached within a short time interval 
						// -> that is an error
						++this._nErrors;
						if (this._nErrors == 1) {
							// log the error time
							this._firstErrorTime = (new Date()).getTime();
						}
						var elapsedErrorTime = ((new Date()).getTime() - this._firstErrorTime) / 1000.0;
						if (this.messageInterval > 0 && elapsedErrorTime > this.messageInterval && !this._dialog.get('open')) {
							// show message to user
							this._dialog.set('content', dojo.replace(this.message, { time: Math.round(elapsedErrorTime) }));
							this._dialog.show();
						}
					}
					else {
						// probably the request got a timeout
						this._nErrors = 0;
						this._firstErrorTime = 0;
					}

					// try again
					setTimeout(dojo.hitch(this, 'sendRequest'), 1000 * Math.min(this.timeoutRetry * this._nErrors, this.maxTimeoutRetry));
				}));
			}
		};
	},

	umcpCommand: function(
		/*String*/ commandStr,
		/*Object?*/ dataObj,
		/*Boolean?*/ handleErrors,
		/*String?*/ flavor,
		/*Object?*/ longPollingOptions) {

		// summary:
		//		Encapsulates an AJAX call for a given UMCP command.
		// returns:
		//		A deferred object.

		// when logging in, ignore all except the AUTH command
		if (umc.tools.status('loggingIn') && !(/^auth$/i).test(commandStr)) {
			console.log(umc.tools._('WARNING: Ignoring command "%s" since user is logging in', commandStr));
			var deferred = new dojo.Deferred();
			deferred.reject();
			return deferred;
		}

		// set default values for parameters
		dataObj = dataObj || {};
		handleErrors = undefined === handleErrors || handleErrors;
		// build the URL for the UMCP command
		var url = '/umcp/command/' + commandStr;
		if ((/^(get\/|set$|auth)/i).test(commandStr)) {
			// special case for 'get' and 'auth' commands .. here we do not need to add 'command'
			url = '/umcp/' + commandStr;
		}

		// build message body
		var _body = {
			 options: dataObj
		};
		if (dojo.isString(flavor)) {
			_body.flavor = flavor;
		}
		var body = dojo.toJson(_body);

		if (longPollingOptions) {
			// long polling AJAX call

			// new handler
			var finishedDeferred = new dojo.Deferred();
			var handler = new umc.tools._PollingHandler(url, body, finishedDeferred, longPollingOptions);
			handler.sendRequest();

			return finishedDeferred; // dojo.Deferred
		}
		else {
			// normal AJAX call
			var call = dojo.xhrPost({
				url: url,
				preventCache: true,
				handleAs: 'json',
				headers: {
					'Content-Type': 'application/json'
				},
				postData: body
			});

			call = call.then(function(data) {
				umc.tools._renewIESession();
				return data;
			});

			// handle XHR errors unless not specified otherwise
			if (handleErrors) {
				call = call.then(function(data) {
					// do not modify the data
					if ( data && data.message ) {
						if ( parseInt(data.status, 10) == 200 ) {
							umc.dialog.notify( data.message );
						} else {
							umc.dialog.alert( data.message );
						}
					}

					return data; // Object
				}, function(error) {
					// handle errors
					umc.tools.handleErrorStatus(error);

					// propagate the error
					throw error; // Error
				});
			}

			// return the Deferred object
			return call; // Deferred
		}
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
		503: umc.tools._( 'Internal server error: The service is temporarily not available.' ),
		510: umc.tools._( 'Internal server error: The module process died unexpectedly.' ),
		511: umc.tools._( 'Internal server error: Could not connect to the module process.' ),
		512: umc.tools._( 'Internal server error: The SSL server certificate is not trustworthy. Please check your SSL configurations.' ),

		551: umc.tools._( 'Internal UMC protocol error: The UMCP message header could not be parsed.' ),
		554: umc.tools._( 'Internal UMC protocol error: The UMCP message body could not be parsed.' ),

		590: umc.tools._( 'Internal module error: An error occured during command processing.' ),
		591: umc.tools._( 'Could not process the request.' )
	},

	parseError: function(error) {
		var status = dojo.getObject('status', false, error);
		var message = '';
		try {
			var jsonResponse = dojo.getObject('responseText', false, error) || '{}';
			// replace all newlines with '<br>' because strings in json must not have line breaks
			jsonResponse = jsonResponse.replace(/\n/g, '<br>');
			var response = dojo.fromJson(jsonResponse);
			status = parseInt(dojo.getObject('status', false, response) || error.status, 10) || status;
			message = dojo.getObject('message', false, response) || '';
		}
		catch (_err) { }

		return {
			status: status,
			message: message
		};
	},

	handleErrorStatus: function(error) {
		// parse the error
		var result = this.parseError(error);
		var status = result.status;
		var message = result.message;

		// handle the different status codes
		if (undefined !== status && status in this._statusMessages) {
			if (411 == status) {
				// authentification failed, show a notification
				umc.dialog.login();
				var logindialog = dojo.query('.umc_LoginMessage');
				logindialog[0].innerHTML = this._statusMessages[status];
				logindialog.style('display', 'block');
			} else if(401 == status) {
				// session has expired
				umc.dialog.login();
				umc.dialog.notify(this._statusMessages[status]);
			}
			/*else if (591 == status) {
				// the command could not be executed, e.g., since the user data was not correct
				// this error deserves a special treatment as it is not critical, but rather a
				// a user error
				umc.dialog.alert('<p>' + this._statusMessages[status] + (message ? ': ' + message : '.') + '</p>');
			}*/
			// handle Tracebacks
			else if(message.match(/Traceback.*most recent call.*File.*line/) || (message.match(/File.*line.*in/) && status >= 500)) {

				var feedbackLink = this._('Please take a second to provide the following information:');
				feedbackLink += "\n\n1) " + this._('steps to reproduce the failure');
				feedbackLink += "\n2) " + this._('expected result');
				feedbackLink += "\n3) " + this._('actual result');
				feedbackLink += "\n\n----------\n\n";
				feedbackLink += message.replace(/<br>/g, "\n");
				feedbackLink += "\n\n----------\n\n";
				feedbackLink += "univention-management-console-frontend " + dojo.version;
				feedbackLink = '<a href="mailto:feedback@univention.de?body=' + encodeURI( feedbackLink ) + '&amp;subject=[UMC-Feedback]%20Traceback">' + this._('Send feedback mail to Univention') + '</a>';

				var content = '<pre>' + message + '</pre><br>' + feedbackLink;
				var hideLink = '<a>' + this._('Hide server error message') + '</a>';
				var showLink = '<a>' + this._('Show server error message') + '</a>';

				var titlePane = dijit.TitlePane({
					title: showLink,
					content: content,
					'class': 'umcTracebackPane',
					open: false,
					onHide: function() { titlePane.set('title', showLink); },
					onShow: function() { titlePane.set('title', hideLink); }
				});

				var container = new umc.widgets.ContainerWidget({});
				container.addChild(new umc.widgets.Text({
					content: '<p>' + this._statusMessages[status] + '</p>'
				}));
				container.addChild(titlePane);

				container.connect(titlePane._wipeIn, 'onEnd', function() { umc.dialog.centerAlertDialog(); } );
				container.connect(titlePane._wipeOut, 'onEnd', function() { umc.dialog.centerAlertDialog(); } );

				umc.dialog.alert( container );
			}
			else {
				// all other cases
				umc.dialog.alert('<p>' + this._statusMessages[status] + '</p>' + (message ? '<p>' + this._('Server error message:') + '</p><p class="umcServerErrorMessage">' + message + '</p>' : ''));
			}
		}
		else if (undefined !== status) {
			// unknown status code .. should not happen
			umc.dialog.alert(this._('An unknown error with status code %s occurred while connecting to the server, please try again later.', status));
		}
		else {
			// probably server timeout, could also be a different error
			umc.dialog.alert(this._('An error occurred while connecting to the server, please try again later.'));
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
		// 		Returning false from within the callback function will break the loop
		//
		//		This method is similar to dojox.lang.functional.forIn wher no hasOwnProperty()
		//		check is carried out.

		scope = scope || dojo.global;
		for (var i in obj) {
			if (obj.hasOwnProperty(i) || inheritedProperties) {
				if ( false === callback.call(scope, i, obj[i], obj ) ) {
					break;
				}
			}
		}
	},

	mapWalk: function(/*Array*/ array, /*Function*/ callback, /*Object?*/ scope) {
		// summary:
		//		Equivalent to dojo.map(), however this function is intended to be used
		//		with multi-dimensional arrays.

		// make sure we have an array
		if (!dojo.isArray(array)) {
			return callback.call(scope, array);
		}

		// clone array and walk through it
		scope = scope || dojo.global;
		var res = dojo.clone(array);
		var stack = [ res ];
		while (stack.length) {
			// new array, go through its elements
			var iarray = stack.pop();
			dojo.forEach(iarray, function(iobj, i) {
				if (dojo.isArray(iobj)) {
					// put arrays on the stack
					stack.push(iobj);
				}
				else {
					// map object
					iarray[i] = callback.call(scope, iobj);
				}
			});
		}

		// return the final array
		return res;
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
				ignCase: true
			};

			// entry for ordering can by a String or an Object
			if (dojo.isString(args[i])) {
				o.attr = args[i];
			}
			else if (dojo.isObject(args[i]) && 'attribute' in args[i]) {
				o.attr = args[i].attribute;
				o.desc = (args[i].descending ? -1 : 1);
				o.ignCase = undefined === args[i].ignoreCase ? true : args[i].ignoreCase;
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
				if (o.ignCase && a.toLowerCase && b.toLowerCase) {
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
	},

	isEqual: /* Boolean */ function(/* mixed */a, /* mixed */b) {
		// summary:
		//		recursive compare two objects(?) and return true if they are equal
		if (a === b) {
			return true;
		}
		if(typeof a !== typeof b) { return false; }

		// check whether we have arrays
		if (dojo.isArray(a) && dojo.isArray(b)) {
			if (a.length !== b.length) {
				return false;
			}
			for (var i = 0; i < a.length; ++i) {
				if (!umc.tools.isEqual(a[i], b[i])) {
					return false;
				}
			}
			return true;
		}
		if (dojo.isObject(a) && dojo.isObject(b) && !(a === null || b === null)) {
			var allKeys = dojo.mixin({}, a, b);
			var result = true;
			umc.tools.forIn(allKeys, function(key) {
					result &= umc.tools.isEqual(a[key], b[key]);
					return result;
			});
			return result;
		}
		return a === b;
	},

	_existingIconClasses: {},

	getIconClass: function(iconName, size) {
		// check whether the css rule for the given icon has already been added
		size = size || 16;
		var values = {
			s: size,
			icon: iconName
		};
		var iconClass = dojo.replace('icon{s}-{icon}', values);
		if (!(iconClass in this._existingIconClasses)) {
			try {
				// add dynamic style sheet information for the given icon
				var css = dojo.replace(
					'background: no-repeat;' +
					'width: {s}px; height: {s}px;' +
					'background-image: url("images/icons/{s}x{s}/{icon}.png");',
					values);
				dojox.html.insertCssRule('.' + iconClass, css);

				// remember that we have already added a rule for the icon
				this._existingIconClasses[iconClass] = true;
			}
			catch (error) {
				console.log(dojo.replace("ERROR: Could not create CSS information for the icon name '{icon}' of size {s}", values));
			}
		}
		return iconClass;
	},

	delegateCall: function(/*Object*/ self, /*Arguments*/ args, /*Object*/ that) {
		// summary:
		//		Delegates a method call into the scope of a different object.
		var m = self.getInherited(args);
		m.apply(that, args);
	},

	_userPreferences: null, // internal reference to the user preferences

	// internal array with default values for all preferences
	_defaultPreferences: {
		tooltips: true,
		moduleHelpText: true
		//confirm: true
	},

	preferences: function(/*String|Object?*/ param1, /*AnyType?*/ value) {
		// summary:
		//		Convenience function to set/get user preferences.
		//		All preferences will be store in a cookie (in JSON format).
		// returns:
		//		If no parameter is given, returns dictionary with all preference
		//		entries. If one parameter of type String is given, returns the
		//		preference for the specified key. If one parameter is given which
		//		is an dictionary, will set all key-value pairs as specified by
		//		the dictionary. If two parameters are given and
		//		the first is a String, the function will set preference for the
		//		key (paramater 1) to the value as specified by parameter 2.

		// make sure the user preferences are cached internally
		var cookieStr = '';
		if (!this._userPreferences) {
			// not yet cached .. get all preferences via cookies
			this._userPreferences = dojo.clone(this._defaultPreferences);
			cookieStr = dojo.cookie('UMCPreferences') || '{}';
			dojo.mixin(this._userPreferences, dojo.fromJson(cookieStr));
		}

		// no arguments, return full preference object
		if (0 === arguments.length) {
			return this._userPreferences; // Object
		}
		// only one parameter, type: String -> return specified preference
		if (1 == arguments.length && dojo.isString(param1)) {
			if (param1 in this._defaultPreferences) {
				return this._userPreferences[param1]; // Boolean|String|Integer
			}
			return undefined;
		}

		// backup the old preferences
		var oldPrefs = dojo.clone(this._userPreferences);

		// only one parameter, type: Object -> set all parameters as specified in the object
		if (1 == arguments.length) {
			// only consider keys that are defined in defaultPreferences
			umc.tools.forIn(this._defaultPreferences, dojo.hitch(this, function(key, val) {
				if (key in param1) {
					this._userPreferences[key] = param1[key];
				}
			}));
		}
		// two parameters, type parameter1: String -> set specified user preference
		else if (2 == arguments.length && dojo.isString(param1)) {
			// make sure preference is in defaultPreferences
			if (param1 in this._defaultPreferences) {
				this._userPreferences[param1] = value;
			}
		}
		// otherwise throw error due to incorrect parameters
		else {
			umc.tools.assert(false, 'umc.tools.preferences(): Incorrect parameters: ' + arguments);
		}

		// publish changes in user preferences
		umc.tools.forIn(this._userPreferences, function(key, val) {
			if (val != oldPrefs[key]) {
				// entry has changed
				dojo.publish('/umc/preferences/' + key, [val]);
			}
		});

		// set the cookie with all preferences
		cookieStr = dojo.toJson(this._userPreferences);
		dojo.cookie('UMCPreferences', cookieStr, { expires: 100, path: '/' } );
		return; // undefined
	},

	ucr: function(/*String|String[]*/ query) {
		// summary:
		//		Function that fetches with the given query the UCR variables.
		// query: String|String[]
		//		Query string (or array of query strings) that is matched on the UCR variable names.
		// return: dojo.Deferred
		//		Returns a dojo.Deferred that expects a callback to which is passed
		//		a dict of variable name -> value entries.

		return this.umcpCommand('get/ucr', dojo.isArray( query ) ? query : [ query ] ).then(function(data) {
			return data.result;
		});
	},

	isFalse: function(/*mixed*/ input) {
		if (dojo.isString(input)) {
			switch (input.toLowerCase()) {
				case 'no':
				case 'false':
				case '0':
				case 'disable':
				case 'disabled':
				case 'off':
					return true;
			}
		}
		if (false === input || 0 === input || null === input || undefined === input || '' === input) {
			return true;
		}
		return false;
	},

	isTrue: function(/*mixed*/ input) {
		//('yes', 'true', '1', 'enable', 'enabled', 'on')
		return !this.isFalse(input);
	},

	explodeDn: function(dn, noTypes) {
		// summary:
		//		Splits the parts of an LDAP DN into an array.
		// dn: String
		//		LDAP DN as String.
		// noTypes: Boolean?
		//		If set to true, the type part ('.*=') of each LDAP DN part will be removed.

		var res = [];
		if (dojo.isString(dn)) {
			res = dn.split(',');
		}
		if (noTypes) {
			res = dojo.map(res, function(x) {
				return x.slice(x.indexOf('=')+1);
			});
		}
		return res;
	},

	ldapDn2Path: function( dn, base ) {
		var base_list = this.explodeDn( base, true );
		var path = '';

		dn = dn.slice( 0, - ( base.length + 1 ) );
		var dn_list = this.explodeDn( dn, true ).slice( 1 );

		// format base
		path = base_list.reverse().join( '.' ) + ':/';
		if ( dn_list.length ) {
			path += dn_list.reverse().join( '/' );
		}

		return path;
	},

	inheritsFrom: function(/*Object*/ _o, /*String*/ c) {
		// summary:
		//		Returns true in case object _o inherits from class c.
		var o = _o;
		var bases = dojo.getObject('_meta.bases', false, _o.constructor);
		if (!bases) {
			// no dojo object
			return false;
		}

		var matched = false;
		dojo.forEach(bases, function(ibase) {
			if (ibase.prototype.declaredClass == c) {
				matched = true;
				return false;
			}
		});
		return matched;
	},

	capitalize: function(/*String*/ str) {
		// summary:
		//		Return a string with the first letter in upper case.
		if (!dojo.isString(str)) {
			return str;
		}
		return str.slice(0, 1).toUpperCase() + str.slice(1);
	},

	stringOrArray: function(/*String|String[]*/ input) {
		// summary:
		//		Transforms a string to an array containing the string as element
		//		and if input is an array, the array is not modified. In any other
		//		case, the function returns an empty array.

		if (dojo.isString(input)) {
			return [ input ];
		}
		if (dojo.isArray(input)) {
			return input;
		}
		return [];
	},

	stringOrFunction: function(/*String|Function*/ input, /*Function?*/ umcpCommand) {
		// summary:
		//		Transforms a string starting with 'javascript:' to a javascript
		//		function, otherwise to an UMCP command function (if umcpCommand)
		//		is specified, and leaves a function a function.
		//		Anything else will be converted to a dummy function.

		if (dojo.isFunction(input)) {
			return input;
		}
		if (dojo.isString(input)) {
			if (0 === input.indexOf('javascript:')) {
				// string starts with 'javascript:' to indicate a reference to a javascript function
				try {
					// evaluate string as javascript code and execute function
					return eval(input.substr(11));
				}
				catch (err) {
					// will return dummy function at the end...
				}
			}
			else if (umcpCommand) {
				// we have a reference to an ucmpCommand, we can try to execute the string as an
				// UMCP command... return function that is ready to query dynamic values via UMCP
				return function(params) {
					return umcpCommand(input, params).then(function(data) {
						// only return the data array
						return data.result;
					});
				};
			}

			// print error message
			console.log('ERROR: The string could not be evaluated as javascript code. Ignoring error: ' + input);
		}

		// return dummy function
		return function() {};
	}
});




