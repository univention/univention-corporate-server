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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.dialog");

dojo.require("dojo.cookie");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.LoginDialog");
dojo.require("umc.widgets.Toaster");
dojo.require("umc.widgets.ConfirmDialog");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.Button");

dojo.mixin(umc.dialog, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}), {

	_loginDialog: null, // internal reference to the login dialog

	_loginDeferred: null,

	login: function() {
		// summary:
		//		Show the login screen.
		// returns:
		//		A dojo.Deferred object that is called upon successful login.
		//		The callback receives the authorized username as parameter.

		if (this._loginDeferred) {
			// a login attempt is currently running
			return this._loginDeferred;
		}

		// if username and password are specified via the query string, try to authenticate directly
		this._loginDeferred = null;
		var username = umc.tools.status('username');
		var password = umc.tools.status('password');
		if (username && password && dojo.isString(username) && dojo.isString(password)) {
			// try to authenticate via long polling... i.e., in case of an error try again until it works
			this._loginDeferred = umc.tools.umcpCommand('auth', {
				username: username,
				password: password
			}, false, undefined, {
				message: this._('So far the authentification failed. Continuing nevertheless.'),
				noLogin: true
			}).then(function() {
				return username;
			});
		}
		else {
			// reject deferred to force login
			this._loginDeferred = new dojo.Deferred();
			this._loginDeferred.reject();
		}

		this._loginDeferred = this._loginDeferred.then(null, dojo.hitch(umc.dialog, function() {
			// auto authentication could not be executed or failed...

			if (!this._loginDialog) {
				// create the login dialog for the first time
				this._loginDialog = new umc.widgets.LoginDialog({});
				this._loginDialog.startup();
			}

			// show dialog
			this._loginDialog.show();
			umc.tools.status('loggingIn', true);

			// connect to the dialog's onLogin event
			var deferred = new dojo.Deferred();
			var signalHandle = dojo.connect(this._loginDialog, 'onLogin', dojo.hitch(umc.dialog, function(username) {
				// disconnect from onLogin handle
				dojo.disconnect(signalHandle);
				umc.tools.status('loggingIn', false);

				// submit the username to the deferred callback
				deferred.callback(username);
			}));
			return deferred;
		}));

		// after login, set the locale and make sure that the username is passed
		// over to the next callback
		this._loginDeferred = this._loginDeferred.then(dojo.hitch(umc.dialog, function(username) {
			// set the locale
			return umc.tools.umcpCommand('set', {
				locale: dojo.locale.replace('-', '_')
			}, false).then(function() {
				// remove the reference to the login deferred object
				umc.dialog._loginDeferred = null;

				// make sure the username is handed over to the next callback
				return username;
			}, function() {
				// error... login again
				return umc.dialog.login();
			});
		}));

		return this._loginDeferred;
	},

	loginOpened: function() {
		// summary:
		//		Returns whether the login dialog has been opened or not

		return this._loginDialog && this._loginDialog.open; // Boolean
	},

	_toaster: null, // internal reference to the toaster

	notify: function(/*String*/ message) {
		// summary:
		//		Show a toaster notification with the given message string.
		// message:
		//		The message that is displayed in the notification.

		// create toaster the first time
		if (!this._toaster) {
			this._toaster = new umc.widgets.Toaster({});
		}

		// show the toaster
		this._toaster.setContent(message, 'message');
	},

	_alertDialog: null, // internal reference for the alert dialog

	alert: function(/*String*/ message, /* String? */ title, /* String? */ buttonLabel) {
		// summary:
		//		Popup an alert dialog with the given message string. The users needs to
		//		confirm the dialog by clicking on the 'OK' button.
		// message:
		//		The message that is displayed in the dialog.
		// title:
		//		An optional title for the popup window
		// buttonLabel:
		//		An alternative label for the button

		// create alert dialog the first time
		if (!this._alertDialog) {
			this._alertDialog = new umc.widgets.ConfirmDialog({
				title: title || this._('Notification'),
				style: 'max-width: 650px;',
				options: [{
					label: buttonLabel || this._('Ok'),
					callback: dojo.hitch(this, function() {
						// hide dialog upon confirmation by click on 'OK'
						this._alertDialog.hide();
					}),
					'default': true
				}]
			});
		}

		// show the confirmation dialog
		this._alertDialog.set('message', message);
		//this._alertDialog.startup();
		this._alertDialog.show();
	},
	
	centerAlertDialog: function() {
		this._alertDialog._relativePosition = null;
		this._alertDialog._position();
	},

	confirm: function(/*String|_Widget*/ message, /*Object[]*/ options) {
		// summary:
		//		Popup a confirmation dialog with a given message string and a
		//		list of options to choose from.
		// description:
		//		This function provides a shortcut for umc.widgets.ConfirmDialog.
		//		The user needs to confirm the dialog by clicking on one of
		//		multiple defined buttons (=choice). When any of the buttons
		//		is pressed, the dialog is automatically closed.
		//		The function returns a dojo.Deferred object. Registered callback
		//		methods are called with the corresponding choice name as parameter.
		// message:
		//		The message that is displayed in the dialog, can also be a _Widget.
		// options:
		//		Array of objects describing the possible choices. Array is passed to
		//		umc.widgets.ConfirmDialog as 'options' parameter. The property 'label' needs
		//		to be specified. The properties 'callback', 'name', 'auto', and 'default' are
		//		optional.
		//		The property 'default' renders the button for the default choice in the style
		//		of a submit button.
		//		If one single (!) item is specified with the property 'auto=true' and
		//		confirmations are switched off in the user preferences, the dialog is not shown
		//		and the callback function for this default option is executed directly.
		//
		// example:
		//		A simple example that uses the 'default' property.
		// |	umc.dialog.confirm(msg, [{
		// |	    label: Delete',
		// |	    callback: function() {
		// |			// do something...
		// |		}
		// |	}, {
		// |	    label: 'Cancel',
		// |	    'default': true
		// |	}]);
		// example:
		//		We may also refer the callback to a method of an object, i.e.:
		// |	var myObj = {
		// |		foo: function(answer) {
		// |			if ('delete' == answer) {
		// |				console.log('Item will be deleted!');
		// |			}
		// |		}
		// |	};
		// |	umc.dialog.confirm('Do you want to delete the item?', [{
		// |	    label: 'Delete item',
		// |		name: 'delete',
		// |	    'default': true,
		// |	    callback: dojo.hitch(myObj, 'foo')
		// |	}, {
		// |	    label: 'Cancel',
		// |		name: 'cancel',
		// |	    callback: dojo.hitch(myObj, 'foo')
		// |	}]);

		// if the user has switched off confirmations, try to find a default option
		if (umc.tools.preferences('confirm') === false) {
			var cb = undefined;
			var response = undefined;
			dojo.forEach(options, function(i, idx) {
				// check for default option
				if (true === i.auto) {
					cb = i.callback;
					response = i.name || idx;
					return false; // break loop
				}
			});
			if (cb && dojo.isFunction(cb)) {
				// we found a default item .. call the callback and exit
				cb(response);
				return;
			}
		}

		// create confirmation dialog
		var confirmDialog = new umc.widgets.ConfirmDialog({
			title: this._('Confirmation'),
			style: 'max-width: 550px;',
			message: message,
			options: options
		});

		// connect to 'onConfirm' event to close the dialog in any case
		var deferred = new dojo.Deferred();
		dojo.connect(confirmDialog, 'onConfirm', function(response) {
			confirmDialog.close();
			deferred.resolve(response);
		});

		// show the confirmation dialog
		confirmDialog.show();

		return deferred;
	},

	templateDialog: function( /*String*/ templateModule, /*String*/ templateFile, /*String*/ keys, /* String? */ title, /* String? */ buttonLabel ) {
		// summary:
		//		Popup an alert dialog with a text message based on the given template file. The users needs to
		//		confirm the dialog by clicking on the 'OK' button.
		// templateModule:
		//		The module name where to find the template
		// templateFile:
		//		The template file to use
		// keys:
		//		An object with values that should be replaced in the template (using dojo.replace)
		// title:
		//		An optional title for the popup window
		// buttonLabel:
		//		An alternative label for the button
		var message = dojo.cache( templateModule, templateFile );
		message = dojo.replace( message, keys );
		var widget = new umc.widgets.Text( {  content : message } );
		dojo.addClass( widget.domNode, 'umcPopup' );
		this.alert( widget, title || 'UMC', buttonLabel );
	}
});

