/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"dojo/promise/all",
	"dojox/html/entities",
	"umc/dialog",
	"umc/tools",
	"umc/app",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/ProgressBar",
	"umc/modules/join/Form",
	"umc/modules/join/Grid",
	"umc/modules/lib/server",
	"umc/i18n!umc/modules/join"
], function(declare, lang, array, topic, all, entities, dialog, tools, app, ConfirmDialog,
			Module, Page, Text, TextBox, PasswordBox, ProgressBar, JoinForm, JoinGrid, Lib_Server, _) {

	app.registerOnStartup(function() {
		var checkForUserRoot = function() {
			tools.ucr(['system/setup/showloginmessage', 'server/role']).then(function(_ucr) {
				if (tools.status('username') == 'root' && tools.isFalse(_ucr['system/setup/showloginmessage'])) {
					var login_as_admin_tag = '<a href="javascript:void(0)" onclick="require(\'login\').relogin(\'Administrator\')">Administrator</a>';
					if (_ucr['server/role'] == 'domaincontroller_slave') {
						dialog.notify(_('As %(root)s you do not have access to the App Center. For this you need to log in as %(administrator)s.', {root: '<strong>root</strong>', administrator: login_as_admin_tag}));
					} else { // master, backup
						dialog.notify(_('As %(root)s you have neither access to the domain administration nor to the App Center. For this you need to log in as %(administrator)s.', {root: '<strong>root</strong>', administrator: login_as_admin_tag}));
					}
				}
			});
		};

		var checkJoinStatus = function() {
			all([
				tools.umcpCommand('join/joined', null, false),
				tools.umcpCommand('join/scripts/query', null, false)
			]).then(
				lang.hitch(this, function(data) {
					var systemJoined = data[0].result;
					var allScriptsConfigured = array.every(data[1].result, function(item) {
						return item.configured;
					});
					var joinModuleLink = tools.linkToModule({module: 'join'});
					if (!systemJoined) {
						// Bug #33389: do not prompt any hint if the system is not joined
						// otherwise we might display this hint if a user runs the appliance
						// setup from an external client.
						// i18n: %s is the "Domain join module".
						//dialog.warn(_('The system has not been joined into a domain so far. Please visit the %s to join the system.', joinModuleLink));
					} else if (!allScriptsConfigured) {
						// i18n: %s is the "Domain join module".
						dialog.notify(_('Not all installed components have been registered. Please visit the %s to register the remaining components.', joinModuleLink));
					}

					if (systemJoined) {
						// Bug #33333: only show the hint for root login if system is joined
						checkForUserRoot();
					}
				}), function() {
					console.warn('WARNING: An error occurred while verifying the join state. Ignoring error.');
				}
			);
		};
		checkJoinStatus();
	});

	var JoinPage = declare("umc.modules.join.JoinPage", [Page], {
		_form: null,
		_joining: null, // flag for the last executed action

		helpText: _("Please enter credentials of a user account with administrator rights to join the system."),
		fullWidth: true,

		buildRendering: function() {
			this.inherited(arguments);

			this._form = new JoinForm({});
			this.addChild(this._form);
		}
	});

	var StatusPage = declare("umc.modules.join.StatusPage", [Page], {
		_grid: null,

		helpText: _("This page shows the status of all available join scripts on this system, along with all join-related actions."),
		fullWidth: true,

		buildRendering: function() {
			this.inherited(arguments);

			this._grid = new JoinGrid({
				sortIndex: 2
			});
			this.addChild(this._grid);
		}
	});

	var LogPage = declare("umc.modules.join.LogPage", [Page], {
		_logtext: null, // text widget that holds log

		headerText: _("Join log"),
		fullWidth: true,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Show Join status'),
				callback: lang.hitch(this, 'onShowGrid')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);

			// FIXME use a generic CSS class that requests a specific monospaced font
			this._logtext = new Text({
				region:			'main',
				content:		_('... loading log ...'),
				style:			'font-family: monospace;'
			});

			this.addChild(this._logtext);
		},

		onShowGrid: function() {
			// event stub
		},

		setText: function(text) {
			this._logtext.set('content', text);
		},

		// fetches join log text.
		fetch_log_text: function() {
			// now really fetch log file contents.
			tools.umcpCommand('join/logview').then(lang.hitch(this, function(data) {
				var txt = entities.encode(data.result).replace(/\n/g, "<br/>\n");
				this.setText(txt);
			}));
		}
	});

	return declare("umc.modules.join", [ Module ], {

		standbyOpacity: 1,
		region: 'main',

		_serverRole: null,

		_switchView: function(code) {
			var lastSelectedChild = this.selectedChildWidget;

			var child = {
				'grid': this._statuspage,
				'log': this._logpage,
				'join_form': this._joinpage
			}[code];
			if (child) {
				this.selectChild(child);
			}

			// update the layout if view changed
			if (lastSelectedChild != this.selectedChildWidget) {
				this.layout();
				// redo the status query for the grid
				this._statuspage._grid.reload_grid();
			}
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.standby(true);

			this._progressBar = new ProgressBar();
			this.own(this._progressBar);

			this._joinpage = new JoinPage();
			this.addChild(this._joinpage);

			this._statuspage = new StatusPage();
			this.addChild(this._statuspage);

			this._logpage = new LogPage();
			this.addChild(this._logpage);

			// select the status page as default
			this.selectChild(this._statuspage);

			// join the system
			this._joinpage._form.on('submit', lang.hitch(this, function() {
				// trigger the join procedure
				var values = this._joinpage._form.get('value');
				this._joinpage._form._widgets.password.set('value', '');

				topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'initial-join');
				this.join(values);
			}));

			// run join scripts
			this._statuspage._grid.on('runScripts', lang.hitch(this, function(scripts, force) {
				var txtscripts = '<ul style="max-height: 200px; overflow: auto;"><li>' + scripts.join('</li><li>') + '</ul>';
				if (this._serverRole == 'domaincontroller_master') {
					// we do not need credentials on DC master
					dialog.confirm(_('The following join scripts will be executed: ') + txtscripts, [{
						name: 'cancel',
						label: 'Cancel',
						'default': true
					}, {
						name: 'run',
						label: _('Run join scripts'),
						callback: lang.hitch(this, function() {
							this.runJoinScripts(scripts, force, {});
						})
					}]);
				} else {
					this.getCredentials(txtscripts).then(lang.hitch(this, function(credentials) {
						this.runJoinScripts(scripts, force, credentials);
					}));
				}
			}));

			tools.umcpCommand('join/locked').then(lang.hitch(this, function(data) {
				if (data.result) {
					this.addWarning(_('Currently, software is being installed or uninstalled. Join scripts should not be run right now.'));
				}
			}));
			// show the join logfile
			this._statuspage._grid.on('ShowLogfile', lang.hitch(this, function() {
				this._switchView('log');
				this._logpage.fetch_log_text();
			}));

			// rejoin the system
			this._statuspage._grid.on('Rejoin',  lang.hitch(this, function() {
//				this._switchView('join_form');
				dialog.confirmForm({form: new JoinForm({buttons: []}), submit: _('Rejoin system'), style: 'max-width: 350px;'}).then(lang.hitch(this, function(values) {
					this.join(values);
				}));
			}));

			this._logpage.on('ShowGrid', lang.hitch(this, function() {
				this._switchView('grid');
			}));

			all([
				this.umcpCommand('join/joined'),
				this.umcpCommand('join/running'),
				tools.ucr('server/role')
			]).then(lang.hitch(this, function(results) {
				var joined = results[0].result;
				var job_running = results[1].result;
				this._serverRole = results[2]['server/role'];

				this.standby(false);
				this.standbyOpacity = 0.75;  // set it back to semi transparent

				if (job_running) {
					// display the running progress
					this._joinpage.showProgressBar(_('A join process is already running...'), _('The join scripts have successfully been executed.'));
				}
				else if (!joined) {
					if (this._serverRole == 'domaincontroller_master') {
						// i18n: %s is the "XXX module".
						dialog.alert(_('A DC master should be joined by the %s.', tools.linkToModule({module: 'setup', flavor: 'wizard'}) || _('Basic settings module')));
						return;
					}
					this._switchView('join_form');
				} else {
					// grid view is selected by default... refresh the grid
					this._statuspage._grid.reload_grid();
				}
			}), lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		// starts the join process and show progressbar
		join: function(dataObj) {
			this.standbyDuring(this.umcpCommand('join/join', {
				hostname: dataObj.hostname,
				username: dataObj.username,
				password: dataObj.password
			})).then(lang.hitch(this, function() {
				this._joining = true;
				this.showProgressBar();
			}), lang.hitch(this, function() {
				this._joining = false;
				this.reinit(false);
			}));
		},

		runJoinScripts: function(scripts, force, credentials) {
			var values = { scripts: scripts, force: force };
			if (credentials.username) {
				values.username = credentials.username;
			}
			if (credentials.password) {
				values.password = credentials.password;
			}

			this.standbyDuring(this.umcpCommand('join/run', values)).then(lang.hitch(this, function() {
				this._joining = false;
				// Job is started. Now wait for its completion.
				this.showProgressBar();
			}), lang.hitch(this, function() {
				this._joining = false;
				this.reinit(false);
			}));
		},

		showProgressBar: function(title, successmsg) {
			this.standby(false);
			this.standby(true, this._progressBar);
			// Job is started. Now wait for its completion.
			this._progressBar.reset(title || _('Starting the join process...'));
			this._progressBar.auto(
				'join/progress',
				{},
				lang.hitch(this, function() {
					this.standby(false);
					var errors = this._progressBar.getErrors();
					if (errors.critical) {
						// invalid credentials... do not show the restart dialog
						dialog.alert(errors.errors[0], _('Join error'));
						this.reinit(false);
					} else if (errors.errors.length) {
						this._alert(errors.errors[0], _('Join error'), lang.hitch(this, function() {
							// reload and show restart dialog after user closed the pop up
							this.reinit(true);
						}));
					} else {
						this.addNotification(successmsg || _('The join process was successful.'));
						this.reinit(true);
					}
				}),
				undefined,
				undefined,
				true // let our callback handle errors
			);
		},

		// gets the current join status and switches display mode if needed.
		reinit: function(restart) {
			this.standby(true);
			return this.umcpCommand('join/joined').then(lang.hitch(this, function(data) {
				// update view
				var joined = data.result;
				if (joined) {
					// show grid with join status, else....
					this._switchView('grid');
				} else {
					// show affordance to join, nothing more.
					this._switchView('join_form');
				}

				if (restart) {
					// ask to restart / reboot
					if (this._joining && joined) {
						Lib_Server.askReboot(_('A reboot of the server is recommended after joining the system.'));
					} else {
						Lib_Server.askRestart(_('A restart of the UMC server components may be necessary for changes to take effect.'));
					}
				}

				this._joining = null;
				this._statuspage._grid.reload_grid();
				this.standby(false);
			}), lang.hitch(this, function(result) {
				this.standby(false);
				console.error("reinit ERROR " + result.message);
			}));
		},

		_alert: function(msg, title, callback) {
			var dialog = new ConfirmDialog({
				message: msg,
				title: title,
				style: 'max-width: 650px;',
				options: [{
					label: 'Ok',
					'default': true,
					callback: lang.hitch(this, function() {
						callback();
						dialog.hide();
					})
				}]
			});
			this.own(dialog);
			dialog.on('cancel', function() { callback(); });
			dialog.show();
			return dialog;
		},

		// pop up to ask for credentials when running join scripts
		getCredentials: function(scripts) {
			var msg = _('<p>Please enter credentials of a user account with administrator rights to run the selected join scripts.</p>') + scripts;
			var deferred = dialog.confirmForm({
				widgets: [{
					name: 'text',
					type: Text,
					content: msg
				}, {
					name: 'username',
					type: TextBox,
					label: _('Username'),
					value: tools.status('username') == 'root' ? 'Administrator' : tools.status('username')
				}, {
					name: 'password',
					type: PasswordBox,
					label: _('Password')
				}],
				layout: [ 'text', 'username', 'password' ],
				title: _('Run join scripts'),
				submit: _('Run'),
				style: 'max-width: 400px;'
			}).then(function(values) {
				if (!values.password || values.password.length === 0) {
					dialog.alert(_('The password may not be empty.'), _('Password invalid'));
					throw new Error();
				}
				if (!values.username || values.username.length === 0) {
					dialog.alert(_('The username may not be empty.'), _('Username invalid'));
					throw new Error();
				}
				return values;
			});

			return deferred;
		}

	});
});
