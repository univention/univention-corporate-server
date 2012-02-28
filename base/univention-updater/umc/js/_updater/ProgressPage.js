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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._updater.ProgressPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.tools");

dojo.require("umc.modules._updater.Page");
dojo.require("umc.modules._updater._LogViewer");

// Some thoughts about the programmatic page structure:
//
//	(1)	we establish a timer that will check if a job is running. All information
//		about the corresponding job come from the Python module, so we will have
//		accurate information even if we have closed and reopened the whole module.
//	(2)	the main purpose of this page is to watch the corresponding log file. This
//		is accomplished with a _LogView class that inherits from umc.widgets.Text
//		and umc.modules._updater._PollingMixin.
//	(3)	no matter how the page is closed: the main Module is listening to our
//		stopWatching method to know when our current page can be closed.
//
dojo.declare("umc.modules._updater.ProgressPage", umc.modules._updater.Page, {

	i18nClass:		'umc.modules.updater',

	// Polling interval for eventually running Updater jobs. If this is
	// set to zero it effectively stops the timer.
	_interval:		1000,

	_job_key:		'',			// the key of the currently running job

	postMixInProperties: function() {

		this.inherited(arguments);

		// If I don't do that -> the page will switch 'show module help description' off
		dojo.mixin(this,{
			helpText:	' ',
			title:		this._("Update progress")
		});
	},

	buildRendering: function() {

		this.inherited(arguments);

		this._pane = new umc.widgets.ExpandingTitlePane({
			title:		this._("Log file view")
		});
		this.addChild(this._pane);

		this._head = new umc.widgets.Text({
			region:		'top',
			content:	this._("... please wait ...")
		});
		this._pane.addChild(this._head);

		this._log = new umc.modules._updater._LogViewer({
			i18nClass:		this.i18nClass,
			region:			'center',
			query:			'updater/installer/logfile'
		});
		this._pane.addChild(this._log);

		dojo.connect(this._log,'_query_error',dojo.hitch(this,function(subject,data) {
			this._query_error(subject,data);
		}));
		dojo.connect(this._log,'_query_success',dojo.hitch(this,function(subject) {
			this._query_success(subject);
		}));

		// returns to the calling page
		this._close = new umc.widgets.Button({
			label:		this._("back"),
			region:		'bottom',
			onClick:	dojo.hitch(this, function() {
				var tab = '';
				// Especially for the 'install a component' functionality: if we encounter
				// that the 'reboot required' flag has been set we don't want to switch
				// back to the 'Components' grid but rather to the 'Updates' page. We will
				// request this by unsetting the _last_tab property, so the switching
				// logic will revert to the first tab of our tab set.
				if (this._reboot_required)
				{
					this.last_tab = null;
				}
				if (this.last_tab)
				{
					tab = this.last_tab;
					this.last_tab = null;
				}
				this.stopWatching(tab);		// updater Module listens here and will switch display back to the given tab.
			})
		});
		this._pane.addChild(this._close);
		this._allow_close(false);
	},

	// starts the polling timer as late as possible.
	startup: function() {

		this.inherited(arguments);
		this._query_job_status();
	},

	// callback that processes job status and reschedules itself.
	_process_job_status: function(data) {

		if (data != null)
		{
			// This is the response that tells us which job is running. As soon as we have this
			// key we will ask for the full properties hash until the job is finished.
			if (typeof(data.result) == 'string')
			{
				var txt = data.result;
				if (txt == '')
				{
					// Should never happen
					if (this.last_tab)
					{
						this._allow_close(true);
					}
				}
				else
				{
					if (this._job_key == '')
					{
						this._job_key = txt;			// from now on, we'll fetch full job details
						this._log.setJobKey(txt);		// tell the logViewer which job we're referring to.
					}

					// if the page is currently in background then we must notify
					// our Module that we want to be shown now, and that we want to
					// know which tab we shall return to on close.
					if (! this.last_tab)
					{
						this.jobStarted();
					}
					else
					{
						this._allow_close(false);		// close button now invisible.
					}
				}
				if (data.result != '')
				{
					// start the first call for 'update/installer/status' if we got a job name
					if ((this._interval) && (! this._timer))
					{
						this._timer = window.setTimeout(dojo.hitch(this, function() {
							this._timer = '';
							this._query_job_status();
						}),this._interval);
					}
				}
			}
			else
			{
				// This knows about all details of the job, and it will know when the job
				// is finished.
				this._last_job = data.result;	// remember for later

				// FIXME Making margins by adding empty lines before and after the text; should
				//		be done by a style or style class.
				var msg = "&nbsp;<br/>";
				msg = msg + dojo.replace(this._("The job <b>{label}</b> (started {elapsed} ago) is currently running."),this._last_job);

				if (this._last_job['logfile'])
				{
					msg = msg + ('<br/>' + dojo.replace(this._("You're currently watching its log file <b>{logfile}</b>"),this._last_job));
				}
				msg = msg + "<br/>&nbsp;<br/>";


				this._head.set('content',msg);

				if (! data.result['running'])
				{
				}

				if (data.result['running'])
				{
					// reschedule this as long as the job runs.
					if ((this._interval) && (! this._timer))
					{
						this._timer = window.setTimeout(dojo.hitch(this, function() {
							this._timer = '';
							this._query_job_status();
						}),this._interval);
					}
				}
				else
				{
					this._allow_close(true);		// does the rest.
				}

				this._pane.layout();

			}
		}
		else {
			// error case, request could not been sent... try again
			if ((this._interval) && (! this._timer))
			{
				this._timer = window.setTimeout(dojo.hitch(this, function() {
					this._timer = '';
					this._query_job_status();
				}),this._interval);
			}
		}

	},

	// queries job status. As long as we know a job key -> ask for full
	// details. The handler _process_job_status() handles this gracefully.
	_query_job_status: function() {

		if (this._job_key == '')
		{
			umc.tools.umcpCommand(
				'updater/installer/running',{},false).then(
				dojo.hitch(this, function(data) {
					this._query_success('updater/installer/running');
					this._process_job_status(data);
				}),
				dojo.hitch(this, function(data) {
					this._query_error('updater/installer/running',data);		// handles error
					this._process_job_status(null);							// only for rescheduling
				})
			);
		}
		else
		{
			umc.tools.umcpCommand('updater/installer/status',{job:this._job_key},false).then(
					dojo.hitch(this, function(data) {
						this._query_success("updater/installer/status(" + this._job_key + ")");
						this._process_job_status(data);
					}),
					dojo.hitch(this, function(data) {
						this._query_error('updater/installer/status',data);		// handles error
						this._process_job_status(null);							// only for rescheduling
					})
				);
		}
	},

	// switches visibility of our 'close' button on or off.
	// Additionally, changes some labels to reflect the current situation.
	_allow_close: function(on) {
		dojo.toggleClass(this._close.domNode,'dijitHidden',! on);
		// While the button is hidden, the polling callback maintains the content
		// of this._head. Only if Close is enabled -> set to a different text.
		if (on)
		{
			if ((this._job_key != '') && (this._last_job))
			{
				// First thing to do: notify the Module that the job is finished. So it can already
				// refresh the 'Updates' and 'Components' pages before the user gets back there.
				this.jobFinished();

				// FIXME Manually making empty lines before and after this text; should better be done
				//		by a style or a style class.
				var msg = "&nbsp;<br/>";
				msg = msg + dojo.replace(this._("The current job (<b>{label}</b>) is now finished.<br/>"),this._last_job);
				if (typeof(this._last_job['elapsed']) != 'undefined')
				{
					msg = msg + dojo.replace(this._("It took {elapsed} to complete.<br/>"),this._last_job);
				}
				msg = msg + this._("You may return to the overview by clicking the 'back' button now.");
				msg = msg + "<br/>&nbsp;<br/>";

				this._head.set('content',msg);

				// set headers according to the outcome
				var status = 'success';
				var lstat = this._last_job['_status_'];
				if ((lstat == undefined) || (lstat != 'DONE'))
				{
					status = 'failed';
				}
				this._switch_headings(status);
				this._log.scrollToBottom();		// jump to bottom a very last time
				this._log.stopWatching();		// now log is freely scrollable manually

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
	// call startWatching with the currently opened tab.
	jobStarted: function() {
	},

	// This function will be called when the already opened ProgressPage encounters
	// the end of the current job. The updater Module listens here and will refresh
	// the 'Updates' and 'Components' pages.
	jobFinished: function() {
	},

	// updater Module calls this when the ProgressPage is to be opened.
	startWatching: function(args) {

		// ensure a clean look (and not some stale text from last job)
		this._head.set('content',this._("... loading job data ..."));

		dojo.mixin(this,args);						// as simple as possible.
		this._allow_close(false);					// forbid closing this tab.
		this._log.startWatching(this._interval);	// start logfile tail
	},

	// updater Module listens to this event to close the page
	// and reopen the named tab.
	//
	// This is a good place to reset the log viewer contents too.
	stopWatching: function(tab) {
		this._job_key = '';
		this._last_job = null;
		this._log.stopWatching(true);
	},

	// lets the timer loop stop when the module is closed.
	uninitialize: function() {

		this.inherited(arguments);
		this._interval = 0;
	},

	// on switch to this page: set initial headings, and fetch
	// the 'job running' status at least once.
	onShow: function() {
		this._switch_headings('running');
		this._query_job_status();
	},

	// internal function that switches any heading variables of
	// our current page, according to the retrieved job status
	_switch_headings: function(status) {

		// avoid doing that repeatedly
		if (status == this._last_heading_status)
		{
			return;
		}

		this._last_heading_status = status;

		var headings = {
			'running': {
				// title:			this._("Update in progress"),
				headerText:		this._("Univention Updater is working"),
				helpText:		this._("As long as the Univention Updater is updating your system, you're not allowed to manage settings or components. You may watch the progress, or close the module.")
			},
			'success': {
				// title:			this._("Update finished"),
				headerText:		this._("Univention Updater job completed"),
				helpText:		this._("Univention Updater has successfully finished the current job. You may read through the log file. If you're finished you may press the 'back' button to close this view.")
			},
			'failed': {
				// title:			this._("Update failed"),
				headerText:		this._("Univention Updater job failed"),
				helpText:		this._("Univention Updater could not successfully complete the current job. The log file should show the cause of the failure. If you're finished examining the log file you may press the 'back' button to close this view.")
			}
		};

		var info = headings[status];
		for (var v in info)
		{
			this.set(v,info[v]);
		}
		// this.layout();

	}

});
