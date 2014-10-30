/*
 * Copyright 2011-2014 Univention GmbH
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

		postMixInProperties: function() {
			this.inherited(arguments);

			// If I don't do that -> the page will switch 'show module help description' off
			lang.mixin(this, {
				helpText: ' ',
				headerButtons: [{
					name: 'close',
					iconClass: 'umcCloseIconWhite',
					label: _('Back'),
					callback: lang.hitch(this, '_closeLogView')
				}],
				navButtons: [{
					name: 'close',
					label: _("Back"),
					onClick: lang.hitch(this, '_closeLogView')
				}],
				title: _("Update progress")
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._head = new Text({
				region: 'nav',
				content: _("... please wait ...")
			});
			this.addChild(this._head);

			this._log = new _LogViewer({
				region: 'main',
				query: 'updater/installer/logfile'
			});
			this.addChild(this._log);

			this._log.on('queryerror', lang.hitch(this, 'onQueryError'));
			this._log.on('querysuccess', lang.hitch(this, 'onQuerySuccess'));
			this._allow_close(false);
		},

		_closeLogView: function() {
			if (!this._allow_closing) {
				dialog.alert(_('Closing not possible while running a update.'));
				return;
			}

			if (this._reboot_required) {
				// show an alert
				dialog.alert(_('In order to complete the recently executed action, it is required to reboot the system.'));
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
				if (typeof(data.result) == 'string') {
					var txt = data.result;
					if (txt !== '') {
						if (this._job_key === '') {
							this._job_key = txt;			// from now on, we'll fetch full job details
							this._log.setJobKey(txt);		// tell the logViewer which job we're referring to.
						}

						// if the page is currently in background then we must notify
						// our Module that we want to be shown now
						this.onJobStarted();
						this._allow_close(false);		// close button now invisible.
					}
					if (data.result !== '') {
						// start the first call for 'update/installer/status' if we got a job name
						if ((this._interval) && (! this._timer)) {
							this._timer = window.setTimeout(lang.hitch(this, function() {
								this._timer = '';
								this._query_job_status();
							}), this._interval);
						}
					}
				} else {
					// This knows about all details of the job, and it will know when the job
					// is finished.
					this._last_job = data.result;	// remember for later

					// FIXME Making margins by adding empty lines before and after the text; should
					//		be done by a style or style class.
					var msg = "&nbsp;<br/>";
					msg = msg + lang.replace(_("The job <b>{label}</b> (started {elapsed} ago) is currently running."), this._last_job);

					if (this._last_job.logfile)
					{
						msg = msg + ('<br/>' + lang.replace(_("You're currently watching its log file <b>{logfile}</b>"), this._last_job));
					}
					msg = msg + "<br/>&nbsp;<br/>";


					this._head.set('content', msg);

					// if (! data.result['running'])
					// {
					// }

					if (data.result.running) {
						// reschedule this as long as the job runs.
						if ((this._interval) && (! this._timer))
						{
							this._timer = window.setTimeout(lang.hitch(this, function() {
								this._timer = '';
								this._query_job_status();
							}), this._interval);
						}
					} else {
						this._allow_close(true);		// does the rest.
					}
				}
			} else {
				// error case, request could not been sent... try again
				if ((this._interval) && (! this._timer)) {
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
						this.onQueryError('updater/installer/running', data);		// handles error
						this._process_job_status(null);							// only for rescheduling
					})
				);
			} else {
				tools.umcpCommand('updater/installer/status', {job: this._job_key}, false).then(
					lang.hitch(this, function(data) {
						this.onQuerySuccess("updater/installer/status(" + this._job_key + ")");
						this._process_job_status(data);
					}),
					lang.hitch(this, function(data) {
						this.onQueryError('updater/installer/status', data);		// handles error
						this._process_job_status(null);							// only for rescheduling
					})
				);
			}
		},

		// switches visibility of our 'close' button on or off.
		// Additionally, changes some labels to reflect the current situation.
		_allow_close: function(yes) {
			this._allow_closing = yes;
			// While the button is hidden, the polling callback maintains the content
			// of this._head. Only if Close is enabled -> set to a different text.
			if (yes)
			{
				if ((this._job_key !== '') && (this._last_job))
				{
					// First thing to do: notify the Module that the job is finished. So it can already
					// refresh the 'Updates' and 'Components' pages before the user gets back there.
					this.onJobFinished();

					// FIXME Manually making empty lines before and after this text; should better be done
					//		by a style or a style class.
					var msg = "&nbsp;<br/>";
					msg = msg + lang.replace(_("The current job (<b>{label}</b>) is now finished.<br/>"), this._last_job);
					if (this._last_job.elapsed !== undefined)
					{
						msg = msg + lang.replace(_("It took {elapsed} to complete.<br/>"), this._last_job);
					}
					msg = msg + _("You may return to the overview by clicking the 'back' button now.");
					msg = msg + "<br/>&nbsp;<br/>";

					this._head.set('content', msg);

					// set headers according to the outcome
					var status = 'success';
					var lstat = this._last_job._status_;
					if ((lstat === undefined) || (lstat != 'DONE'))
					{
						status = 'failed';
					}
					this._switch_headings(status);
					this._log.scrollToBottom(true);		// jump to bottom a very last time
					this._log.onStopWatching();		// now log is freely scrollable manually

					this._last_job = null;	// can be deleted, but this._job_key should be retained!
				}
			}
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
			// ensure a clean look (and not some stale text from last job)
			this._head.set('content', _("... loading job data ..."));

			this._allow_close(false);					// forbid closing this tab.
			this._log.startWatching(this._interval);	// start logfile tail
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
			if (status == this._last_heading_status) {
				return;
			}

			this._last_heading_status = status;

			var headings = {
				'running': {
					// title: _("Update in progress"),
					headerText: _("Univention Updater is working"),
					helpText: _("As long as the Univention Updater is updating your system, you're not allowed to manage settings. You may watch the progress, or close the module.")
				},
				'success': {
					// title: _("Update finished"),
					headerText: _("Univention Updater job completed"),
					helpText: _("Univention Updater has successfully finished the current job. You may read through the log file. If you're finished you may press the 'back' button to close this view.")
				},
				'failed': {
					// title: _("Update failed"),
					headerText: _("Univention Updater job failed"),
					helpText: _("Univention Updater could not successfully complete the current job. The log file should show the cause of the failure. If you're finished examining the log file you may press the 'back' button to close this view.")
				}
			};

			var info = headings[status];
			for (var v in info)
			{
				this.set(v, info[v]);
			}
			// this.layout();

		},

		updateStatus: function(values) {
			// receive new status values from update page
			this._reboot_required = tools.isTrue(values.reboot_required);
		}
	});
});
