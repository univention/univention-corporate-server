/*global console MyError dojo dojox dijit umc */

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

// Inheriting from umc.widgets.TabbedModule so any pages being added
// will become tabs automatically.
dojo.declare("umc.modules.join", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_page:				null,			// umc.widgets.Page
	_content:			null,			// umc.widgets.ExpandingTitlePane
//	_split:				null,			// dijit.layout.BorderContainer
	_grid:				null,			// umc.widgets.Grid
	_infotext:			null,
	
	_logview:			null,			// container that gives scrollability to _logtext
	_logtext:			null,			// text widget that holds log
	_b_show:			null,			// button to show log
	_b_hide:			null,			// button to hide log
	_b_full:			null,			// button to extend log to show all lines
	_logcount_default:	15,				// default line count for log view 
	_logcount:			15,				// current line count (0 = unlimited)
	_refresh_time:		1000,			// period [ms] of refresh
	_log_stamp:			0,				// Unix timestamp of the join.log as we've read it
	_refresh_job:		null,			// if defined: job that refreshes the log view
	_proto_gen:			0,				// simply to show the refresh
	
	_joined:			'not set',		// remember last joined status
	
	_footer:			null,			// redefined footer container...
	_footers:			null,			// ... and its content cells
	_multi_action:		null,			// ... and its multi-action button
	
	_polling_job:		null,			// polling for grid refresh while scripts are running
	_job_running:		false,			// true while scripts are running
	_polling_time:		1000,			// once per second
	
	_grid_query:		{'*': '*'},		// all?
	
	idProperty:			'script',		// doesn't help with the sorting problem of selected rows
	i18nClass: 			'umc.modules.join',
	
	// all functions that deal with the log view pane. Code arg determines what to do:
	//  'hide' ... switch display off
	//	'show' ... switch display on, show last '_logcount_default' lines
	//	'full' .... (display is already on) show all log lines
	_switch_log_display: function(code) {
		if (code == 'hide')
		{
			this._content.removeChild(this._logview);
			this._bottom.addChild(this._b_show);
			this._bottom.removeChild(this._b_hide);
			this._bottom.removeChild(this._b_full);
			
			// stop refresh job
			if (this._refresh_job)
			{
				this._refresh_job.cancel();
				this._refresh_job = null;
			}
		}
		else
		{
			if (code == 'full')
			{
				this._logcount = 0;
				this._refresh_log(true);
				this._bottom.removeChild(this._b_full);
			}
			else
			{
				this._logcount = this._logcount_default;
				this._refresh_log(true);
				this._bottom.addChild(this._b_hide);
				this._bottom.addChild(this._b_full);
				this._content.addChild(this._logview);
				this._logview.addChild(this._logtext);
			}

			this._bottom.removeChild(this._b_show);
		}
	},
	
	// gets the current join status and switches display mode if needed.
	_check_join_status: function() {
		this.umcpCommand('join/joined').then(dojo.hitch(this, function(data) {
			var result = data.result;
			if (result != this._joined)
			{
				this._joined = result;
				if (result)
				{
					// show grid with join status, else....
					this._infotext.set('content',this._("This system joined on %s",result));
					this._content.removeChild(this._joinpane);
					this._content.addChild(this._grid);
					this._reload_grid();		// force grid reload
				}
				else
				{
					// show affordance to join, nothing more.
					this._infotext.set('content',this._("This system has not been joined yet."));
					this._content.removeChild(this._grid);
					this._content.addChild(this._joinpane);
				}
			}
		}),
		dojo.hitch(this, function(result) {
			console.error("check_join_status ERROR " + result.message);
		})
		);
	},
	
	// Asynchronously invokes reload of the log lines display. Before fetching real data,
	// checks if the timestamp of log file has changed. Use 'force=true' to override
	// the timestamp check.
	_refresh_log: function(force) {
		if (force)
		{
			this._fetch_log_text();
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
		//
		// Added here: if this._refresh_time is set to zero we stop the timer.
		if ((! this._refresh_job) && (this._refresh_time))
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
	_job_polling_loop: function(on) {
		
		// 'on' arg is for starting and stopping
		if (typeof(on) != 'undefined')
		{
			this._job_running = on;
		}

		// If in the meantime the callback has set _job_running to FALSE
		// the function will do nothing, effectively stopping the loop.
		if (this._job_running)
		{
			// this query returns false as soon as the scripts are finished, and this
			// will avoid scheduling any new polling cycle.
			this.umcpCommand('join/running').then(dojo.hitch(this, function(data) {
				try
				{
					var result = data.result;
					if (result != this._job_running)
					{
						this._job_running = result;
						if (! result)
						{
							this._joinform.standby(false);
						}
						this._check_join_status();	// switch between join form and script grid
						this._reload_grid();		// redo the status query for the grid, effectively triggering
													// _check_grid_status() on 'fetchComplete'
					}
					// for first display: if none of the two widgets (script grid or join form)
					// is displayed AND we run into a running job we have to do two things:
					//  (1) show a header text that explains the situation
					//	(2) switch log display on.
					if (this._job_running)
					{
						var txt = this._infotext.get('content');
						if (txt == '')
						{
							this._infotext.set('content',this._("Currently some join scripts are running. You may watch the log file until they are finished."));
							this._switch_log_display('show');
						}
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
			})
			);

			// We should have exactly one such job. If one is underway, we don't
			// step on its feet. Otherwise, we start a new one.
			if (this._polling_job == null)
			{
		        var deferred = new dojo.Deferred();
		        this._polling_job = deferred;
		        setTimeout(dojo.hitch(this, function() {
		        	if (this._polling_job)
		        	{
		            	this._polling_job.callback({
		            		called: true
		            	});
		        	}
		        }),
		        this._polling_time);
		        deferred.then(dojo.hitch(this,function() {
		        	this._polling_job = null;		// this job has fired.
		        	this._job_polling_loop();		// go on to next loop
		        }));
			}
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
		
			// While a job is running the grid is in standby() nevertheless, so it won't
			// make sense to refresh it.
			if (this._job_running)
			{
				return;
			}
					
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
				if (row['action'] != '')
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
	
	// Asynchronously runs the selected script(s).
	//
	_run_scripts: function(list) {
		// switch the log pane visible; this will establish a refresh too.
		this._switch_log_display('show');
		
		// set the grid unclickable
		this._grid.standby(true);
		
		// if list is none: it is called from our 'run all' button. Depending on the dialog state,
		// we have to get the list from different places:
		//  (1) something is selected -> use the grid's selected IDs
		//	(2) nothing selected -> use our 'runnables' array as we've read it in _check_grid_status()
		
		if (list == null)
		{
			list = this._grid.getSelectedIDs();
			if (list.length == 0)
			{
				list = this._runnables;
			}
		}
		
		if ((list != null) && (list.length != 0))
		{
        	this._job_running = true;

        	if (list.length == 1)
        	{
        		this._footers[0].set('content',this._("One join script is currently running"));
        	}
        	else
        	{
        		this._footers[0].set('content',this._('%d join scripts are currently running',list.length));
        	}
			this._footers[1].removeChild(this._multi_action);
		
	        this.umcpCommand('join/run',{scripts: list}).then(dojo.hitch(this, function(data) {
	        	var result = dojo.getObject('result', false, data);
	        	if (result != '')
	        	{
	        		// Note result is already localized
	        		umc.dialog.alert(this._("Can't start join: ") + result);
		        	this._check_join_status();		// sets meaningful messages
	        	}
	        	else
	        	{
	        		// Job is started. Now wait for its completion.
	        		this._job_polling_loop(true);
	        	}
	        }));
		}

	},

	buildRendering: function() {
		this.inherited(arguments);
			
		this._page = new umc.widgets.Page({
			headerText:		this._("Join status"),
			helpText:		this._("This page shows the status of all available join scripts on this system, along with all join-related actions (run selected or all join scripts, or join the system as a whole)")
		});
		this.addChild(this._page);

		// Title pane without rollup/down
		this._content = new umc.widgets.ExpandingTitlePane({
			title:			this._("Current status")
		});
		this._page.addChild(this._content);
		
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
	            		return (values['action'] != '');
	            	}),
	                callback: dojo.hitch(this, function(id) {
	            		if (dojo.isArray(id))
	            		{
	            			id = id[0];
	            		}
	                	this._run_scripts([id]);
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
				this._run_scripts();		// without arg: will be filled there with either
											// the selected or all runnable scripts.
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

		this._logview = new umc.widgets.ContainerWidget({
			region:			'bottom',
			scrollable:		true,
			splitter:		true,
			style:			'height:45%;'	// should initially occupy 45% of pane height
		});
		// FIXME Does Univention have a style guide that requests a specific monospaced font?
		this._logtext = new umc.widgets.Text({
			scrollable:		true,
			content:		this._('... loading log ...'),
			style:			'font-family:monospace;'
		});
		
		// seperate right-aligned widget below the SplitPane, simply to contain
		// the button(s) to show/hide the log view
		this._bottom = new umc.widgets.ContainerWidget({
			region:		'bottom',
			style:		'text-align: right;'
		});
		this._content.addChild(this._bottom);
		this._b_show = new umc.widgets.Button({
			label:		this._('show log'),
			onClick:	dojo.hitch(this, function() {
				this._switch_log_display('show');
			})
		});
		this._bottom.addChild(this._b_show);
		
		this._b_hide = new umc.widgets.Button({
			label:		this._('hide log'),
			onClick:	dojo.hitch(this, function() {
				this._switch_log_display('hide');
			})
		});
		
		this._b_full = new umc.widgets.Button({
			label:		this._('show all'),
    		onClick:	dojo.hitch(this, function() {
				this._switch_log_display('full');
    		})
		});

// --------------- DEBUG BUTTONS ------------------
//		this._bottom.addChild(new umc.widgets.Button({
//			label:	'[reload grid]',
//			onClick:	dojo.hitch(this, function() {
//				this._reload_grid();
//			})
//		}));
//		this._bottom.addChild(new umc.widgets.Button({
//			label:	'[check join status]',
//			onClick:	dojo.hitch(this, function() {
//				this._check_join_status();
//			})
//		}));
//		this._bottom.addChild(new umc.widgets.Button({
//			label:	'[check grid status]',
//			onClick:	dojo.hitch(this, function() {
//				this._check_grid_status();
//			})
//		}));
// ------------ END DEBUG BUTTONS ---------------
		
		// We can't change the 'title' property of an ExpandingTitlePane after we've created it...
		// so we write the (variable) status info into the 'top' component of the BorderContainer.
		var info = new umc.widgets.ContainerWidget({
			region:			'top',
			scrollable:		false,
			style:			'border:none;'
		});
		this._content.addChild(info);
		
		this._infotext = new umc.widgets.Text({
			style:			'border:none;margin:.2em;',
			content:		''
		});
		info.addChild(this._infotext);
		
		// The standard view is the grid with all join scripts. There's a different view
		// meant for a system that has not been joined yet: a form for entering an admin
		// password and for starting the join process. This form is prepared here and stored
		// into the this._joinpane variable. The _check_join_status() method will decide
		// which view is to show.
		this._joinpane = new umc.widgets.ContainerWidget({
			region:				'center',
			scrollable:			true
		});
		var buttons = 
		[
			{
				type:			'submit',
				'default':		true,
				label:			this._("Start Join"),
				onClick:		dojo.hitch(this, function() {
					this._joinform.standby(true);
					this._switch_log_display('show');
			        this.umcpCommand('join/join',{
						host: this._joinform._widgets['host'].value,
						user: this._joinform._widgets['user'].value,
						pass: this._joinform._widgets['pass'].value				        	
			        }).then(dojo.hitch(this, function(data) {
			        	var result = dojo.getObject('result', false, data);
			        	if (result != '')
			        	{
			        		this._joinform.standby(false);
			        		// Note result is already localized
			        		umc.dialog.alert(this._("Can't start join: ") + result);
				        	this._check_join_status();		// sets meaningful messages
			        	}
			        	else
			        	{
			        		// Job is started. Now wait for its completion.
			        		this._job_polling_loop(true);
			        	}
			        }));
				})
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
				label:			this._('DC Hostname'),
				description:	this._('The hostname of the DC Master of the domain')
			},
			{
				type:			'TextBox',
				name:			'user',
				value:			'Administrator',
				label:			this._('Username'),
				description:	this._('The username of the Domain Administrator')
			},
			{
				type:		'PasswordBox',
				name:		'pass',
				value:		'',
				label: this._( 'Password' ),
				description: this._( 'Password of the Domain Administrator' )
			}
		];
		this._joinform = new umc.modules._join.Form({
			buttons:	buttons,
			widgets:	widgets
		});
		this._joinpane.addChild(this._joinform);
	},
	
	startup: function() {
		
		this.inherited(arguments);

		// All display elements exist. Now we check what we have to display.
		// This is done by checking once for a running job (at the Python side)
		// and setting the display accordingly. The polling loop itself will then
		// establish triggers that change display if the current job is finished.
		this._job_polling_loop(true);
		
	},
	
	uninitialize: function() {
		
		this.inherited(arguments);
		this._refresh_time = 0;
		
	}
	
});
