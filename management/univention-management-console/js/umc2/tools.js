/*global console MyError dojo dojox dijit umc2 */

dojo.provide("umc2.tools");

dojo.mixin(umc2.tools, {
	xhrPostJSON: function(/*Object*/ dataObj, /*String*/ url, /*function*/ xhrHandler, /*Boolean [optional]*/ handleErrors) {
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
					umc2.tools.xhrHandleErrors(dataOrError, ioargs);
				}

				// call custom callback
				xhrHandler(dataOrError, ioargs);
			}
		};

		// send off the data
		var xhrs = dojo.xhrPost(xhrArgs);
	},

	xhrHandleErrors: function(dataOrError, ioargs) {
		if (ioargs && 'xhr' in ioargs) {
			// handle the different status codes
			switch (ioargs.xhr.status) {
				case 200: // evertything is ok :)
					return;
				case 401:
					umc2.app.loginDialog.show();
					if (umc2.app.loggingIn) {
						umc2.app.alert('Wrong credentials, please try again!');
					}
					else {
						umc2.app.loggingIn = true;
						umc2.app.alert('Your session has expired, please log in again!');
					}
					return;
				case 403:
					umc2.app.alert('You are not authorized to perform this action!');
					return;
				case 503:
					umc2.app.alert('This service is temporarily not available (staus: 503)!');
					return;
				default:
					umc2.app.alert('An unexpected HTTP-error occurred (status: ' + ioargs.xhr.status + ')');
					return;
			}
		}
		
		// probably server timeout, could also be a different error
		umc2.app.alert('An error occurred while connecting to the server, please try again later.');
	}
});

