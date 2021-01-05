/*
 * Copyright 2011-2021 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global console,define,window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dijit/Dialog",
	"umc/dialog",
	"login",
	"umc/app",
	"umc/tools",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/Module",
	"umc/modules/updater/UpdatesPage",
	"umc/modules/updater/ProgressPage",
	"umc/i18n!umc/modules/updater",
	"xstyle/css!./updater.css"
], function(declare, lang, array, on, Dialog, dialog, login, app, tools, ConfirmDialog, Module, UpdatesPage, ProgressPage, _) {

	app.registerOnStartup(function() {
		var checkUpdateIsRunning = function() {
			tools.umcpCommand('updater/installer/running', {}, false).then(function(data) {
				if (data.result === 'release') {
					app.openModule('updater');
					dialog.alert(_('<p><b>Caution!</b> Currently a release update is performed!</p>') + ' ' +  _('<p>Leave the system up and running until the update is completed!</p>'), _('Release update'));
				}
			});
		};
		var checkUpdateAvailable = function() {
			tools.ucr(['update/available']).then(function(_ucr) {
				if (tools.isTrue(_ucr['update/available'])) {
					var link = tools.linkToModule({module: 'updater'});
					dialog.notify(_('An update for UCS is available. Please visit the %s to install the updates.', link));
				}
			});
		};
		var checkOutOfMaintenance = function() {
			tools.umcpCommand('updater/maintenance_information').then(function(data) {
				var info = data.result;
				var link = tools.linkToModule({module: 'updater'});

				if (info.last_update_failed) {
					var version = _("a new UCS version");
					if (info.last_update_version) {
						version = "UCS " + info.last_update_version;
					}
					var warning1 = _("The update to %s failed. Please visit the %s for more information.", version, link);
					dialog.warn(warning1);
				}

				if (!info.show_warning) {
					return;
				}

				// show warning notification
				var warning2 = _("The currently used UCS version is out of maintenance. Please visit the %s for more information.", link);
				dialog.warn(warning2);
			});
		};
		checkUpdateIsRunning();
		checkUpdateAvailable();
		checkOutOfMaintenance();
	});

	return declare("umc.modules.updater", Module, {
		// some variables related to error handling
		_connection_status: 0,			// 0 ... successful or not set
										// 1 ... errors received
										// 2 ... currently authenticating
		_busy_dialog: null,		// a handle to the 'connection lost' dialog while
								// queries return with errors.
		_error_count: 0,		// how much errors in one row

		_beforeunloadHandler: null,

		buildRendering: function() {

			this.inherited(arguments);

			this._updates = new UpdatesPage({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this.addChild(this._updates);
			this._progress = new ProgressPage({});

			this.addChild(this._progress);

			// --------------------------------------------------------------------------
			//
			//        Connections that make the UI work (mostly tab switching)
			//

			this._progress.on('stopwatching', lang.hitch(this, function() {
				// Revert to the 'Updates' page if the installer action encountered
				// the 'reboot' affordance.
				this.selectChild(this._updates);
			}));

			// waits for the Progress Page to notify us that a job is running
			this._progress.on('jobstarted', lang.hitch(this, function() {
				this._switch_to_progress_page();
			}));

			// --------------------------------------------------------------------------
			//
			//        Connections that listen for changes and propagate
			//        them to other pages
			//

			// *** NOTE *** the Updates Page also has some mechanisms to refresh itself
			//                on changes that reflect themselves in the sources.list
			//                snippet files. But this refresh is intentionally slow (once
			//                in 5 secs) to avoid resource congestion. The callbacks here
			//                should immediately trigger refresh whenever something was
			//                done at the frontend UI.

			// ---------------------------------------------------------------------------
			//
			//        Listens for 'query error' and 'query success' events on all attached pages
			//        and their children, delivering them to our own (central) error handler
			//

			array.forEach(this.getChildren(), lang.hitch(this, function(child) {
				child.on('queryerror', lang.hitch(this, function(subject, data) {
					this.handleQueryError(subject, data);
				}));

				child.on('querysuccess', lang.hitch(this, function(subject, data) {
					this.handleQuerySuccess(subject, data);
				}));
			}));

			// --------------------------------------------------------------------------
			//
			//        Connections that centralize the work of the installer:
			//        listen for events that should start UniventionUpdater
			//

			// invokes the installer from the 'release update' button (Updates Page)
			this._updates.on('runreleaseupdate', lang.hitch(this, function(release) {
				this._call_installer({
					job: 'release',
					detail: release,
					confirm: lang.replace(_("Update to {release}"), {release: release})
				});
			}));

			// invokes the installer from the 'component update' button (Updates Page)
			this._updates.on('rundistupgrade', lang.hitch(this, function() {
				this._confirm_distupgrade();
			}));

			// propagate the status information to other pages
			this._updates.on('statusloaded', lang.hitch(this, function(vals) {
				this._progress.updateStatus(vals);
			}));

			this._updates.on('viewlog', lang.hitch(this, function() {
				this._progress._log.setJobKey('release');
				this._progress._may_just_close = true;
				this._switch_to_progress_page();
				this._progress.set('allowClose', true);
				this._progress._switch_headings('failed');
			}));

			this.registerUnloadHandler();
		},

		registerUnloadHandler: function() {
			// this piece of code was taken from:
			// https://developer.mozilla.org/en-US/docs/Web/Events/beforeunload
			this._beforeunloadHandler = on(window, "beforeunload", lang.hitch(this, function(e) {
				if (this.selectedChildWidget !== this._progress || this._progress._log.get('gotoMaintenance') || this._progress.get('allowClose')) {
					return;
				}
				var msg = _('An update of the system is being executed.') + '\n' +
					_('Are you sure to close the updater log view?') + '\n\n' +
					_('It is expected that the system may not respond (via web browser, SSH, etc.) during a period of up to several minutes during the update as services are stopped, updated, and restarted.');
				(e || window.event).returnValue = msg;
				return msg;
			}));
			this.own(this._beforeunloadHandler);
		},

		// We defer these actions until the UI is readily rendered
		startup: function() {
			this.inherited(arguments);
			this.selectChild(this._updates);
		},

		// Separate function that can be called the same way as _call_installer:
		// instead of presenting the usual confirm dialog it presents the list
		// of packages for a distupgrade.
		_confirm_distupgrade: function() {
			try {
				this.standbyDuring(this.umcpCommand('updater/updates/check')).then(lang.hitch(this, function(data) {
					// FIXME Lots of manual styling to achieve reasonable look
					var txt = "<table>\n";
					var upd = data.result.update;
					var ins = data.result.install;
					var rem = data.result.remove;
					if ((!upd.length) && (!ins.length) && (!rem.length)) {
						this._updates.refreshPage(true);
						return;
					}
					if (rem.length) {
						txt += "<tr><td colspan='2' style='padding:.5em;'><b><u>";
						if (rem.length === 1) {
							txt += lang.replace(_("1 package to be REMOVED"));
						} else {
							txt += lang.replace(_("{count} packages to be REMOVED"), {count:rem.length});
						}
						txt += "</u></b></td></tr>";
						array.forEach(rem, function(pkg) {
							txt += "<tr>\n";
							txt += "<td style='padding-left:1em;'>" + pkg[0] + "</td>\n";
							txt += "<td style='padding-left:1em;padding-right:.5em;'>" + pkg[1] + "</td>\n";
							txt += "</tr>\n";
						});
					}
					if (upd.length) {
						txt += "<tr><td colspan='2' style='padding:.5em;'><b><u>";
						if (upd.length === 1) {
							txt += lang.replace(_("1 package to be updated"));
						} else {
							txt += lang.replace(_("{count} packages to be updated"), {count:upd.length});
						}
						txt += "</u></b></td></tr>";
						array.forEach(upd, function(pkg) {
							txt += "<tr>\n";
							txt += "<td style='padding-left:1em;'>" + pkg[0] + "</td>\n";
							txt += "<td style='padding-left:1em;padding-right:.5em;'>" + pkg[1] + "</td>\n";
							txt += "</tr>\n";
						});
					}
					if (ins.length) {
						txt += "<tr><td colspan='2' style='padding:.5em;'><b><u>";
						if (ins.length === 1) {
							txt += lang.replace(_("1 package to be installed"));
						} else {
							txt += lang.replace(_("{count} packages to be installed"), {count:ins.length});
						}
						txt += "</u></b></td></tr>";
						array.forEach(ins, function(pkg) {
							txt += "<tr>\n";
							txt += "<td style='padding-left:1em;'>" + pkg[0] + "</td>\n";
							txt += "<td style='padding-left:1em;padding-right:.5em;'>" + pkg[1] + "</td>\n";
							txt += "</tr>\n";
						});
					}
					txt += "</table>";
					txt += "<p style='padding:1em;'>" + _("Do you really want to perform the update/install/remove of the above packages?") + "</p>\n";
					var dia = new ConfirmDialog({
						title: _("Start Upgrade?"),
						message: txt,
						'class': 'updaterDialog',
						options: [{
								label: _('Cancel'),
								name: 'cancel'
							}, {
								label: _('Install'),
								name: 'start',
								'default': true
							}]
					});

					dia.on('confirm', lang.hitch(this, function(answer) {
						dia.close();
						if (answer === 'start') {
							this._call_installer({
								confirm: false,
								job: 'distupgrade',
								detail: ''
							});
						}
					}));
					dia.show();

					return;
				}));
			} catch(error) {
				console.error("PACKAGE DIALOG: " + error.message);
			}
		},

		// Central entry point into all installer calls. Subject
		// and detail are passed as args to the 'updater/installer/execute' backend.
		//
		// Argument 'confirm' has special meaning:
		//        true ......... ask for confirmation and run the installer only if confirmed,
		//        false ........ run the installer unconditionally.
		//        any string ... the confirmation text to ask.
		_call_installer: function(args) {

			var msg = '';
			if (args.confirm) {
				msg = '<p>' + _('Please respect the following guidelines for UCS updates:') + '</p>';
				msg += '<ul>';
				msg += '<li>' + _('<b>Leave the system up and running</b> at any moment during the update!') + ' ' + _('It is expected that the system may not respond (via web browser, SSH, etc.) during a period of up to several minutes during the update as services are stopped, updated, and restarted.') + '</li>';
				msg += '<li>' + _('The update should occur in a <b>maintenance window</b> as some services in the domain may not be available during the update.') + '</li>';
				msg += '<li>' + _('It is recommended to <b>test the update</b> in a separate test environment prior to the actual update.') + '</li>';
				if (args.detail) {
					msg += '<li>' + _('Consider <a href="https://docs.software-univention.de/release-notes-%s-en.html" target="_blank">release notes and changelogs</a> as well as references posted in the <a href="https://help.univention.com/" target="_blank">Univention Help</a>.', args.detail) + '</li>';
				}
				else {
					msg += '<li>' + _('Consider <a href="https://docs.software-univention.de/" target="_blank">release notes and changelogs</a> as well as references posted in the <a href="https://help.univention.com/" target="_blank">Univention Help</a>.') + '</li>';
				}
				msg += '</ul>';
				msg += '<p>' + _('Depending on the system performance, network connection and the installed software the update may take from 30 minutes up to several hours.') + '</p>';

				dialog.confirm(msg, [{
						label: _('Cancel')
					}, {
						label: args.confirm,
						'default': true,
						callback: lang.hitch(this, function() {
							args.confirm = false;
							this._call_installer(args);
						})
					}
				], _('Update notes'));

				return;
			}

			this.standbyDuring(this.umcpCommand('updater/installer/execute', {
				job: args.job,
				detail: args.detail || ''
			})).then(lang.hitch(this, function(data) {
				if (data.result.status === 0) {
					this._switch_to_progress_page();
				} else {
					dialog.alert(lang.replace(_("The Univention Updater action could not be started [Error {status}]: {message}"), data.result));
				}
			}));
		},

		_switch_to_maintenance_page: function() {
		},

		// Switches to the progress view: all tabs but the 'update in progess' will disappear.
		// Remembers the currently selected tab and will restore it when finished.
		// NOTE that we don't pass any args to the progress page since it is able
		//        to fetch them all from the AT job.
		_switch_to_progress_page: function() {

			try {
				this.selectChild(this._progress);

				this._progress.startWatching();
			} catch(error) {
				console.error("switch_progress: " + error.message);
			}
		},

		// We must establish a NO ERROR callback too, so we can reset
		// the error status
		handleQuerySuccess: function(subject) {

			//console.error("QUERY '" + subject + "' -> SUCCESS");
			if (this._connection_status !== 0) {
				this._reset_error_status();
			}
		},

		// Recover after any kind of long-term failure:
		//
		//    -	set error counter to zero
		//    -	set connection status to ok
		//    -	close eventually opened 'connection lost' dialog
		//    -	refresh Updates page
		//    -	restart polling
		_reset_error_status: function() {

			this._connection_status = 0;
			this._error_count = 0;
			if (this._busy_dialog) {
				this._busy_dialog.hide();
				this._busy_dialog.destroy();
				this._busy_dialog = null;
			}
		},

		// Handles gracefully all things related to fatal query errors while
		// an installer call is running. The background is that all polling
		// queries are done with 'handleErrors=false', and their corresponding
		// Error callback hands everything over to this function. So it could
		// theoretically even survive a reboot...
		handleQueryError: function(subject, data) {

			try {
				// While the login dialog is open -> all queries return at the
				// error callback, but without data! (should be documented)
				// FIXME: remove this if()
				if (typeof(data) === 'undefined') {
					//console.error("QUERY '" + subject + "' without DATA");
					return;
				}
				//console.error("QUERY '" + subject + "' STATUS = " + data.status);
				var result = tools.parseError(data);
				if (result.status === 401) {
					if (this._connection_status !== 2) {
						this._connection_status = 2;

						if (this._busy_dialog) {
							this._busy_dialog.hide();
							this._busy_dialog.destroy();
							this._busy_dialog = null;
						}

						login.showLoginDialog().then(lang.hitch(this, function() {
							// if authenticated again -> reschedule refresh queries, Note that these
							// methods are intelligent enough to do nothing if the timer in question
							// is already active.
							this._updates.refreshPage();
							this._updates.startPolling();
							this._progress.startPolling();
						}));
					}
				} else {
					this._connection_status = 1;

					this._error_count = this._error_count + 1;
					if (this._error_count >= 5 && this._busy_dialog === null) {
						this._busy_dialog = new Dialog({
							title: _('Update notes'),
							closable: false,
							style: "width: 300px",
							'class': 'umcConfirmDialog'
						});
						this._busy_dialog.attr("content",
							'<p>' + _('The update is being executed.') + '</p>' +
							'<p>' + _('<b>Leave the system up and running</b> at any moment during the update!') + '</p>' +
							'<p>' + _('It is expected that the system may not respond (via web browser, SSH, etc.) during a period of up to several minutes during the update as services are stopped, updated, and restarted.') + '</p>');
						this._busy_dialog.show();
					}
				}
			} catch(error) {
				console.error("HANDLE_ERRORS: " + error.message);
			}
		}
	});

});
