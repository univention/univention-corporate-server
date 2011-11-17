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
			helpText: this._('A connection to the VNC server can be established now. A click on the corresponding button launches a VNC browser client. To login, enter username and the password for VNC connection as specified in this module.')
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
			helpText: this._('This UMC module allows direct access to the graphical interface of the server via the VNC protocol. For this, a VNC server will be started first, then a connection can be established.')
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
			message += this._('VNC server is running and password is set.');
			this._form.getWidget('info').set('content', message);
		} else {
			this._form.getButton('start').set('visible', true);
			this._form.getButton('stop').set('visible', false);
			this._form.getButton('connect').set('visible', false);
			message += this._('VNC server is not running.');
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