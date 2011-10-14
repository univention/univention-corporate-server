/*global console MyError dojo dojox dijit umc window */

dojo.provide("umc.modules.updater"); 

// ------------ Basics ------------------
dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.ConfirmDialog");

// ------- Overloaded classes --------
dojo.require("umc.modules._updater.Module");
dojo.require("umc.modules._updater.Page");
dojo.require("umc.modules._updater.Grid");
dojo.require("umc.modules._updater.Form");

// ------- Pages inside the module ----------
dojo.require("umc.modules._updater.UpdatesPage");
dojo.require("umc.modules._updater.ComponentsPage");
dojo.require("umc.modules._updater.DetailsPage");
dojo.require("umc.modules._updater.SettingsPage");
dojo.require("umc.modules._updater.ProgressPage");

dojo.declare("umc.modules.updater", umc.modules._updater.Module, {

	i18nClass: 			'umc.modules.updater',
	
	// some variables related to error handling
	_connection_status:	0,			// 0 ... successful or not set
									// 1 ... errors received
									// 2 ... currently authenticating
	_busy_dialog: null,		// a handle to the 'connection lost' dialog while
							// queries return with errors.
	_error_count: 0,		// how much errors in one row
	
	buildRendering: function() {

		this.inherited(arguments);
		
		this._updates = new umc.modules._updater.UpdatesPage({
			moduleStore:	umc.store.getModuleStore(null,'updater/updates')
		});
		
		this._components = new  umc.modules._updater.ComponentsPage({
			moduleStore:	umc.store.getModuleStore('name','updater/components')
		});

		this._details = new umc.modules._updater.DetailsPage({
			moduleStore:	umc.store.getModuleStore('name','updater/components')
			
		});
		
		this._settings = new umc.modules._updater.SettingsPage({
			moduleStore:	umc.store.getModuleStore('dummy','updater/settings')
		});

		this._progress = new umc.modules._updater.ProgressPage({
			// Strictly spoken, we don't need the args to this moduleStore,
			// we simply need the store itself.
			moduleStore:	umc.store.getModuleStore(null,'updater/installer')
		});
		
		this.addChild(this._updates);
		this.addChild(this._components);
		this.addChild(this._details); 
		this.addChild(this._settings);
		this.addChild(this._progress);
		
		// --------------------------------------------------------------------------
		//
		//		Connections that make the UI work (mostly tab switching)
		//
		
		// switches from 'add' or 'edit' (components grid) to the detail form
		dojo.connect(this._components,'showDetail',dojo.hitch(this, function(id) {
			this.exchangeChild(this._components,this._details);
			// if an ID is given: pass it to the detail page and let it load
			// the corresponding component record
			if (id)
			{
				this._details.startEdit(false,id);
			}
			// if ID is empty: ask the SETTINGS module for default values.
			else
			{
				this._details.startEdit(true,this._settings.getComponentDefaults());
			}
		}));
		
		// closes detail form and returns to grid view.
		dojo.connect(this._details,'closeDetail',dojo.hitch(this, function(args) {
			this.exchangeChild(this._details,this._components);
		}));
		
		// waits for the Progress Page to be closed (automatically or by a close button)
		dojo.connect(this._progress,'stopWatching',dojo.hitch(this, function(tab) {
			this.hideChild(this._progress);
			this.showChild(this._updates);
			this.showChild(this._components);
			this.showChild(this._settings);
			
			// Revert to the 'Updates' page if the installer action encountered
			// the 'reboot' affordance.
			if (! tab)
			{
				tab = this._updates;
			}
			this.selectChild(tab);
		}));
		
		// waits for the Progress Page to notify us that a job is finished. This
		// should immediately refresh the 'Updates' and 'Components' pages.
		dojo.connect(this._progress,'jobFinished',dojo.hitch(this, function() {
			this._updates.refreshPage(true);
			this._components.refreshPage();
		}));
		
		// waits for the Progress Page to notify us that a job is running
		dojo.connect(this._progress,'jobStarted',dojo.hitch(this, function() {
			this._switch_to_progress_page();
		}));

		// --------------------------------------------------------------------------
		//
		//		Connections that listen for changes and propagate
		//		them to other pages
		//
		
		// *** NOTE *** the Components Grid is able to refresh itself automatically,
		//				so we don't have to refresh it manually on any changes.
		
		// *** NOTE *** the Updates Page also has some mechanisms to refresh itself
		//				on changes that reflect themselves in the sources.list
		//				snippet files. But this refresh is intentionally slow (once
		//				in 5 secs) to avoid resource congestion. The callbacks here
		//				should immediately trigger refresh whenever something was
		//				done at the frontend UI.
		
		// listens for changes on the 'settings' tab and refreshes the 'updates' page.
		dojo.connect(this._settings,'dataChanged',dojo.hitch(this, function() {
			this._updates.refreshPage();
		}));
		
		// called whenever detail form is successfully saved. Should refresh 'Updates' page.
		dojo.connect(this._details,'dataChanged',dojo.hitch(this, function(args) {
			this._updates.refreshPage();
		}));
		
		// listens for changes on the 'components' grid (enabling/disabling) and
		// refreshes the 'Updates' page.
		dojo.connect(this._components,'dataChanged',dojo.hitch(this, function() {
			this._updates.refreshPage();
		}));
		
		// ---------------------------------------------------------------------------
		//
		//		Listens for 'query error' and 'query success' events on all attached pages
		//		and their children, delivering them to our own (central) error handler
		//
		
		var ch = this.getChildren();
		for (var obj in ch)
		{
	    	dojo.connect(ch[obj],'_query_error',dojo.hitch(this,function(subject,data) {
	    		this._query_error(subject,data);
	    	}));
	    	
	    	dojo.connect(ch[obj],'_query_success',dojo.hitch(this,function(subject) {
	    		this._query_success(subject);
	    	}));
		}
    			
		// --------------------------------------------------------------------------
		//
		//		Connections that centralize the work of the installer:
		//		listen for events that should start UniventionUpdater
		//
		
		// invokes the installer from the 'install' button (components grid)
		dojo.connect(this._components,'installComponent',dojo.hitch(this, function(name) {
			this._call_installer({
				job:		'component',
				detail:		name,
				confirm:	dojo.replace(this._("Do you really want to install the '{name}' component?"),{name: name})
			});
		}));
		
		// invokes the installer from the 'release update' button (Updates Page)
		dojo.connect(this._updates,'runReleaseUpdate',dojo.hitch(this, function(release) {
			this._call_installer({
				job:		'release',
				detail:		release,
				confirm:	dojo.replace(this._("Do you really want to install release updates up to version {release}?"),{release: release})
			});
		}));
		
		// invokes the installer from the 'errata update' button (Updates Page)
		dojo.connect(this._updates,'runErrataUpdate',dojo.hitch(this, function() {
			this._call_installer({
				job:		'errata',
				confirm:	this._("Do you really want to install all available errata updates?")
			});
		}));
		
		// invokes the installer from the 'component update' button (Updates Page)
		dojo.connect(this._updates,'runDistUpgrade',dojo.hitch(this, function() {
			this._confirm_distupgrade();
		}));
		
		// invokes the installer in easy mode
		dojo.connect(this._updates,'runEasyUpgrade',dojo.hitch(this, function() {
			this._call_installer({
				job:		'easyupgrade',
				confirm:	this._("Do you really want to upgrade your system?")
			});
		}));
		
	},
	
	// We defer these actions until the UI is readily rendered
	startup: function() {
		
		this.inherited(arguments);
		
		this.hideChild(this._details);
		this.hideChild(this._progress);
		
	},
	
	// Seperate function that can be called the same way as _call_installer:
	// instead of presenting the usual confirm dialog it presents the list
	// of packages for a distupgrade.
	_confirm_distupgrade: function() {
		
		try
		{
			this.standby(true);
			this.moduleStore.umcpCommand('updater/updates/check').then(dojo.hitch(this, function(data) {
				this.standby(false);
				// FIXME Lots of manual styling to achieve resonable look
				var txt = "<div style='overflow:scroll;max-height:400px;'<table>\n";
				var upd = data.result['update'];
				var ins = data.result['install'];
				if ((! upd.length) && (! ins.length))
				{
					this._updates.refreshPage(true);
					return;
				}
				if (upd.length)
				{
					txt += "<td colspan='2' style='padding:.5em;'><b><u>" + dojo.replace(this._("{count} packages to be updated"),{count:upd.length}) + "</u></b></td>";
					for (var i in upd)
					{
						txt += "<tr>\n";
						txt += "<td style='padding-left:1em;'>" + upd[i][0] + "</td>\n";
						txt += "<td style='padding-left:1em;padding-right:.5em;'>" + upd[i][1] + "</td>\n";
						txt += "</tr>\n";
					}
				}
				if (ins.length)
				{
					txt += "<td colspan='2' style='padding:.5em;'><b><u>" + dojo.replace(this._("{count} packages to be installed"),{count:ins.length}) + "</u></b></td>";
					for (var i in ins)
					{
						txt += "<tr>\n";
						txt += "<td style='padding-left:1em;'>" + ins[i][0] + "</td>\n";
						txt += "<td style='padding-left:1em;padding-right:.5em;'>" + ins[i][1] + "</td>\n";
						txt += "</tr>\n";
					}
				}
				txt += "</table></div>";
				txt += "<p style='padding:1em;'>" + this._("Do you really want to perform the update/install of the above packages?") + "</p>\n";
				var dia = new umc.widgets.ConfirmDialog({
					title:			this._("Start Upgrade?"),
					message:		txt,
					style:			'max-width:600px;',
					options:
					[
					 	{
					 		label:		this._('Cancel'),
					 		name:		'cancel'
					 	},
					 	{
					 		label:		this._('Start!'),
					 		name:		'start',
					 		'default':	true
					 	}
					]
				});
				
				dojo.connect(dia,'onConfirm',dojo.hitch(this, function(answer) {
					dia.close();
					if (answer == 'start')
					{
			 			this._call_installer({
			 				confirm:		false,
			 				job:			'distupgrade',
			 				detail:			''
			 			});
					}
				}));				
				dia.show();
	
				return;
			}),
			dojo.hitch(this, function(data) {
				this.standby(false);
			})
			);
		}
		catch(error)
		{
			console.error("PACKAGE DIALOG: " + error.message);
		}
	},

	// Central entry point into all installer calls. Subject
	// and detail are passed as args to the 'updater/installer/execute' backend.
	//
	// Argument 'confirm' has special meaning:
	//		true ......... ask for confirmation and run the installer only if confirmed,
	//		false ........ run the installer unconditionally.
	//		any string ... the confirmation text to ask.
	_call_installer: function(args) {
		
		if (args['confirm'])
		{
			var msg = "<h1>" + this._("Attention!") + "</h1><br/>";
			msg = msg + "<p>" +
				this._("Installing an system update is a significant change to this system and could have impact to other systems. ") +
				this._("In normal case, trouble-free use by users is not possible during the update, since system services may need to be restarted. ") +
				this._("Thus, updates shouldn't be installed on a live system. ") +
				this._("It is also recommended to evaluate the update in a test environment and to create a backup of the system.") + 
				"</p>";
			msg = msg + "<p>" + 
				this._("During setup, the web server may be stopped, leading to a termination of the HTTP connection. ") +
				this._("Nonetheless, the update proceeds and the update can be monitored from a new UMC session. ") +
				this._("Logfiles can be found in the directory /var/log/univention/.") + 
				"</p>";
			msg = msg + "<p>" + 
				this._("Please also consider the release notes, changelogs and references posted in the <a href='http://forum.univention.de'>Univention Forum</a>.") + 
				"</p>";
			if (typeof(args['confirm']) == 'string')
			{
				msg = msg + "<p>" + args['confirm'] + "</p>";
			}
			else
			{
				msg = msg + "<p>" + 
					this._("Do you really wish to proceed?") + 
					"</p>";
			}
			
			umc.dialog.confirm(msg,
			[
			 	{
			 		label:		this._('Cancel')
			 	},
			 	{
			 		label:		this._('Start!'),
			 		'default':	true,
			 		callback:	dojo.hitch(this,function() {
			 			args['confirm'] = false;
			 			this._call_installer(args);
			 		})
			 	}
			]);

			return;
		}

		this.standby(true);

		this.moduleStore.umcpCommand('updater/installer/execute',{
			job:	args['job'],
			detail:		args['detail']?args['detail']:''
		}).then(dojo.hitch(this,function(data) {
			this.standby(false);
			if (data.result['status'] == 0)
			{
				this._switch_to_progress_page();
			}
			else
			{
				umc.dialog.alert(dojo.replace(this._("The installer action could not be started [Error {status}]: {message}"),data.result));
			}
		}),
		// Strongly needed: an error callback! In this case, the built-in error processing
		// (popup or login prompt) is well suited for the situation, so we don't disable it.
		dojo.hitch(this,function(data) {
			this.standby(false);
		}));
	},
	
	
	// Switches to the progress view: all tabs but the 'update in progess' will disappear.
	// Remembers the currently selected tab and will restore it when finished.
	// NOTE that we don't pass any args to the progress page since it is able
	//		to fetch them all from the AT job.
	_switch_to_progress_page: function() {
		
		try
		{
			// No clue why it says that selectedChildWidget() is not a method
			// of 'this'... so I have to do it differently.
			//args['last_tab'] = this.selectedChildWidget();
			var children = this.getChildren();
			var args = {};
			for (var tab in children)
			{
				if (children[tab].get('selected'))
				{
					args['last_tab'] = children[tab];
				}
			}
			
			this.hideChild(this._updates);
			this.hideChild(this._components);
			this.hideChild(this._settings);
			
			this.showChild(this._progress);
			this.selectChild(this._progress);
			
			this._progress.startWatching(args);
		}
		catch(error)
		{
			console.error("switch_progress: " + error.message);
		}
	},
	
	// We must establish a NO ERROR callback too, so we can reset
	// the error status
	_query_success: function(subject) {

		//console.error("QUERY '" + subject + "' -> SUCCESS");
		if (this._connection_status != 0)
		{
			this._reset_error_status();
		}
	},
	
	// Recover after any kind of long-term failure:
	//
	//	-	set error counter to zero
	//	-	set connection status to ok
	//	-	close eventually opened 'connection lost' dialog
	//	-	refresh Updates page
	//	-	restart polling
	_reset_error_status: function() {
		
		this._connection_status = 0;
		this._error_count = 0;
		if (this._busy_dialog)
		{
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
	_query_error: function(subject,data) {
		
		try
		{
			// While the login dialog is open -> all queries return at the
			// error callback, but without data! (should be documented)
			if (typeof(data) == 'undefined')
			{
				//console.error("QUERY '" + subject + "' without DATA");
				return;
			}
			//console.error("QUERY '" + subject + "' STATUS = " + data.status);
			if (data.status == 401)
			{
				if (this._connection_status != 2)
				{
					this._connection_status = 2;
	
					if (this._busy_dialog)
					{
						this._busy_dialog.hide();
						this._busy_dialog.destroy();
						this._busy_dialog = null;
					}
	
					umc.dialog.login().then(dojo.hitch(this, function(username) {
						// if authenticated again -> reschedule refresh queries, Note that these
						// methods are intelligent enough to do nothing if the timer in question
						// is already active.
						this._updates.refreshPage();
						this._updates.startPolling();
						this._components.startPolling();
						this._progress.startPolling();
					})
					);
	
		            
		            umc.dialog.notify(this._("Your current session has expired, or the connection to the server was lost. You must authenticate yourself again."));
				}
//				else
//				{
//					console.error("QUERY '" + subject + "' -> AGAIN STATUS 401");
//				}
			}
			else
			{
				this._connection_status = 1;
	
				this._error_count = this._error_count + 1;
				if (this._error_count < 5)
				{
					// this toaster thingy is not really usable!
					//umc.dialog.notify(this._("Connection to server lost. Trying to reconnect."));
				}
				else
				{
					if (this._busy_dialog == null)
					{
						this._busy_dialog = new dijit.Dialog({
							title:		this._("Connection lost!"),
							closable:	false,
							style:		"width: 300px",
							'class':	'umcConfirmDialog'
						});
						this._busy_dialog.attr("content",
								'<p>' + this._("The connection to the server was lost, trying to reconnect. You may need to re-authenticate when the connection is restored.") + '</p>' +
								'<p>' + this._("Alternatively, you may close the current Management Console window, wait some time, and try to open it again.") + '</p>');
						this._busy_dialog.show();
					}
				}
			}
		}
		catch(error)
		{
			console.error("HANDLE_ERRORS: " + error.message);
		}
	}

});
