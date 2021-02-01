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
/*global define, window*/

// Some thoughts about the programmatic page structure:
//
//	(1)	we establish a timer that will check if a job is running. All information
//		about the corresponding job come from the Python module, so we will have
//		accurate information even if we have closed and reopened the whole module.
//	(2)	the main purpose of this page is to watch the corresponding log file. This
//		is accomplished with a _LogView class that inherits from umc.widgets.Text
//		and umc.modules._updater._PollingMixin.
//	(3)	no matter how the page is closed: the main Module is listening to our
//		onStopWatching method to know when our current page can be closed.
//
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"umc/dialog",
	"umc/tools",
	"umc/modules/updater/Page",
	"umc/modules/updater/_LogViewer",
	"umc/widgets/Button",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/modules/lib/server",
	"umc/i18n!umc/modules/updater"
], function(declare, lang, domClass, dialog, tools, Page, _LogViewer, Button, ContainerWidget, Text, libServer, _) {
	return declare("umc.modules.updater.ProgressPage", Page, {

		// Polling interval for eventually running Updater jobs. If this is
		// set to zero it effectively stops the timer.
		_interval: 1000,

		_job_key: '', // the key of the currently running job

		_reboot_required: null,
		_may_just_close: false,

		allowClose: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			this._orgNavButtons = [{
				name: 'close',
				label: _("Back"),
				onClick: lang.hitch(this, '_closeLogView')
			}];

			// If I don't do that -> the page will switch 'show module help description' off
			lang.mixin(this, {
				helpText: ' ',
				headerButtons: [{
					name: 'close',
					iconClass: 'umcCloseIconWhite',
					label: _('Back'),
					callback: lang.hitch(this, '_closeLogView')
				}],
				navButtons: this._orgNavButtons,
				title: _("Update progress")
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._log = new _LogViewer({
				region: 'main',
				query: 'updater/installer/logfile'
			});
			this.addChild(this._log);

			this._log.on('queryerror', lang.hitch(this, 'onQueryError'));
			this._log.on('querysuccess', lang.hitch(this, 'onQuerySuccess'));
			this.set('allowClose', false);
		},

		_closeLogView: function() {
			if (!this.get('allowClose')) {
				dialog.alert(_('Closing not possible while running a update.'));
				return;
			}

			if (this._reboot_required) {
				// show an alert
				dialog.alert(_('In order to complete the recently executed action, it is required to reboot the system.'));
				this.onStopWatching();
			} else if (this._may_just_close) {
				this._may_just_close = false;
				this.onStopWatching();
			} else {
				// ask user to restart
				libServer.askRestart(_('For the changes to take effect, it is recommended to perform a restart of the UMC server components.')).then(
					function() { /* nothing to do */ },
					lang.hitch(this, function() {
						// user canceled -> change current view
						this.onStopWatching();
					})
				);
			}
		},

		// starts the polling timer as late as possible.
		startup: function() {
			this.inherited(arguments);
			this._query_job_status();
		},

		// callback that processes job status and reschedules itself.
		_process_job_status: function(data) {

			if (data !== null) {
				// This is the response that tells us which job is running. As soon as we have this
				// key we will ask for the full properties hash until the job is finished.
				if (typeof(data.result) === 'string') {
					var txt = data.result;
					if (txt !== '') {
						if (this._job_key === '') {
							this._job_key = txt; // from now on, we'll fetch full job details
							this._log.setJobKey(txt); // tell the logViewer which job we're referring to.
						}

						// if the page is currently in background then we must notify
						// our Module that we want to be shown now
						this.onJobStarted();
						this.set('allowClose', false); // close button now invisible.
					}
					if (data.result !== '') {
						// start the first call for 'update/installer/status' if we got a job name
						if ((this._interval) && (!this._timer)) {
							this._timer = window.setTimeout(lang.hitch(this, function() {
								this._timer = '';
								this._query_job_status();
							}), this._interval);
						}
					}
				} else {
					// This knows about all details of the job, and it will know when the job
					// is finished.
					this._last_job = data.result; // remember for later

					if (data.result.running) {
						// reschedule this as long as the job runs.
						if ((this._interval) && (!this._timer)) {
							this._timer = window.setTimeout(lang.hitch(this, function() {
								this._timer = '';
								this._query_job_status();
							}), this._interval);
						}
					} else {
						this.set('allowClose', true); // does the rest.
					}
				}
			} else {
				// error case, request could not been sent... try again
				if ((this._interval) && (!this._timer)) {
					this._timer = window.setTimeout(lang.hitch(this, function() {
						this._timer = '';
						this._query_job_status();
					}), this._interval);
				}
			}
		},

		// queries job status. As long as we know a job key -> ask for full
		// details. The handler _process_job_status() handles this gracefully.
		_query_job_status: function() {

			if (this._job_key === '') {
				tools.umcpCommand('updater/installer/running', {}, false).then(
					lang.hitch(this, function(data) {
						this.onQuerySuccess('updater/installer/running');
						this._process_job_status(data);
					}),
					lang.hitch(this, function(data) {
						this.onQueryError('updater/installer/running', data); // handles error
						this._process_job_status(null); // only for rescheduling
					})
				);
			} else {
				tools.umcpCommand('updater/installer/status', {job: this._job_key}, false).then(
					lang.hitch(this, function(data) {
						this.onQuerySuccess("updater/installer/status(" + this._job_key + ")");
						this._process_job_status(data);
					}),
					lang.hitch(this, function(data) {
						this.onQueryError('updater/installer/status', data); // handles error
						this._process_job_status(null); // only for rescheduling
					})
				);
			}
		},

		// switches visibility of our 'close' button on or off.
		// Additionally, changes some labels to reflect the current situation.
		_setAllowCloseAttr: function(allow_closing) {
			this._set('allowClose', allow_closing);  // public attribute used by updater.js
			this.set('navButtons', allow_closing ? this._orgNavButtons : []);
			// While the button is hidden, the polling callback maintains the content.
			// Only if Close is enabled -> set to a different text.
			if (allow_closing) {
				if ((this._job_key !== '') && (this._last_job)) {
					// First thing to do: notify the Module that the job is finished. So it can already
					// refresh the 'Updates' and 'Components' pages before the user gets back there.
					this.onJobFinished();

					// set headers according to the outcome
					var status = 'success';
					var lstat = this._last_job._status_;
					if ((lstat === undefined) || (lstat !== 'DONE')) {
						status = 'failed';
					}
					this._switch_headings(status);
					this._log.scrollToBottom(true); // jump to bottom a very last time
					this._log.onStopWatching(); // now log is freely scrollable manually
					this._alertUserOfStatusChange(status);

					this._last_job = null; // can be deleted, but this._job_key should be retained!
				}
			}
		},

		_alertUserOfStatusChange: function(status) {
			dialog.confirm(this.headerText, [{
				label: _("Investigate log further"),
				'default': status === 'failed'
			},
			{
				label: _("Finish updates"),
				'default': status === 'success',
				callback: lang.hitch(this, '_closeLogView')
			}], ' ');
		},

		// gives a means to restart polling after reauthentication
		startPolling: function() {
			this._process_job_status(null);
		},

		// This function will be called when the (background) ProgressPage encounters
		// that a job has been started. The updater Module listens here and will then
		// call startWatching.
		onJobStarted: function() {
		},

		// This function will be called when the already opened ProgressPage encounters
		// the end of the current job. The updater Module listens here and will refresh
		// the 'Updates' and 'Components' pages.
		onJobFinished: function() {
		},

		// updater Module calls this when the ProgressPage is to be opened.
		startWatching: function() {
			this.set('allowClose', false); // forbid closing this tab.
			this._log.startWatching(this._interval); // start logfile tail
		},

		// updater Module listens to this event to close the page
		//
		// This is a good place to reset the log viewer contents too.
		onStopWatching: function() {
			this._job_key = '';
			this._last_job = null;
			this._log.onStopWatching(true);
		},

		// lets the timer loop stop when the module is closed.
		uninitialize: function() {
			this.inherited(arguments);
			this._interval = 0;
		},

		// on switch to this page: set initial headings, and fetch
		// the 'job running' status at least once.
		_onShow: function() {
			this._switch_headings('running');
			this._query_job_status();
		},

		// internal function that switches any heading variables of
		// our current page, according to the retrieved job status
		_switch_headings: function(status) {
			// avoid doing that repeatedly
			if (status === this._last_heading_status) {
				return;
			}

			this._last_heading_status = status;

			var headings = {
				'running': {
					headerText: _('UCS is being updated'),
					helpText: '<p>' + _('The update is being executed.') +
						' ' + _('<b>Leave the system up and running</b> at any moment during the update!') + '</p>' +
						'<p>' + _('It is expected that the system may not respond (via web browser, SSH, etc.) during a period of up to several minutes during the update as services are stopped, updated, and restarted.') + '</p>'
				},
				'success': {
					headerText: _('UCS update successful'),
					helpText: _('The update has been successfully finished. Press the "back" button to close this view.')
				},
				'failed': {
					headerText: _('UCS update failed'),
					helpText: _('The update failed, please examine the log file for the exact cause. Press the "back" button to close this view.')
				}
			};

			var info = headings[status];
			info.forEach(function(v) {
				this.set(v, info[v]);
			});
			// this.layout();
		},

		updateStatus: function(values) {
			// receive new status values from update page
			this._reboot_required = tools.isTrue(values.reboot_required);
		}
	});
});
