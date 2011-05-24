/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.LoginDialog");

dojo.require("dijit.form.Button");
dojo.require("dijit.form.TextBox");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojox.layout.TableContainer");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.tools");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Label");

dojo.declare('umc.widgets.LoginDialog', [ dojox.widget.Dialog, umc.widgets.StandbyMixin ], {
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
		this.inherited(arguments);

		var widgets = [{
			type: 'TextBox',
			name: 'username',
			value: dojo.cookie('univention.umc.username') || '',
			description: 'Der Benutzername ihres Domänen-Kontos.',
			label: 'Benutzername'
		}, {
			type: 'PasswordBox',
			name: 'password',
			description: 'Das Passwort ihres Domänen-Kontos.',
			label: 'Passwort'
		}];

		var buttons = [{
			name: 'submit',
			label: 'Anmelden',
			callback: dojo.hitch(this, function(values) {
				// call LoginDialog.onSubmit() and clear password
				this._authenticate(values.username, values.password);
				this._form.elementValue('password', '');
			})
		}, {
			name: 'cancel',
			label: 'Zurücksetzen'
		}];

		var layout = [['username'], ['password']];
		
		this._form = new umc.widgets.Form({
			//style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			cols: 1,
			orientation: 'horiz',
			region: 'center'
		}).placeAt(this.containerNode);
		this._form.startup();

		// put the layout together
		this._layoutContainer = new dojox.layout.TableContainer({
			cols: 1,
			showLabels: false
		});
		this._layoutContainer.addChild(new umc.widgets.Label({
			content: '<p>Willkommen auf der Univention Management Console (v2). Bitte geben Sie Benutzername und Passwort ein!</p>'
		}));
		this._layoutContainer.addChild(this._form);
		this.set('content', this._layoutContainer);
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
		umc.tools.umcpCommand('auth', {
			username: username,
			password: password
		}).then(dojo.hitch(this, function(data) {
			// disable standby in any case
			//console.log('# _authenticate - ok');
			//console.log(data);
			this.standby(false);

			// make sure that we got data
			this.onLogin(username);
		}), dojo.hitch(this, function(error) {
			// disable standby in any case
			//console.log('# _authenticate - error');
			//console.log(error);
			this.standby(false);
		}));
	},

	onLogin: function(/*String*/ username) {
		// event stub
	}
});


