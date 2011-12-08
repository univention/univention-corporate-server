/*
 * Copyright 2011 Univention GmbH
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

dojo.provide("umc.modules._updater.UpdatesPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.tools");
dojo.require("umc.store");

dojo.require("umc.modules._updater.Page");

dojo.declare("umc.modules._updater.UpdatesPage", umc.modules._updater.Page, {
	
	i18nClass: 		'umc.modules.updater',
	_last_reboot:	false,
	
    postMixInProperties: function() {

    	this.inherited(arguments);

        dojo.mixin(this, {
	    	title:			this._("Updates"),
	        headerText:		this._("Available system updates"),
	        helpText:		this._("Overview of all updates that affect the system as a whole.")
        });
    },

    buildRendering: function() {
		
    	this.inherited(arguments);
    	
    	var widgets =
    	[
    	 	// --------------------- Reboot pane -----------------------------
			{
				type:			'HiddenInput',
				name:			'reboot_required'
			},
			{
				type:			'Text',
				name:			'reboot_progress_text',
				label:			'',
				content:		this._("The computer is now rebooting. ") +
								this._("This may take some time. Please be patient. ") +
								this._("During reboot, the connection to the system will be lost. ") +
								this._("When the connection is back you will be prompted to authenticate yourself again.")
			},
    	 	{
				type:			'Text',
				name:			'reboot_text',
				label:			'',
				content:		this._("In order to complete the recently executed installer action, it is required to reboot the system."),
				// FIXME: Manual placement: should be done by the layout framework some day.
				style:			'width:500px;'
    	 	},
    	 	// ------------------- Easy upgrade mode -------------------------
    	 	{
    	 		type:			'HiddenInput',
    	 		name:			'easy_mode'
    	 	},
    	 	{
    	 		type:			'HiddenInput',
    	 		name:			'easy_update_available'
    	 	},
    	 	{
    	 		type:			'Text',
    	 		name:			'easy_release_text',
    	 		label:			'',
    	 		content:		'easy_release_text'			// set in onLoaded event
    	 	},
    	 	{
    	 		type:			'Text',
				// FIXME: Manual placement: should be done by the layout framework some day.
				style:			'width:500px;',
    	 		name:			'easy_available_text',
    	 		label:			'',
    	 		content:		'easy_available_text'		// changed in onLoaded event
    	 	},
    	 	// -------------------- Release updates --------------------------
			{
				type:			'ComboBox',
				name:			'releases',
		 		label:			this._('Update system up to release'),
		 		// No matter what has changed: the 'serial' API will reflect it.
		 		// These dependencies establish the auto-refresh of the combobox
		 		// whenever the form itself has been reloaded.
		 		depends:		['ucs_version','latest_errata_update','erratalevel','serial','timestamp'],
		 		dynamicValues:	'updater/updates/query',
		 		// FIXME Manual placement: should be done by the layout framework some day.
		 		style:			'width:300px;',
		 		onValuesLoaded:	dojo.hitch(this, function(values) {
		 			// TODO check updater/installer/running, don't do anything if something IS running
		 			try
		 			{
		 				this._query_success('updater/updates/query');
		 				var element = this._form.getWidget('releases');
		 				var to_show = false;
		 				if (values.length)
		 				{
		 					to_show = true;
			 				var val = values[values.length-1]['id'];
			 				element.set('value',val);
		 				}
		 				// hide or show combobox, spacers and corresponding button
	 					this._form.showWidget('releases',to_show);
						this._form.showWidget('hspacer_180px',to_show);
						this._form.showWidget('vspacer_1em',to_show);
						
						this._form.showWidget('ucs_updates_text',! to_show);		// either combobox or the text that no updates are available.

						var but = this._form._buttons['run_release_update'];
						but.set('visible', to_show);

	 					// renew affordance to check for package updates, but only
	 					// if we didn't see availability yet.
	 					if (! this._updates_available)
	 					{
	 						this._set_updates_button(false,this._("Package update status not yet checked"));
	 					}
		 			}
		 			catch(error)
		 			{
		 				console.error("onValuesLoaded: " + error.message);
		 			}
		 		})
			},
			{
				type:			'HiddenInput',
				name:			'ucs_version'
			},
			{
				type:			'HiddenInput',
				name:			'serial'
			},
			{
				type:			'HiddenInput',
				name:			'language'
			},
			{
				type:			'HiddenInput',
				name:			'timestamp'
			},
			{
				type:			'HiddenInput',
				name:			'components'
			},
			{
				type:			'HiddenInput',
				name:			'enabled'
			},
			{
				type:			'Text',
				label:			'',
				name:			'vspacer_1em',
				style:			'height:1em;'
			},
			{
				type:			'Text',
				label:			'',
				name:			'hspacer_180px',
		 		// FIXME Manual placement: should be done by the layout framework some day.
				style:			'width:180px;'
			},
			{
				type:			'Text',
				label:			'',
				name:			'ucs_version_text',
				content:		this._("... loading data ...")
			},
			{
				type:			'Text',
				label:			'',
				name:			'ucs_updates_text',
				content:		this._("There are no release updates available.")
			},
			// ---------------------- Errata updates -----------------------
			{
				type:			'HiddenInput',
				name:			'erratalevel'
			},
			{
				type:			'HiddenInput',
				name:			'latest_errata_update'
			},
			{
				type:			'Text',
				label:			'',
				name:			'errata_update_text1',
				content:		this._("... loading data ...")
			},
			{
				type:			'Text',
				label:			'',
				name:			'errata_update_text2',
		 		// FIXME Manual placement: should be done by the layout framework some day.
				style:			'width:500px;margin-top:.5em;'
			},
			// -------------------- Package updates ------------------------
			{
				type:			'Text',
				label:			'',
				name:			'package_update_text1'
			},
			{
				type:			'Text',
				label:			'',
				name:			'package_update_text2',
		 		// FIXME Manual placement: should be done by the layout framework some day.
				style:			'width:500px;margin-top:.5em;',
				content:		this._("Package update status not yet checked")
			}
		];
    	     
    	// All buttons are initialized with the CSS class that will initially hide them.
    	// (except the 'package updates' button that has different functions)
    	// We don't want to have clickable buttons before their underlying data
    	// has been fetched.
       	var buttons =
   		[
           	{
   	            name:		'run_release_update',
		 		label:		this._('Install release update'),
		 		callback:	dojo.hitch(this,function() {
		 			var element = this._form.getWidget('releases');
		 			var release = element.get('value');
		 			// TODO check updater/installer/running, don't do action if a job is running
		 			this.runReleaseUpdate(release);
		 		}),
		 		visible:	false
           	},
           	{
   	            name:		'run_errata_update',
     			label:		this._('Install errata update'),
     			callback:	dojo.hitch(this, function() {
		 			// TODO check updater/installer/running, don't do action if a job is running
     				this.runErrataUpdate();
     			}),
		 		visible:	false
           	},
           	{
   	            name:		'run_packages_update',
   	            label:		this._("Check for package updates"),
   	            callback:	dojo.hitch(this, function() {
   	            	this._check_dist_upgrade();
   	            })
           	},
           	// If refresh isn't automatic anymore... should we show a "Refresh" button?
//           	{
//           		name:		'refresh',
//           		label:		this._("Refresh"),
//           		callback:	dojo.hitch(this, function() {
//           			this.refreshPage();
//           		})
//           	},
           	{
           		name:		'reboot',
           		label:		this._("Reboot"),
           		callback:	dojo.hitch(this, function() {
           			this._reboot();
           		})
           	},
           	{
           		name:		'easy_upgrade',
           		label:		this._("Start Upgrade"),		// FIXME Label not correct
           		callback:	dojo.hitch(this, function() {
		 			// TODO check updater/installer/running, don't do action if a job is running
           			this.runEasyUpgrade();
           		})
           	}
   		];
       	
       	var layout = 
       	[
       	 	{
       	 		label:		this._("Reboot required"),
       	 		layout:
       	 		[
       	 		 	['reboot_progress_text'],
       	 		 	['reboot_text','reboot']
       	 		]
       	 	},
       	 	{
       	 		label:		this._("Release information"),
       	 		layout:
       	 		[
       	 		 	['easy_release_text'],
       	 		 	['easy_available_text','easy_upgrade']
       	 		]
       	 	},
       	 	{
       	 		label:		this._("Release updates"),
       	 		layout:
       	 		[
   		    		['ucs_version_text'],
					['vspacer_1em'],
   		    		['releases','hspacer_180px','run_release_update'],
   		    		['ucs_updates_text']
   		    	]
       	 	},
       	 	{
       	 		label:		this._("Errata updates"),
       	 		layout:
   	 			[
   	 			 	['errata_update_text1'],
   	 			 	['errata_update_text2' , 'run_errata_update']
   		    	]
       	 	},
       	 	{
       	 		label:		this._("Package updates"),
       	 		layout:
       	 		[
					['package_update_text1'],
       	 		 	['package_update_text2', 'run_packages_update']
       	 		]
       	 	}
       	];

       	this._form = new umc.modules._updater.Form({
       		widgets:		widgets,
       		layout:			layout,
       		buttons:		buttons,
       		moduleStore:	umc.store.getModuleStore(null,'updater/updates')
//			polling:	{
//				interval:	5000,
//				query:		'updater/updates/serial',
//				callback:	dojo.hitch(this, function() {
//					this.refreshPage();
//				})
//			}
       	});
       	
       	// Before we attach the form to our page, just switch off all title panes.
       	// This delays showing the right panes until we know the value of 'easy_mode'.
       	for (var i = 0; i<5; i++)
       	{
       		this._show_title_pane(i,false);
       	}
       	
       	this.addChild(this._form);
       	this._form.showWidget('releases',false);
       	this._form.showWidget('ucs_updates_text',false);
       	
       	// Propagate query errors/success to our parent container if it's listening
    	dojo.connect(this._log,'_query_error',dojo.hitch(this,function(subject,data) {
    		this._query_error(subject,data);
    	}));
    	dojo.connect(this._log,'_query_success',dojo.hitch(this,function(subject) {
    		this._query_success(subject);
    	}));
    	
       	dojo.connect(this._form,'onLoaded',dojo.hitch(this, function(args) {
       		try
       		{
       			this._query_success('updater/updates/get');
				var values = this._form.gatherFormValues();
				
				// before we do anything else: switch visibility of panes dependant of the 'easy mode'
				this._switch_easy_mode((values['easy_mode'] === true) || (values['easy_mode'] === 'true'));
				
				// set text that shows release updates.
       			// *** NOTE *** Availability of release updates (and visibility of 'Execute' button) can't be
       			//				processed here since we have to wait for the 'onValuesLoaded' event of the
       			//				combobox.
       			var vtxt = dojo.replace(this._("The currently installed release version is {ucs_version}"),values);
       			this._form.getWidget('ucs_version_text').set('content',vtxt);
       			
       			// Text (and button visibility) in EASY mode. We reuse the 'vtxt' variable if the
       			// erratalevel is not yet set.
       			if (values['erratalevel'] != 0)
       			{
       				vtxt = dojo.replace(this._("The currently installed release version is {ucs_version} errata{erratalevel}"),values);
       			}
       			this._form.getWidget('easy_release_text').set('content',vtxt);
       			
       			// easy_update_available -> easy_available_text
       			var ava = ((values['easy_update_available'] === true) || (values['easy_update_available'] === 'true'));
       			this._form.getWidget('easy_available_text').set('content',
       					ava ?
       					this._("There are updates available.") :
       					this._("There are no updates available.")
       					);
       			var ebu = this._form._buttons['easy_upgrade'];
       			dojo.toggleClass(ebu.domNode,'dijitHidden',! ava);

       			// Text for errata updates. Stuffed into two different widgets so the button on the right
       			// can be aligned at the second sentence.
		    	var tmp1 = (values['erratalevel'] != 0) ?
		    		dojo.replace(this._("Your system is at errata level {erratalevel}."),values) :
		    		this._("No errata updates for the current version are installed.");
				this._form.getWidget('errata_update_text1').set('content',tmp1);
			    var tmp2 = (values['latest_errata_update'] != 0) ?
					dojo.replace(this._("The most recent errata update is {latest_errata_update}."),values) :
					this._("There are no errata updates available for the current release.");
				this._form.getWidget('errata_update_text2').set('content',tmp2);
				
				// Uuuh, Buttons are not included in the _widgets list, so they can't be addressed by
				// showWidget()... so I have to grab into internal structure of the Form :-(
				var but = this._form._buttons['run_errata_update'];
				dojo.toggleClass(but.domNode,'dijitHidden',values['latest_errata_update'] <= values['erratalevel']);

 				var tx1 = '';
 				var tx2 = '';
 				if (values['components'] == '0')
 				{
 					tx1 = this._("There are no components configured for this system.");
 				}
 				else
 				{
 					tx1 = dojo.replace(this._("The system knows about {components} components."),values);
 					tx1 = tx1 + '<br/>' + (values['enabled'] == 0 ?
						this._("None of them are currently enabled.") :
						dojo.replace(this._("{enabled} of them are currently enabled."),values));
 				}
 				this._form.getWidget('package_update_text1').set('content',tx1);		 				
 				
 				this._show_reboot_pane(values['reboot_required']);
 					
       		}
       		catch(error)
       		{
       			console.error("onLoaded: " + error.message);
       		}
       	}));
	},
	
	// Internal function that sets the 'updates available' button and
	// corresponding text widget.
	_set_updates_button: function(avail,msg) {
		try
		{
			this._updates_available = avail;
			var but = this._form._buttons['run_packages_update'];
			but.set('label',avail ?
				this._("Install package updates") :
				this._("Check for package updates"));
			this._form.getWidget('package_update_text2').set('content',msg);
		}
		catch(error)
		{
			console.error("set_updates_button: " + error.message);
		}
	},
	
	// Internal function that does different things about package updates:
	//
	//	- if no package updates are available: check for availability
	//	- if some are available -> invoke 'runDistUpgrade()' callback.
	_check_dist_upgrade: function() {
		
		if (this._updates_available)
		{
			this.runDistUpgrade();
		}
		else
		{
			this.standby(true);
			umc.tools.umcpCommand('updater/updates/available').then(
				dojo.hitch(this, function(data) {
					this.standby(false);
					this._set_updates_button(data.result,
						data.result ?
							this._("Package updates are available.") :
							this._("There are no package updates available."));
				}),
				dojo.hitch(this, function(data) {
					this.standby(false);
					this._set_updates_button(false,this._("Update availability could not be checked."));
				})
			);
		}
	},
	
	// Now we need it: a general function that switches the visibility of
	// panes on and off. We use this for the visibility of the reboot
	// pane and the switch between easy and normal mode.
	//
	// *** HACK *** this function cannot address the titlePanes directly since they're
	//				buried in the internal layout structures of the form. But as we have
	//				digged into the structure of the form, we rely on the following things:
	//
	//				(1)	the first child of the form is the container that contains all
	//					title panes
	//				(2)	the order of the titlePanes there is the same as the order in
	//					our layout structure.
	_show_title_pane: function(number, on) {
		
		var cont = this._form.getChildren()[0];		// the container that contains the title panes
		var chi = cont.getChildren();				// the array of TitlePanes
		
		if (number < chi.length)
		{
			var pan = chi[number];
			dojo.toggleClass(pan.domNode,'dijitHidden',! on);
		}
	},
	
	// switches easy mode on or off. Doesn't touch the 'reboot required' pane.
	_switch_easy_mode: function(on) {
		
		this._show_title_pane(1,on);		// this is the 'easy mode' pane
		this._show_title_pane(2,! on);		// release
		this._show_title_pane(3,! on);		// errata
		this._show_title_pane(4,! on);		// packages
	},
	
	// Switches visibility of the reboot pane on or off. Second arg 'inprogress'
	// switches between 'affordance to reboot' (progress=false) and
	// 'reboot in progress' (progress=true).
	//
	_show_reboot_pane: function(on,progress) {
		
		if (typeof(on) == 'string')
		{
			on = (on == 'true');
		}
		
		// pop a message up whenever the 'on' value changes
		if (on != this._last_reboot)
		{
			this._last_reboot = on;
		}
		
		var pane = this._form.getChildren()[0].getChildren()[0];
		dojo.toggleClass(pane.domNode,'dijitHidden',! on);
		
		if (on)
		{
			if (typeof(progress) == 'undefined')
			{
				progress = false;
			}
			this._form.showWidget('reboot_text',! progress);
			this._form.showWidget('reboot_progress_text',progress);

			var but = this._form._buttons['reboot'];
			dojo.toggleClass(but.domNode,'dijitHidden',progress);
		}

	},
	
	// called when the 'reboot' button is pressed.
	// now with confirmation that doesn't depend on the 'confirmations' setting.
	_reboot: function() {
		
		umc.dialog.confirm(
			this._("Do you really want to reboot the machine?"),
			[
			 	{
			 		label:		this._("Cancel"),
			 		'default':	true
			 	},
			 	{
			 		label:		this._("Reboot"),
			 		callback:	dojo.hitch(this, function() {
			 			this.standby(true);
			 			umc.tools.umcpCommand('updater/installer/reboot').then(dojo.hitch(this, function() {
			 				this.standby(false);
			 				this._show_reboot_pane(true,true);
			 			}),
			 			dojo.hitch(this, function() {
			 				this.standby(false);
			 			})
			 			);
			 		})
			 	}
			]
		);

	},
	
	// First page refresh doesn't work properly when invoked in 'buildRendering()' so
	// we defer it until the UI is being shown
	startup: function() {
		
		this.inherited(arguments);
		this._show_reboot_pane(false);
		this.refreshPage();
		
	},
	
	// ensures refresh whenever we're returning from any action.
	onShow: function() {
		
		this.inherited(arguments);
		this.refreshPage(true);
	},
	
	// should refresh any data contained here. (can be called from outside when needed)
	// with 'force=true' the caller can request that even the affordance to 'check
	// update availability' is reset to 'not yet checked'.
	// Normally 'force' is not specified and assumed to be 'false'.
	refreshPage: function(force) {
		if (force)
		{
			this._updates_available = false;
		}
		this._form.load(' ');
	},
	
	// gives a means to restart polling after reauthentication
	startPolling: function() {
		// not needed anymore.
		// this._form.startPolling();
	},
	
	// These functions are stubs that the 'updater' Module is listening to,
	// to start the corresponding installer call.
	runReleaseUpdate: function(release) {
	},
	runErrataUpdate: function() {
	},
	runDistUpgrade: function() {
	},
	runEasyUpgrade: function() {
	}

});
