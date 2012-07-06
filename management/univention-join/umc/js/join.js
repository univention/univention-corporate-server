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
/*global console MyError dojo dojox dijit umc setTimeout*/

dojo.provide("umc.modules.join");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.Button");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.Grid");
dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.modules._join.Form");
dojo.require("dojox.string.sprintf");
dojo.require("dojo.window");
dojo.require("dijit.layout.StackContainer");
dojo.require("dijit.layout.BorderContainer");
dojo.require("umc.modules.lib.server");

// Inheriting from umc.widgets.TabbedModule so any pages being added
// will become tabs automatically.
dojo.declare("umc.modules.join", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_page:				null,			// umc.widgets.Page
	_titlePane:			null,			// umc.widgets.ExpandingTitlePane
//	_split:				null,			// dijit.layout.BorderContainer
	_grid:				null,			// umc.widgets.Grid

	_logpane:			null,			// container that gives scrollability to _logtext
	_logtext:			null,			// text widget that holds log
	_logbottom:			null,			// empty element to which we can scroll to
	_b_show:			null,			// button to show log
	_b_hide:			null,			// button to hide log
	_b_full:			null,			// button to extend log to show all lines
	_logcount_default:	20,				// default line count for log view 
	_logcount:			20,				// current line count (0 = unlimited)
	_refresh_time:		1000,			// period [ms] of refresh
	_log_stamp:			0,				// Unix timestamp of the join.log as we've read it
	_refresh_job:		null,			// if defined: job that refreshes the log view
	_proto_gen:			0,				// simply to show the refresh

	_joined:			null,			// remember last joined status

	_footer:			null,			// redefined footer container...
	_footers:			null,			// ... and its content cells
	_multi_action:		null,			// ... and its multi-action button

	_polling_job:		null,			// polling for grid refresh while scripts are running
	_job_running:		false,			// true while scripts are running
	_polling_time:		1000,			// once per second

	_grid_query:		{'*': '*'},		// all?

	idProperty:			'script',		// doesn't help with the sorting problem of selected rows
	i18nClass: 			'umc.modules.join',
	standbyOpacity:		1,

	// all functions that deal with the log view pane. Code arg determines what to do:
	_switch_view: function(code) {
		var lastSelectedChild = this._stackContainer.selectedChildWidget;
		if (code == 'grid')
		{
			// show the grid
			this._stackContainer.selectChild(this._grid);

			// stop the loops
			this._refresh_log(false);
			this._job_polling_loop(false);
		}
		else if (code == 'log')
		{
			// show the log view without the closing button
			this._b_hide.set('disabled', true);
			this._stackContainer.selectChild(this._logpane);

			// by default show only the last N lines of the log
			if (lastSelectedChild != this._logpane) {
				this._logcount = this._logcount_default; 
			}

			// start the loops
			this._refresh_log(true);
			this._job_polling_loop();
		}
		else if (code == 'log_finished')
		{
			// show the log view with the closing button
			this._b_hide.set('disabled', false);
			this._stackContainer.selectChild(this._logpane);

			// stop the loops
			this._refresh_log(false);
			this._job_polling_loop(false);
		}
		else if (code == 'join_form')
		{
			// show the join form (on an unjoined system)
			this._stackContainer.selectChild(this._joinpane);

			// stop the loops
			this._refresh_log(false);
			this._job_polling_loop(false);
		}

		// update the layout if view changed
		if (lastSelectedChild != this._stackContainer.selectedChildWidget) {
			this.layout();
			this._reload_grid();		// redo the status query for the grid, effectively triggering
										// _check_grid_status() on 'fetchComplete'
		}
	},

	_setTitle: function(joinDate) {
		if (joinDate) {
			this._titlePane.set('title', this._("Current status: System joined on %s", joinDate));
		}
		else {
			this._titlePane.set('title', this._("Current status: System has not been joined yet"));
		}
	},

	// gets the current join status and switches display mode if needed.
	_check_join_status: function() {
		this.standby(true);
		this.umcpCommand('join/joined').then(dojo.hitch(this, function(data) {
			// update view
			var result = data.result;
			this._setTitle(result);
			if (result) {
				// show grid with join status, else....
				this._switch_view('grid');
				if (result != this._joined) {
					this._reload_grid();		// force grid reload
				}
			}
			else {
				// show affordance to join, nothing more.
				this._switch_view('join_form');
			}

			// save curent value
			this._joined = result;
			this.standby(false);
		}), dojo.hitch(this, function(result) {
			console.error("check_join_status ERROR " + result.message);
			this.standby(false);
		}));
	},

	// Asynchronously invokes reload of the log lines display. Before fetching real data,
	// checks if the timestamp of log file has changed. Use 'force=true' to override
	// the timestamp check.  Use 'force=false' to stop the refresh loop.
	_refresh_log: function(force) {
		if (force === true)
		{
			this._fetch_log_text();
		}
		else if (force === false) {
			// force the refreshing log loop to stop
			if (this._refresh_job) {
				this._refresh_job.cancel();
				this._refresh_job = null;
			}
		}
		else
		{
			this.umcpCommand('join/logview',{
				count: -1			// returns timestamp of log file
			}).then(dojo.hitch(this,function(data) {
				var result = data.result;
				if (result != this._log_stamp)
				{
					this._log_stamp = result;	// yes I know, I should do that after it was reloaded
					this._fetch_log_text();
					}
				else
				{
					// ... if there was nothing to read -> restart the refresh timer immediately.
					this._renew_refresh_job();
				}
			}));
		}
	},

	// fetches join log text. This function doesn't care about changedness,
	// it's the function being invoked if either 'force' is set or the
	// log really changed.
	_fetch_log_text: function() {
		// now really fetch log file contents.
		this.umcpCommand('join/logview',{
			count:	this._logcount
		}).then(dojo.hitch(this,function(data) {
			var result = data.result;
			var txt = dojox.string.sprintf("<u><b>%s</b></u><br/>\n",this._("Join Protocol"));

			if (this._logcount)
			{
				var tmp = this._("last {logcount} lines");
				txt = txt + dojox.string.sprintf("(%s)<br/>&nbsp;...<br/>\n",
						dojo.replace(tmp,{logcount: this._logcount}));
			}
			for (var line in result)
			{
				txt = txt + dojox.string.sprintf("%s<br/>\n",result[line]);
			}
			this._logtext.set('content',txt);
			if (this._logbottom) {
			dojo.window.scrollIntoView(this._logbottom.domNode);
			}
			else {
				console.error('no logfooter');
			}

			// if we had something to read -> restart the refresh timer AFTER we
			// have read everything
			this._renew_refresh_job();

		}));
	},

	// re-establishes a refresh job after a predefined time.
	_renew_refresh_job: function() {
		// Establish refresh every second. We keep the last instance of our 'Deferred'
		// as an instance member this._refresh_job, thus avoiding to have more than one
		// refresh running at any time.
		if (!this._refresh_job)
		{
	        var deferred = new dojo.Deferred();
	        this._refresh_job = deferred;
	        setTimeout(dojo.hitch(this, function() {
	        	if (this._refresh_job)
	        	{
	            	this._refresh_job.callback({
	            		called: true
	            	});
	        	}
	        }),
	        this._refresh_time);
	        deferred.then(dojo.hitch(this,function() {
	        	this._refresh_job = null;		// this job has fired.
	            this._refresh_log();
	        }));
		}
	},

	// triggers a grid reload. Should be called from the 'then' handler
	// of any 'run' invocation. Rebuilding the whole grid status (by calling
	// this._check_grid_status() ) will be done automatically in the 'onFetchComplete'
	// event of the store.
	_reload_grid: function() {
		this._grid._grid.filter(this._grid_query);
	},

	// This function establishes and refreshes a polling loop that will
	// run as long as one of the join job functions run (or precisely:
	// as long as the umcp query 'running' returns true).
	//
	// At the end of the loop, the function calls the functions that refresh
	// the display according to the new status.
	//
	// pass the parameter on=false in order to force the loop to stop.
	_job_polling_loop: function(on) {
		if (on === false) {
			if (this._polling_job) {
				this._polling_job.cancel();
				this._polling_job = null;
			}
			return;
		}

		// We should have exactly one such job. If one is underway, we don't
		// step on its feet. Otherwise, we start a new one.
		if (!this._polling_job)
		{
			// this query returns false as soon as the scripts are finished, and this
			// will avoid scheduling any new polling cycle.
			var umcpDeferred = this.umcpCommand('join/running').then(dojo.hitch(this, function(data) {
				try
				{
					this._job_running = data.result;
					if (!this._job_running) {
						this._joinform.standby(false);
						this._switch_view('log_finished');
					}
					else {
						this._switch_view('log');
					}
				}
				catch(error)
				{
					console.error('job_polling_loop ERROR: ' + error.message);
				}
			}),
			dojo.hitch(this, function(result) {
				this._joinform.standby(false);
				this._grid.standby(false);
				this._switch_view('grid');
			}));

			var deferred = new dojo.Deferred();
			this._polling_job = deferred;
			deferred.then(dojo.hitch(this,function() {
				this._polling_job = null;		// this job has fired.
				this._job_polling_loop();		// go on to next loop
			}));

			// set timeout to trigger refesh
			umcpDeferred.then(dojo.hitch(this, function() {
				setTimeout(dojo.hitch(this, function() {
					if (this._polling_job)
					{
						this._polling_job.resolve();
					}
				}), this._polling_time);
			}));
		}
	},

	// Seperate function that iterates over all rows of the grid and
	// updates any dependent things:
	//
	//	-	counts runnable rows
	//	-	shows or hides a '[run all]' action button if count is != 0
	//	-	shows or hides a '[run selected]' action button if some are selected
	_check_grid_status: function() {
		try
		{
			var runnable = 0;
			var selected = 0;
			this._runnables = [];
			var dup = {};

			for (var rowIndex=0; rowIndex < this._grid._grid.attr("rowCount"); rowIndex++)
			{
				var row = this._grid.getRowValues(rowIndex);

				// check against bug that duplicates data starting from the 26th row
				var fn = row['script'];
				if (typeof(dup[fn]) != 'undefined')
				{
					this._reload_grid();
					return;
				}
				dup[fn] = 1;

				var allow = false;
				if (row['action'] !== '')
				{
					runnable++;
					allow = true;
					this._runnables.push(row['script']);
				}
				if (this._grid._grid.selection.selected[rowIndex])
				{
					if (allow)
					{
						selected++;
					}
					else
					{
						// Work around bug in the Grid base class: the 'select all' checkbox
						// happily selects all rows, even if some of them are disabled!
						this._grid._grid.rowSelectCell.toggleRow(rowIndex, false);
					}
				}
				this._grid._grid.rowSelectCell.setDisabled(rowIndex, ! allow);

			}
			if (selected)
			{
				var txt = (selected==1)?
						this._('1 script selected'):
						this._('%d scripts selected',selected);
				this._footers[0].set('content',txt);
				this._multi_action.set('label',this._('run selected scripts'));
				this._footers[1].addChild(this._multi_action);
			}
			else
			{
				if (runnable)
				{
					var due = this._('%d scripts are due to be run.',runnable);
					if (runnable == 1)
					{
						due = this._("One script is due to be run.");
					}
					this._footers[0].set('content',due);

					this._multi_action.set('label',this._('run all'));
					this._footers[1].addChild(this._multi_action);
				}
				else
				{
					this._footers[0].set('content',this._('Join status ok, nothing to do.'));
					this._footers[1].removeChild(this._multi_action);
				}
			}
		}
		catch(error)
		{
			console.error("check grid status: " + error.message);
		}
	},

	// trigger the join procedure
	_run_join: function() {
		this._joinform.standby(true);
		var pass = this._joinform._widgets['pass'].get('value');
		this._joinform._widgets['pass'].set('value', '');
		this.umcpCommand('join/join',{
			host: this._joinform._widgets['host'].get('value'),
			user: this._joinform._widgets['user'].get('value'),
			pass: pass
		}).then(dojo.hitch(this, function(data) {
			if (data.result.msg) {
				this._joinform.standby(false);
				// Note result is already localized
				umc.dialog.alert(this._("Can't start join process:<br>") + data.result.msg, data.result.title);
				this._setTitle(false);
				this._check_join_status();
			}
			else
			{
				// Job is started. Now wait for its completion.
				this._switch_view('log');
			}
		}));
	},

	// Asynchronously runs the selected script(s).
	//
	_run_scripts: function(credentials, list) {
		// set the grid unclickable
		this._grid.standby(true);

		// if list is none: it is called from our 'run all' button. Depending on the dialog state,
		// we have to get the list from different places:
		//  (1) something is selected -> use the grid's selected IDs
		//	(2) nothing selected -> use our 'runnables' array as we've read it in _check_grid_status()

		if ((list === null) || (list === undefined))
		{
			list = this._grid.getSelectedIDs();
			if (list.length === 0)
			{
				list = this._runnables;
			}
		}

		if ((list !== null) && (list !== undefined) && (list.length > 0))
		{
			var values = { scripts: list };
			if (credentials.username) {
				values.username = credentials.username;
			}
			if (credentials.password) {
				values.password = credentials.password;
			}

			this.umcpCommand('join/run', values).then(dojo.hitch(this, function(data) {
				if (data.result.msg) {
					// Note result is already localized
					umc.dialog.alert(this._("Can't start join script:<br>%s", data.result.msg), this._('Error'));
					this._grid.standby(false);
					this._check_grid_status();		// sets meaningful messages
					this._check_join_status();
				}
				else
				{
					// Job is started. Now wait for its completion.
					this._switch_view('log');
				}
			}));
		}

	},

	buildRendering: function() {
		this.inherited(arguments);
		this.standby(true);

		this._page = new umc.widgets.Page({
			headerText:		this._("Join status"),
			helpText:		this._("This page shows the status of all available join scripts on this system, along with all join-related actions (run selected or all join scripts, or join the system as a whole)")
		});

		// Title pane without rollup/down
		this._titlePane = new umc.widgets.ExpandingTitlePane({
			title:			this._("Current status")
		});
		this._page.addChild(this._titlePane);

		// add StackContainer as center element to the TitlePane in order to
		// switch between the different layers
		this._stackContainer = new dijit.layout.StackContainer({
			region: 'center'
		});
		this._titlePane.addChild(this._stackContainer);

		// Trying to give the user a chance to resize the grid <-> logview ratio.
		// Even a simple BorderContainer is able to do that: just give some of its
		// children a 'splitter: true' property.

		this._grid = new umc.widgets.Grid({
			region:			'center',
			moduleStore:	umc.store.getModuleStore('script','join/scripts'),
			// query:			this._grid_query,		// why?
			actions:
			[
	         	{
	                name:				'run',
	                label:				this._( 'Execute' ),
	                description:		this._( 'Execute this join script' ),
	                isContextAction:	true,
	                isStandardAction:	true,
	            	canExecute: dojo.hitch(this, function(values) {
	            		// Knowledge is in the Python module!
	            		return (values['action'] !== '');
	            	}),
	                callback: dojo.hitch(this, function(id) {
	            		if (dojo.isArray(id))
	            		{
	            			id = id[0];
	            		}
						umc.tools.ucr('server/role').then( dojo.hitch( this, function(ucrValues) {
							if (ucrValues['server/role'] == 'domaincontroller_master') {
								this._run_scripts({}, [id]);
							} else {
								this._get_credentials().then( dojo.hitch( this, function(credentials) {
	                				this._run_scripts(credentials, [id]);
								}));
							}
						}));
	                })
	            }
			],
			columns:
			[
				{
					name:			'script',
					label:			this._("Script (package)"),
					description:	this._("Script name (the same as the package it belongs to)"),
					editable:		false
//					width:			'50%'
				},
				{
					name:			'current',
					label:			this._("Current<br/>version"),
					description:	this._("Latest script version ready for execution"),
					editable:		false,
					width:			'adjust'
				},
				{
					name:			'last',
					label:			this._("Last<br/>version"),
					description:	this._("Latest script version that was executed successfully"),
					editable:		false,
					width:			'adjust'
				},
				// Status column. Currently only text.
				{
					name:			'status',
					label:			this._("State"),
					description:	this._("Status of this package"),
					editable:		false,
					width:			'14%'
				}
			]
		});
		this._stackContainer.addChild(this._grid);

		// -------------------- Modifications to Grid ----------------------

		// These modifications should better be done in the argument list
		// passed to the umc.widgets.Grid constructor, but currently that
		// class isn't prepared to handle them. So we first construct our
		// grid instance, and then we replace some of its properties.
		//
		// limit sortability to '1st col, ascending', so the selection sort
		// problem of the grid doesn't hit us. Sorting the 1st column
		// ascending must remain allowed since the umc.widgets.Grid does
		// an unconditional sort on first data load.
		this._grid._grid.canSort = function(col) {
			return (col == 1);
		};

		// the predefined footer structure (that adopts column widths of data cols with actions
		// into columns of footer cells) doesn't make sense here. We let all the callbacks
		// intact that try to update the footer, but we detach it from the grid so it's
		// not visible anymore.
		this._grid.removeChild(this._grid._footer);

		// Now we can add a different layout container here: a 2x1 table with adjacent
		// left- and right-aligned cells. CSS class is copied from the base class.
		this._footer = new dojox.layout.TableContainer({
			region:				'bottom',
			cols:				2,
			style:				'width:100%;',
			'class':			this._grid._footer['class'],
			showLabels:			false
		});
		this._grid.addChild(this._footer);
		this._footers =
		[
		 	// a text widget for the textual message
		 	new umc.widgets.Text({
		 		content:		'&nbsp;',
		 		style:			'text-align:left;'
		 	}),
		 	// a container that will get the multi-action button
		 	new umc.widgets.ContainerWidget({
		 		style:			'text-align:right;'
		 	})
		];
		this._multi_action = new umc.widgets.Button({
			// FIXME Style this button according to Univention guidelines
			//'class':	'umcSubmitButton',
			onClick:	dojo.hitch(this, function() {
				umc.tools.ucr('server/role').then( dojo.hitch( this, function(ucrValues) {
					if (ucrValues['server/role'] == 'domaincontroller_master') {
						this._run_scripts({});
					} else {
						this._get_credentials().then( dojo.hitch( this, function(credentials) {
							// _run_scripts without second arg: will be filled there with either the selected or all runnable scripts.
							this._run_scripts(credentials);
						}));
					}
				}));
			})
		});
		for (var i=0; i<this._footers.length; i++)
		{
			this._footer.addChild(this._footers[i]);
		}

		// our 'selection changed' handler will set the message and button label
		// according to the current status.
		dojo.connect(this._grid._grid,"onSelectionChanged",dojo.hitch(this, function() {
			this._check_grid_status();
		}));
        // Status of the grid has to be recalculated whenever a data fetch has completed,
		// be it successfully or not.
        this.connect(this._grid._grid, "_onFetchComplete", dojo.hitch(this, function() {
            this._check_grid_status();
        }));
        this.connect(this._grid._grid, "_onFetchError", dojo.hitch(this, function() {
            this._check_grid_status();
        }));

		// ---------------- END modifications to Grid ----------------------

		this._logpane = new dijit.layout.BorderContainer({
			gutters: false
		});
		this._stackContainer.addChild(this._logpane);

		// temporary container for scrolling to the bottom
		var logContainer = new umc.widgets.ContainerWidget({
			region:			'center',
			scrollable:		true
		});
		this._logpane.addChild(logContainer);

		// FIXME use a generic CSS class that requests a specific monospaced font
		this._logtext = new umc.widgets.Text({
			region:			'center',
			content:		this._('... loading log ...'),
			style:			'font-family:monospace;'
		});
		logContainer.addChild(this._logtext);

		// this element allows us to scroll to the bottom of the log
		this._logbottom = new umc.widgets.Text({});
		logContainer.addChild(this._logbottom);

		// seperate right-aligned widget below the SplitPane, simply to contain
		// the button(s) to show/hide the log view
		this._logbuttons = new umc.widgets.ContainerWidget({
			region:		'bottom',
			style:		'text-align: right;'
		});
		this._logpane.addChild(this._logbuttons);
		/*this._b_show = new umc.widgets.Button({
			label:		this._('show log'),
			onClick:	dojo.hitch(this, function() {
				this._switch_view('show');
			})
		});
		this._logbuttons.addChild(this._b_show);
		*/

		this._b_hide = new umc.widgets.Button({
			label:		this._('Close log'),
			disabled:	true,
			'class': 'umcSubmitButton',
			onClick:	dojo.hitch(this, function() {
				var msg = this._('A restart of the UMC server components may be necessary for changes to take effect.');
				if (this._joined) {
					// show a different message for initial join
					msg = this._('A restart of the UMC server components is necessary after an initial join.');
				}
				umc.modules.lib.server.askRestart(msg).then(
					function() { /* nothing to do */ },
					dojo.hitch(this, function() {
						// user canceled -> change the current view
						this._check_join_status();
					}
				));
			})
		});
		this._logbuttons.addChild(this._b_hide);

		this._b_full = new umc.widgets.Button({
			label:		this._('Show full log'),
    		onClick:	dojo.hitch(this, function() {
				this._logcount = 0;
				this._refresh_log(true);
    		})
		});
		this._logbuttons.addChild(this._b_full);

// --------------- DEBUG BUTTONS ------------------
//		this._logbuttons.addChild(new umc.widgets.Button({
//			label:	'[reload grid]',
//			onClick:	dojo.hitch(this, function() {
//				this._reload_grid();
//			})
//		}));
//		this._logbuttons.addChild(new umc.widgets.Button({
//			label:	'[check join status]',
//			onClick:	dojo.hitch(this, function() {
//				this._check_join_status();
//			})
//		}));
//		this._logbuttons.addChild(new umc.widgets.Button({
//			label:	'[check grid status]',
//			onClick:	dojo.hitch(this, function() {
//				this._check_grid_status();
//			})
//		}));
// ------------ END DEBUG BUTTONS ---------------

		// The standard view is the grid with all join scripts. There's a different view
		// meant for a system that has not been joined yet: a form for entering an admin
		// password and for starting the join process. This form is prepared here and stored
		// into the this._joinpane variable. The _check_join_status() method will decide
		// which view is to show.
		this._joinpane = new umc.widgets.ContainerWidget({
			region:				'center',
			scrollable:			true
		});
		this._stackContainer.addChild(this._joinpane);
		var buttons = 
		[
			{
				name:			'submit',
				label:			this._("Start Join"),
				callback:		dojo.hitch(this, '_run_join')
			}
		];
		var widgets =
		[
			{
				type:			'Text',
				name:			'text',
				style:			'margin-top:1em;margin-bottom:1em;',
				content:		this._("Please enter the required information below and click the 'Start Join' button. This will join your system into the domain.")
			},
			{
				type:			'TextBox',
				name:			'host',
				value:			'',
				label:			this._('Hostname of domain controller master'),
				description:	this._('The hostname of the domain controller master of the domain')
			},
			{
				type:			'TextBox',
				name:			'user',
				value:			'Administrator',
				label:			this._('Username'),
				description:	this._('The username of the domain administrator')
			},
			{
				type:		'PasswordBox',
				name:		'pass',
				value:		'',
				label: this._( 'Password' ),
				description: this._( 'Password of the domain administrator' )
			}
		];
		this._joinform = new umc.modules._join.Form({
			buttons:	buttons,
			widgets:	widgets
		});
		this._joinpane.addChild(this._joinform);

		// add the prepared page to the module widget
		this.addChild(this._page);

		// all display elements exist, now check the curren status:
		// -> job running
		// -> joined
		// -> unjoined
		(new dojo.DeferredList([
			this.umcpCommand('join/joined'),
			this.umcpCommand('join/running')
		])).then(dojo.hitch(this, function(results) {
			// result[i]: [ 0 ] -> success/failure, [ 1 ] -> data
			this._joined = results[0][0] ? results[0][1].result : false;
			this._job_running = results[1][0] ? results[1][1].result : false;
			this.standby(false);
			this.standbyOpacity = 0.75;  // set it back to semi transparent
			this._setTitle(this._joined);  // update TitlePane title
			if (this._job_running) {
				this._switch_view('log');
			}
			else if (!this._joined) {
				this._switch_view('join_form');
			}
			else {
				// grid view is selected by default... refresh the grid
				this._reload_grid();
			}
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	_get_credentials: function() {
		var msg = this._('<p>Please enter username and password of a Domain Administrator to run the selected join scripts and click the <i>Run</i> button.</p>'); 
		var deferred = new dojo.Deferred();
		var dialog = null;
		var form = new umc.widgets.Form({
			widgets: [{
				name: 'text',
				type: 'Text',
				content: msg
			}, {
				name: 'username',
				type: 'TextBox',
				label: this._('Username'),
				value: ''
			}, {
				name: 'password',
				type: 'PasswordBox',
				label: this._('Password')
			}],
			buttons: [{
				name: 'cancel',
				label: this._('Cancel'),
				callback: dojo.hitch(this, function() {
					deferred.reject();
					this.standby(false);
					dialog.hide();
					dialog.destroyRecursive();
					form.destroyRecursive();
				})
			},{
				name: 'submit',
				label: this._('Run'),
				callback: dojo.hitch(this, function() {
					if (form.getWidget('password').get('value').length === 0) {
						umc.dialog.alert( this._('The password may not be empty.'), this._('Password invalid') );
					} else {
						this.standby(false);
						deferred.resolve({
							username: form.getWidget('username').get('value'),
							password: form.getWidget('password').get('value')
						});
						form.getWidget('password').set('value', '');
						dialog.hide();
						dialog.destroyRecursive();
						form.destroyRecursive();
					}
				})
			}],
			layout: [ 'text', 'username', 'password' ]
		});
		dialog = new dijit.Dialog({
			title: this._('Run join scripts'),
			content: form,
			style: 'max-width: 400px;'
		});
		this.connect(dialog, 'onHide', function() {
			if (deferred.fired < 0) {
				// user clicked the close button
				this.standby(false);
				deferred.reject();
			}
		});
		dialog.show();
		return deferred;
	},

	uninitialize: function() {
		this.inherited(arguments);
		this._refresh_log(false);
		this._job_polling_loop(false);
	}
});
