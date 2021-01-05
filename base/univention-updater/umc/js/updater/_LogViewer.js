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
/*global define,document,window,XMLHttpRequest*/

// Class that provides a logfile viewer. Features are:
//
//	(1)	uses the _PollingMixin to query for the mtime of the named log file
//	(2)	provides scrolling capability
//	(3)	can scroll to the bottom of the file if new data has arrived
//		(should only work if the current position is at EOF)
//
// the passed query argument must be a backend function that understands
// the 'count' argument specially:
//
//	-1 ...... return the file timestamp of the log
//	0 ....... return the whole file contents
//  <any> ... return this many last lines (tail -n)

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/window",
	"dojo/_base/array",
	"dojo/dom-geometry",
	"dojo/window",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/i18n!umc/modules/updater"
], function(declare, lang, win, array, geometry, dojoWindow, entities, tools, Text, ContainerWidget, _) {
	return declare('umc.modules.updater._LogViewer', [ ContainerWidget ], {
		'class': 'umcUpdaterLogViewer',

		_oldScrollPosition: 0,
		_goToBottom: true,
		_last_stamp: 0,
		_check_interval: 0,
		_current_job: '',
		_log_position: 0,
		_max_number_of_lines: 2500, // ~ 200kB if one line ^= 80 chars
		_all_lines: [], // hold all past _max_number_of_lines lines

		buildRendering: function() {

			this.inherited(arguments);

			this._text = new Text({
				'class': 'umcDynamicMaxHeight',
				content: _("... loading log file ...")
			});
			this.addChild(this._text);
		},

		_checkForMaintenanceMode: function() {
			var loginURL = '/univention/login/';
			var xhr = new XMLHttpRequest();
			xhr.timeout = this._check_interval;
			xhr.onreadystatechange = lang.hitch(this, function(e) {
				if (xhr.readyState === 4 && xhr.status === 200) {
					var headers = xhr.getAllResponseHeaders().toLowerCase();
					array.forEach(headers.split('\n'), lang.hitch(this, function(header) {
						var content = header.split(':', 2);
						if (content.length == 2 && content[0] == 'x-ucs-maintenance' && content[1].trim() == 'true') {
							// Okay. During update, the maintenance mode is on.
							// We should leave UMC and watch the progress on the maintenance page instead
							this.set('gotoMaintenance', true);
							document.location = loginURL + '?dojo.preventCache=' + Math.floor(Math.random() * 100000);
						}
					}));
				}
			});
			xhr.open('HEAD', loginURL + '?dojo.preventCache=' + Math.floor(Math.random() * 100000), true);
			xhr.send();
		},

		_fetch_log: function() {
			this._checkForMaintenanceMode();
			tools.umcpCommand(this.query,{job:this._current_job, count:-1},false).then(lang.hitch(this,function(data) {

				this.onQuerySuccess(this.query + " [count=-1]");
				var stamp = data.result;
				if (stamp !== this._last_stamp) {
					this._last_stamp = stamp;
					tools.umcpCommand(this.query,{job:this._current_job,count:this._log_position},false).then(lang.hitch(this, function(data) {

						var contentLength = parseInt( data.result.length, 10 );
						if( contentLength ) {
							this._log_position += contentLength;
						}
						this.onQuerySuccess(this.query + " [count=0]");
						this.setContentAttr(data.result);
					}),
					lang.hitch(this, function(data) {
						this.onQueryError(this.query + " [count=0]",data);
					})
					);
				}

				if (this._check_interval) {
					window.setTimeout(lang.hitch(this,function() {
						this._fetch_log();
					}),this._check_interval);
				}

			}),
			lang.hitch(this,function(data) {
				this.onQueryError(this.query + " [count=-1]",data);
				// even in case of errors -> reschedule polling!
				if (this._check_interval) {
					window.setTimeout(lang.hitch(this,function() {
						this._fetch_log();
					}),this._check_interval);
				}
			})
			);

		},

		// set content:
		// -checks if the current scroll position
		// (before setting content) is at bottom, and if it is -> set
		// bottom position after setting content too.
		// -checks if the log file exceeds a certain limit
		// -URLs get replaced with clickable links
		setContentAttr: function(lines) {
			this._all_lines = this._all_lines.concat(lines);
			var printable_lines = this._all_lines;
			if (this._lines_exceeded || this._all_lines.length > this._max_number_of_lines) {
				var lines_exceeded = this._all_lines.length - this._max_number_of_lines;
				this._lines_exceeded += lines_exceeded;
				this._all_lines = this._all_lines.slice(lines_exceeded, this._all_lines.length);
				var logfile_exceeded = '[...] ' + lang.replace(_('The log file exceeded {max} lines by {exceeded}. Please see the full logfile.'),
					{
						max: this._max_number_of_lines,
						exceeded: this._lines_exceeded
					}
				);
				printable_lines = [logfile_exceeded].concat(this._all_lines);
			}
			var content = entities.encode(printable_lines.join('\n'));
			content = content.replace(/https?:\/\/.[^&"> \n\t]+/gi, '<a href="$&" target="_blank" rel="noopener noreferrer">$&</a>');
			this._text.set('content', content);
			this.scrollToBottom();
		},

		// 3 cases we want to scroll to the bottom
		// (1) module has been just loaded --> this._goToBottom
		// (2) someone tells us to do so --> forceScrollToBottom
		// (3) the user scrolls to a defined position --> isAtBottom()
		scrollToBottom: function(forceScrollToBottom) {
			var body_node = win.body();
			if (forceScrollToBottom === true) {
				this._goToBottom = true;
			}
			this.hasUserMovedScrollbar(this._oldScrollPosition, geometry.docScroll().y);
			this.isAtBottom(body_node);
			if (this._goToBottom){
				window.scrollTo(0, geometry.position(body_node).h);
			}
			this._oldScrollPosition = geometry.docScroll().y;
		},

		// if the old scrollbar position isn't the new one, the user has changed it
		hasUserMovedScrollbar: function(oldPos, newPos){
			if (oldPos !== newPos){
				this._goToBottom = false;
			}
		},

		// if the user scrolls to a defined position of the scrollbar, we are guessing
		// that the user wants the scrollbar to auto-scroll again
		// this point is defined at a ratio of 75%
		isAtBottom: function(body_node){
			var viewPortHeight = dojoWindow.getBox().h;
			var content_height = geometry.position(body_node).h; // the overall height of the text inside the view
			if (content_height === 0) {
				return;
			}

			var scroll_position = geometry.docScroll().y; //  current position auf the scrollbar
			var ratio = (scroll_position + viewPortHeight) / content_height; 
			if (ratio >= 0.75) {
				this._goToBottom = true;
			}
		},


		// Called from ProgressPage when the log file polling is to be started.
		// job key can't be an argument here as we don't know it.
		startWatching: function(interval) {

			this._check_interval = interval;
			// clean up any stale display and states from last run
			this.set('content', _("... loading log file ..."));
			this._all_lines = [];
			this._lines_exceeded = 0;
			this._goToBottom = true;
			this._last_stamp = 0;
			this._log_position = 0;

			this._fetch_log();		// first call, will reschedule itself as long
									// as _check_interval is not zero
		},

		// A separate function that is called by the 'ProgressPage' when the key of the
		// current job has become known.
		setJobKey: function(job) {
			this._current_job = job;
		},

		// effectively stops the polling timer. Can be called from outside (if ProgressPage is being closed)
		// or from inside (as 'uninitialize' handler)
		//
		// Argument 'clean' = TRUE -> also clean up display buffer contents.
		onStopWatching: function(clean) {

			this._check_interval = 0;

			if ((typeof(clean) !== 'undefined') && (clean)) {
				this.set('content',_("... loading log file ..."));
			}
		},

		uninitialize: function() {
			this.inherited(arguments);
			this.onStopWatching();
		},

		// can be listened to from outside
		onQueryError: function(subject,data) {
		},
		onQuerySuccess: function(subject) {
		}
	});
});
