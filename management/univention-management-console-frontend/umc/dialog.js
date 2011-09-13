/*global dojo dijit dojox umc console window */

dojo.provide("umc.dialog");

dojo.require("dojo.cookie");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.LoginDialog");
dojo.require("umc.widgets.Toaster");
dojo.require("umc.widgets.ConfirmDialog");

dojo.mixin(umc.dialog, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
}), {

	_loginDialog: null, // internal reference to the login dialog

	login: function() {
		// summary:
		//		Show the login screen.
		// returns:
		//		A dojo.Deferred object that is called upon successful login.
		//		The callback receives the authorized username as parameter.

		// create the login dialog for the first time
		if (!this._loginDialog) {
			this._loginDialog = new umc.widgets.LoginDialog({});
			this._loginDialog.startup();
		}

		// show dialog
		this._loginDialog.show();
		this.loggingIn = true;

		// connect to the dialog's onLogin event
		var deferred = new dojo.Deferred();
		var signalHandle = dojo.connect(this._loginDialog, 'onLogin', dojo.hitch(this, function(username) {
			// disconnect from onLogin handle
			dojo.disconnect(signalHandle);
			this.loggingIn = false;

			// submit the username to the deferred callback
			deferred.callback(username);
		}));

		return deferred;
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

	alert: function(/*String*/ message) {
		// summary:
		//		Popup an alert dialog with the given message string. The users needs to
		//		confirm the dialog by clicking on the 'OK' button.
		// message:
		//		The message that is displayed in the dialog.

		// create alert dialog the first time
		if (!this._alertDialog) {
			this._alertDialog = new umc.widgets.ConfirmDialog({
				title: this._('Notification'),
				style: 'max-width: 500px;',
				options: [{
					label: this._('Ok'),
					callback: dojo.hitch(this, function() {
						// hide dialog upon confirmation by click on 'OK'
						this._alertDialog.hide();
					})
				}]
			});
		}

		// show the confirmation dialog
		this._alertDialog.set('message', message);
		//this._alertDialog.startup();
		this._alertDialog.show();
	},

	confirm: function(/*String*/ message, /*Object[]*/ options) {
		// summary:
		//		Popup a confirmation dialog with a given message string and a
		//		list of options to choose from.
		// description:
		//		This function provides a shortcut for umc.widgets.ConfirmDialog.
		//		The user needs to confirm the dialog by clicking on one of
		//		multiple defined buttons (=choice). When any of the buttons
		//		is pressed, the dialog is automatically closed.
		// message:
		//		The message that is displayed in the dialog.
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
		if (!umc.tools.preferences('confirm')) {
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
			style: 'max-width: 400px;',
			message: message,
			options: options
		});

		// connect to 'onConfirm' event to close the dialog in any case
		dojo.connect(confirmDialog, 'onConfirm', function(response) {
			confirmDialog.close();
		});

		// show the confirmation dialog
		confirmDialog.show();
	}
});

