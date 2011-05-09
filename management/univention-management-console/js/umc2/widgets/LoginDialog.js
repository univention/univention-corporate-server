/*global dojo dijit dojox umc2 console window */

dojo.provide("umc2.widgets.LoginDialog");

dojo.require("dijit.form.Button");
dojo.require("dijit.form.TextBox");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojox.layout.TableContainer");
dojo.require("dojox.widget.Dialog");
dojo.require("umc2.tools");
dojo.require("umc2.widgets.StandbyMixin");
dojo.require("umc2.widgets.ContainerForm");
dojo.require("umc2.widgets.ContainerWidget");

dojo.declare('umc2.widgets.LoginDialog', [ dojox.widget.Dialog, umc2.widgets.StandbyMixin ], {
	// our own variables
	_layoutContainer: null,
	_passwordTextBox: null,
	_usernameTextBox: null,
	_form: null,

	postMixInProperties: function() {
		dojo.mixin(this, {
			closable: false,
			modal: true,
			sizeDuration: 900,
			sizeMethod: 'chain',
			sizeToViewport: false,
			dimensions: [300, 180]
		});
	},

	buildRendering: function() {
		// call superclass' postCreate()
		this.inherited(arguments);

		// embed layout container within a form-element
		this._form = new umc2.widgets.ContainerForm({
			onSubmit: dojo.hitch(this, function(evt) {
				// stop the event and call LoginDialog.onSubmit()
				dojo.stopEvent(evt);
				this._authenticate(this._usernameTextBox.get('value'), this._passwordTextBox.get('value'));

				// clear password entry
				this._passwordTextBox.set('value', '');
			})
		}).placeAt(this.containerNode);

		// add some informative Text
		this._form.addChild(new dijit.layout.ContentPane({
			content: 'Willkomen auf der Univention Management Console (v2). Bitte geben Sie Benutzername und Passwort ein!'
		}));

		// first create a table container which contains all widgets
		this._layoutContainer = new dojox.layout.TableContainer({
			cols: 1,
			showLabels: true,
			orientation: 'horiz'
		}).placeAt(this._form);

		// add username input field
		this._usernameTextBox = new dijit.form.TextBox({
			id: this.id + 'UsernameTextBox',
			label: 'Benutzername',
			//style: 'width: 300px',
			value: ''
		});
		this._layoutContainer.addChild(this._usernameTextBox);

		// add password input field
		this._passwordTextBox = new dijit.form.TextBox({
			id: this.id + 'PasswordTextBox',
			label: 'Passwort',
			type: 'password',
			//style: 'width: 300px',
			value: ''
		});
		this._layoutContainer.addChild(this._passwordTextBox);

		// add 'login' button
		var buttonContainer = new umc2.widgets.ContainerWidget();
		buttonContainer.addChild(new dijit.form.Button({
			id: this.id + 'LoginButton',
			label: '<b>Login</b>',
			type: 'submit'
		}));
	
		// add 'clear' button
		buttonContainer.addChild(new dijit.form.Button({
			id: this.id + 'clearButton',
			label: 'Clear',
			onClick: dojo.hitch(this, function(evt) {
				this.reset();
			})
		}));

		// add container for buttons to main layout
		this._layoutContainer.addChild(buttonContainer);

		// call startup to make sure everything is rendered correctly
		this._form.startup();
	},

	postCreate: function() {
		// call superclass' postCreate()
		this.inherited(arguments);

		// hide the close button
		dojo.style(this.closeButtonNode, 'display', 'none');
	},

	reset: function() {
		// description:
		//		Reset all form entries to their initial values.
		this._passwordTextBox.reset();
		this._usernameTextBox.reset();
	},

	_onKey:  function(evt) {
		// ignore ESC key
		if (evt.charOrCode == dojo.keys.ESCAPE) {
			return;
		}

		// otherwise call the standard handler
		this.inherited(arguments);
	},

	_authenticate: function(username, password) {
		this.standby(true);
		umc2.tools.xhrPostJSON(
			{
				username: username,
				password: password
			},
			'/umcp/auth',
			dojo.hitch(this, function(data, ioargs) {
				// disable standby in any case
				this.standby(false);

				// make sure that we got data
				if (200 == dojo.getObject('xhr.status', false, ioargs)) {
					this.onLogin();
				}
			})
		);
	},

	onLogin: function() {
		// event stub
	}
});


