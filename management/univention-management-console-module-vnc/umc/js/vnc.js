/*
 * Copyright 2011-2012 Univention GmbH
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

/*global define window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/tools",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/Form",
	"umc/widgets/PasswordInputBox",
	"umc/i18n!umc/modules/vnc"
], function(declare, lang, array, tools, ExpandingTitlePane, Module, Page, Text, Form, PasswordInputBox, _) {

	var _VNCPage = declare("umc.modules.vnc._VNCPage", Page, {

		// internal reference to the formular containing all form widgets
		_form: null,

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: Text,
				name: 'info',
				content: _('Status: ')
			}];
			var buttons = [{
				name: 'start',
				label: _('Start VNC server'),
				callback: lang.hitch(this, function() {
					this.onStart();
				})
			}, {
				name: 'stop',
				label: _('Stop VNC server'),
				callback: lang.hitch(this, function() {
					this.onStop();
				})
			}, {
				name: 'connect',
				label: _('Connect to the VNC server'),
				callback: lang.hitch(this, function() {
					this.onConnect();
				})
			}];
			var layout = [['info'], ['start', 'stop', 'connect']];
			this._form = new Form({
				widgets: widgets,
				buttons: buttons,
				layout: layout
			});

			var titlePane = new ExpandingTitlePane({
				title: _('VNC configuration')
			});
			this.addChild(titlePane);
			titlePane.addChild(this._form);

			this._form.getButton('start').set('visible', false);
			this._form.getButton('stop').set('visible', false);
			this._form.getButton('connect').set('visible', false);
		},

		init: function(isRunning) {
			var message = _('Status: ');
			if (isRunning) {
				this._form.getButton('start').set('visible', false);
				this._form.getButton('stop').set('visible', true);
				this._form.getButton('connect').set('visible', true);
				message += _('VNC server is running and password is set.');
				this._form.getWidget('info').set('content', message);
			} else {
				this._form.getButton('start').set('visible', true);
				this._form.getButton('stop').set('visible', false);
				this._form.getButton('connect').set('visible', false);
				message += _('VNC server is not running.');
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

	var _PasswordPage = declare("umc.modules.vnc._PasswordPage", Page, {

		// internal reference to the formular containing all form widgets
		_form: null,

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: Text,
				name: 'info',
				content: _('To setup a VNC session a password is required.')
			}, {
				type: PasswordInputBox,
				name: 'password',
				label: _('Password'),
				required: true
			}];

			var buttons = [{
				name: 'submit',
				label: _('Set'),
				callback: lang.hitch(this, function() {
					var passwordWidget = this._form.getWidget('password');
					if (passwordWidget.isValid()) {
						this.onSetPassword(passwordWidget.get('value'));
					}
				})
			}];

			var layout = [['info'], ['password'], ['submit']];

			this._form = new Form({
				widgets: widgets,
				buttons: buttons,
				layout: layout
			});

			var titlePane = new ExpandingTitlePane({
				title: _('VNC configuration')
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

	return declare("umc.modules.vnc", Module, {

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
			this._vncPage = new _VNCPage({
				headerText: _('VNC'),
				helpText: _('A connection to the VNC server can be established now. A click on the corresponding button launches a VNC browser client. To login, enter username and the password for VNC connection as specified in this module.')
			});
			this.addChild(this._vncPage);

			this._vncPage.on('start', lang.hitch(this, function() {
				this.standby(true);
				tools.umcpCommand('vnc/start').then(
					lang.hitch(this, function(data) {
						this.init();
						this.standby(false);
					}),
					lang.hitch(this, function() {
						this.standby(false);
					})
				);
			}));

			this._vncPage.on('stop', lang.hitch(this, function() {
				this.standby(true);
				tools.umcpCommand('vnc/stop').then(
					lang.hitch(this, function(data) {
						this.init();
						this.standby(false);
					}),
					lang.hitch(this, function() {
						this.standby(false);
					})
				);
			}));

			this._vncPage.on('connect', lang.hitch(this, function() {
				tools.umcpCommand('vnc/connect').then(
					lang.hitch( this, function( response ) {
						var w = window.open();
						var html = lang.replace( '<html><head><title>{host}</title></head><body><applet archive="/vnc/TightVncViewer.jar" code="com.tightvnc.vncviewer.VncViewer" height="100%%" width="100%%"><param name="host" value="localhost"/><param name="port" value="{port}"/><param name="socketfactory" value="com.tightvnc.vncviewer.SshTunneledSocketFactory"><param name="sshhost" value="{host}"><param name="offer relogin" value="no" /></applet></body></html>', {
							host: response.result.host,
							port: response.result.port
						} );
						w.document.write( html );
						w.document.close();
					})
				);
			}));
		},

		renderPasswordPage: function() {
			this._passwordPage = new _PasswordPage({
				headerText: _('VNC'),
				helpText: _('This UMC module allows direct access to the graphical interface of the server via the VNC protocol. For this, a VNC server will be started first, then a connection can be established.')
			});
			this.addChild(this._passwordPage);

			this._passwordPage.on('SetPassword', lang.hitch(this, function(password) {
				this.standby(true);
				tools.umcpCommand('vnc/password', {'password': password}).then(
					lang.hitch(this, function(data) {
						this.init();
						this.standby(false);
					}),
					lang.hitch(this, function() {
						this.standby(false);
					})
				);
			}));
		},

		init: function() {
			tools.umcpCommand('vnc/status').then(
				lang.hitch(this, function(data) {
					if (! data.result.isSetPassword) {
						this.selectChild(this._passwordPage);
					} else {
						this._vncPage.init(data.result.isRunning);
						this.selectChild(this._vncPage);
					}
					this.standby(false);
				}),
				lang.hitch(this, function() {
					this.standby(false);
				})
			);
		}
	});

});
