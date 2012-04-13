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

dojo.provide("umc.modules._updater.UpdatesPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.tools");
dojo.require("umc.store");
dojo.require("umc.widgets.TitlePane");

dojo.require("umc.modules._updater.Page");

dojo.declare("umc.modules._updater.UpdatesPage", umc.modules._updater.Page, {

	i18nClass:		'umc.modules.updater',
	_last_reboot:	false,
	_update_prohibited: false,

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
				type:			'HiddenInput',
				name:			'appliance_mode'
			},
			{
				type:			'HiddenInput',
				name:			'release_update_blocking_component'
			},
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
						var element_releases = this._form.getWidget('releases');
						var to_show = false;
						var to_show_msg = true;

						var element_updatestext = this._form.getWidget('ucs_updates_text');
						element_updatestext.set('content', this._("There are no release updates available."));

						if (values.length)
						{
							var val = values[values.length-1]['id'];
							to_show = true;
							to_show_msg = false;
							element_releases.set('value',val);
						}

						var appliance_mode = (this._form.getWidget('appliance_mode').get('value') === 'true');
						var blocking_component = this._form.getWidget('release_update_blocking_component').get('value');
						if ((blocking_component) && (! appliance_mode)) {
							// further updates are available but blocked by specified component which is required for update
							element_updatestext.set('content', dojo.replace(this._("Further release updates are available but cannot be installed because the component '{0}' is not available for newer release versions."), [blocking_component]));
							to_show_msg = true;
						}

						// hide or show combobox, spacers and corresponding button
						this._form.showWidget('releases',to_show);
						this._form.showWidget('hspacer_180px',to_show);
						this._form.showWidget('vspacer_1em',to_show);

						this._form.showWidget('ucs_updates_text', to_show_msg);

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
				type:			'HiddenInput',
				name:			'components_errata'
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
//			{
//				name:		'refresh',
//				label:		this._("Refresh"),
//				callback:	dojo.hitch(this, function() {
//					this.refreshPage();
//				})
//			},
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
			moduleStore:	umc.store.getModuleStore(null,'updater/updates'),
			scrollable: true
//			polling:	{
//				interval:	5000,
//				query:		'updater/updates/serial',
//				callback:	dojo.hitch(this, function() {
//					this.refreshPage();
//				})
//			}
		});

		// fetch all known/initial titlepanes and save them with their name
		// so they can be used later on
		this._titlepanes = { 
			reboot: this._form._container.getChildren()[0],
			easymode: this._form._container.getChildren()[1],
			release: this._form._container.getChildren()[2],
			errata: this._form._container.getChildren()[3],
			packages: this._form._container.getChildren()[4]
		};

		// Before we attach the form to our page, just switch off all title panes.
		// This delays showing the right panes until we know the value of 'easy_mode'.
		this._show_updater_panes(false);

		// show standby while loading data
		this.standby(true);

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
				var element = this._form.getWidget('easy_available_text');
				var ava = ((values['easy_update_available'] === true) || (values['easy_update_available'] === 'true'));
				var appliance_mode = ((values['appliance_mode'] === true) || (values['appliance_mode'] === 'true'));
				var blocking_component = this._form.getWidget('release_update_blocking_component').get('value');
				if (ava) {
					element.set('content', this._("There are updates available."));
				} else if ((blocking_component) && (! appliance_mode)) {
					element.set('content', dojo.replace(this._("Further release updates are available but cannot be installed because the component '{0}' is not available for newer release versions."), [blocking_component]));
				} else {
					element.set('content', this._("There are no updates available."));
				}
				var ebu = this._form._buttons['easy_upgrade'];
				dojo.toggleClass(ebu.domNode,'dijitHidden',! ava);

				// Text for errata updates. Stuffed into two different widgets so the button on the right
				// can be aligned at the second sentence.

				var but = this._form._buttons['run_errata_update'];
				var ucs_errata_count = parseInt(values['latest_errata_update'],10) - parseInt(values['erratalevel'],10)
				if (( ucs_errata_count > 0 ) || ( values.components_errata !== "" ))
				{
					// Convert the string back to an object. This is necessary because such a dict
					// can not be transferred through a hidden value
					if (values.components_errata !== "" ) {
						values.components_errata = dojo.fromJson(values.components_errata);
					}

					var tmp1 = this._("Errata updates are available for this system.");
					if (( ucs_errata_count > 0 ) && ( values.components_errata !== "" ))
					{
						// Errata Updates for UCS and for components
						if ( ucs_errata_count > 1 ) {
							var tmp2 = dojo.replace(this._("For UCS are {errata_count} errata updates available" ), {errata_count: ucs_errata_count});
						} else {
							var tmp2 = dojo.replace(this._("For UCS is one errata update available" ), {errata_count: ucs_errata_count});
						}
						for (var key in values.components_errata)
						{
							if ( parseInt(values.components_errata[key],10) > 1 ) {
								tmp2 += dojo.replace(this._(" and for component {component} are {count} errata updates available"), {component: key, count: values.components_errata[key]})
							} else {
								tmp2 += dojo.replace(this._(" and for component {component} is one errata update available"), {component: key, count: values.components_errata[key]})
							}
						}
						tmp2 += '.';
					}
					else if ( ucs_errata_count > 0 )
					{
						// Errata Updates for UCS
						if ( ucs_errata_count > 1 ) {
							var tmp2 = dojo.replace(this._("There are {errata_count} errata updates for UCS available." ), {errata_count: ucs_errata_count})
						} else {
							var tmp2 = dojo.replace(this._("There is one errata update for UCS available." ), {errata_count: ucs_errata_count})
						}
					}
					else
					{
						// Errata Updates for components
						for (var key in values.components_errata)
						{
							if (tmp2 === undefined) {
								if ( parseInt(values.components_errata[key],10) > 1 ) {
									var tmp2 = dojo.replace(this._("For component {component} are {count} errata updates available"), {component: key, count: values.components_errata[key]})
								} else {
									var tmp2 = dojo.replace(this._("For component {component} is one errata update available"), {component: key, count: values.components_errata[key]})
								}
							} else {
								if ( parseInt(values.components_errata[key],10) > 1 ) {
									tmp2 += dojo.replace(this._(" and for component {component} are {count} errata updates available"), {component: key, count: values.components_errata[key]})
								} else {
									tmp2 += dojo.replace(this._(" and for component {component} is one errata update available"), {component: key, count: values.components_errata[key]})
								}
							}
						}
						tmp2 += '.';
					}
					this._form.getWidget('errata_update_text2').set('content',tmp2);

					// Show the Update button
					dojo.toggleClass(but.domNode,'dijitHidden',false)
				}
				else
				{
					var tmp1 = this._("There are no errata updates available for this system.")
					dojo.toggleClass(but.domNode,'dijitHidden',true)
				}
				this._form.getWidget('errata_update_text1').set('content',tmp1);

				var tx1 = '';
				var tx2 = '';
				if (values['components'] == '0')
				{
					tx1 = this._("There are no components configured for this system.");
				}
				else
				{
					if (values['components'] == '1')
					{
						tx1 = this._("The system knows about 1 component.");
					}
					else
					{
						tx1 = dojo.replace(this._("The system knows about {components} components."),values);
					}
					tx1 += '<br/>';
					switch(values['enabled'])
					{
						case '0':
							tx1 += this._("None of them are currently enabled.");
							break;
						case '1':
							tx1 += this._("1 of them is currently enabled.");
							break;
						default:
							tx1 += dojo.replace(this._("{enabled} of them are currently enabled."),values);
					}

				}
				this._form.getWidget('package_update_text1').set('content',tx1);

				this._show_reboot_pane(values['reboot_required']);

			}
			catch(error)
			{
				console.error("onLoaded: " + error.message);
			}
			this.standby(false);
		}));

		// call hooks updater_show_message and updater_prohibit_update.
		//
		// "updater_show_message" has to return its data as a dictionary . 
		// The returned data will be displayed in a new titlepane for each hook.
		// data structure:
		// {
		//   valid: (true|false)   ==> indicates if a message should be displayed
		//   title: <string>       ==> title of TitlePane
		//   message: <string>     ==> content of TitlePane
		// }
		//
		// "updater_prohibit_update" has to return a boolean directly.
		// If the value "true" is returned by at least one hook, the titlepanes 
		// "easymode", "release", "errata" and "packages" will be hidden and
		// this._update_prohibited will be set to true.

		umc.tools.umcpCommand('updater/hooks/call', { hooks: ['updater_show_message', 'updater_prohibit_update'] }).then(dojo.hitch(this, function(result) {
			this._update_prohibited = false;
			var index = 0;
			var newpane;
			dojo.forEach(result.result.updater_show_message, function(hookresult) {
				if (hookresult.valid) {
		 			newpane = new dijit.TitlePane({
		 				title: hookresult.title,
		 				content: hookresult.message
		 			});
		 			this._form._container.addChild(newpane, 0);
				}
			}, this);
			dojo.forEach(result.result.updater_prohibit_update, function(hookresult) {
				if (hookresult) {
					this._update_prohibited = true;
					this._show_updater_panes(false);
				}
			}, this);
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

	// This function switches the visibilty of all relevant titlepanes used for updates.
	// Other titlepanes (e.g. reboot) are not affected.
	_show_updater_panes: function(on) {
		dojo.forEach(['easymode','release','errata','packages'], function(iname) {
			dojo.toggleClass(this._titlepanes[iname].domNode, 'dijitHidden', ! on);
		}, this);
	},

	// Switches easy mode on or off. If the update is prohibited via hook, this 
	// function hides the updater titlepanes. Doesn't touch other panes like the 
	// 'reboot required' pane.
	_switch_easy_mode: function(on) {
		if (this._update_prohibited) {
			this._show_updater_panes(false);
		} else {
			dojo.toggleClass(this._titlepanes.easymode.domNode, 'dijitHidden',! on);
			dojo.toggleClass(this._titlepanes.release.domNode, 'dijitHidden', on);
			dojo.toggleClass(this._titlepanes.errata.domNode, 'dijitHidden', on);
			dojo.toggleClass(this._titlepanes.packages.domNode, 'dijitHidden', on);
		}
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

		dojo.toggleClass(this._titlepanes.reboot.domNode,'dijitHidden',! on);

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
