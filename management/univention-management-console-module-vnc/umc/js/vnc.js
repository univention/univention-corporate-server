/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.vnc");

dojo.require("umc.i18n");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.PasswordInputBox");

dojo.declare("umc.modules.vnc", [ umc.widgets.Module, umc.i18n.Mixin ], {

	// internal reference to the VNC page
	_vncPage: null,

	// internal reference to the password page
	_passwordPage: null,

	standbyOpacity: 1.00,

	buildRendering: function() {
		this.inherited(arguments);
		this.standby(true);

		this.renderVNCPage();
		this.renderPasswordPage();

		this.init();
    },

	renderVNCPage: function() {
		this._vncPage = new umc.modules.vnc._VNCPage({
			headerText: this._('VNC'),
			helpText: this._('Access to a System via VNC Session')
		});
		this.addChild(this._vncPage);

		this.connect(this._vncPage, 'onStart', function() {
			this.standby(true);
			umc.tools.umcpCommand('vnc/start').then(
				dojo.hitch(this, function(data) {
					this.init();
					this.standby(false);
				}),
				dojo.hitch(this, function() {
					this.standby(false);
				})
			);
		});

		this.connect(this._vncPage, 'onStop', function() {
			this.standby(true);
			umc.tools.umcpCommand('vnc/stop').then(
				dojo.hitch(this, function(data) {
					this.init();
					this.standby(false);
				}),
				dojo.hitch(this, function() {
					this.standby(false);
				})
			);
		});

		this.connect(this._vncPage, 'onConnect', function() {
			umc.tools.umcpCommand('vnc/connect').then(
				dojo.hitch(this, function(data) {
					if (data.result.url != undefined) {
						window.open(data.result.url);
					}
				})
			);
		});
	},

	renderPasswordPage: function() {
		this._passwordPage = new umc.modules.vnc._PasswordPage({
			headerText: this._('VNC'),
			helpText: this._('Access to a System via VNC Session')
		});
		this.addChild(this._passwordPage);

		this.connect(this._passwordPage, 'onSetPassword', function(password) {
			this.standby(true);
			umc.tools.umcpCommand('vnc/password', {'password': password}).then(
				dojo.hitch(this, function(data) {
					this.init();
					this.standby(false);
				}),
				dojo.hitch(this, function() {
					this.standby(false);
				})
			);
		});
	},

	init: function() {
		umc.tools.umcpCommand('vnc/status').then(
			dojo.hitch(this, function(data) {
				if (! data.result.isSetPassword) {
					this.selectChild(this._passwordPage);
				} else {
					this._vncPage.init(data.result.isRunning);
					this.selectChild(this._vncPage);
				}
				this.standby(false);
			}),
			dojo.hitch(this, function() {
				this.standby(false);
			})
		);
	}
});

dojo.declare("umc.modules.vnc._VNCPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	// internal reference to the formular containing all form widgets
	_form: null,

	// use i18n information from umc.modules.vnc
	i18nClass: 'umc.modules.vnc',

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'Text',
			name: 'info',
			content: this._('Status: ')
		}];
		var buttons = [{
			name: 'start',
			label: this._('Start VNC server'),
			callback: dojo.hitch(this, function() {
				this.onStart();
			})
		}, {
			name: 'stop',
			label: this._('Stop VNC server'),
			callback: dojo.hitch(this, function() {
				this.onStop();
			})
		}, {
			name: 'connect',
			label: this._('Connect to the VNC server'),
			callback: dojo.hitch(this, function() {
				this.onConnect();
			})
		}];
		var layout = [['info'], ['start', 'stop', 'connect']];
		this._form = new umc.widgets.Form({
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('VNC configuration')
		});
		this.addChild(titlePane);
		titlePane.addChild(this._form);

		this._form.getButton('start').set('visible', false);
		this._form.getButton('stop').set('visible', false);
		this._form.getButton('connect').set('visible', false);
	},

	init: function(isRunning) {
		var message = this._('Status: ');
		if (isRunning) {
			this._form.getButton('start').set('visible', false);
			this._form.getButton('stop').set('visible', true);
			this._form.getButton('connect').set('visible', true);
			message += this._('Password is set and the VNC server is running.');
			this._form.getWidget('info').set('content', message);
		} else {
			this._form.getButton('start').set('visible', true);
			this._form.getButton('stop').set('visible', false);
			this._form.getButton('connect').set('visible', false);
			message += this._('Currently there is no VNC server running.');
			this._form.getWidget('info').set('content', message);
		}
	},

	onStart: function() {
		return true;
	},

	onStop: function() {
		return true;
	},

	onConnect: function() {
		return true;
	},

	postCreate: function() {
		this.inherited(arguments);
		this.startup();
	}
});

dojo.declare("umc.modules.vnc._PasswordPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	// internal reference to the formular containing all form widgets
	_form: null,

	// use i18n information from umc.modules.vnc
	i18nClass: 'umc.modules.vnc',

	buildRendering: function() {
		this.inherited(arguments);

		var widgets = [{
			type: 'Text',
			name: 'info',
			content: this._('To setup a VNC session a password is required.')
		}, {
			type: 'PasswordInputBox',
			name: 'password',
			label: this._('Password'),
			required: true
		}];

		var buttons = [{
			name: 'submit',
			label: this._('Set'),
			callback: dojo.hitch(this, function(data) {
				// TODO: Check if password value is ''
				if (this._form.getWidget('password').isValid()) {
					this.onSetPassword(data.password);
				}
			})
		}];

		var layout = [['info'], ['password'], ['submit']];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('VNC configuration')
		});

		this.addChild(titlePane);
		titlePane.addChild(this._form);
	},

	postCreate: function() {
		this.inherited(arguments);
		this.startup();
	},

	onSetPassword: function() {
		return true;
	}
});