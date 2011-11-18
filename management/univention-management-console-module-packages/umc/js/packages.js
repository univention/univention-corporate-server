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

dojo.provide("umc.modules.packages");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.store");

dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Grid");

dojo.require("umc.modules._packages.SearchForm");

dojo.declare("umc.modules.packages", [ umc.widgets.Module, umc.i18n.Mixin ], {

	i18nClass:			'umc.modules.packages',
	idProperty:			'package',
	_last_log_stamp:	0,

	buildRendering: function() {

		this.inherited(arguments);

		var page = new umc.widgets.Page({
			headerText:		this._("Package management"),
			helpText:		this._("On this page, you see all software packages available on your system, and you can install, deinstall or update them."),
			title:			this._("Package management")
		});
		this.addChild(page);

		this._pane = new umc.widgets.ExpandingTitlePane({
			title:			this._("Packages")
		});
		page.addChild(this._pane);

		this._form = new umc.modules._packages.SearchForm({
			region:				'top'
		});
		dojo.connect(this._form,'onSubmit',dojo.hitch(this, function() {
			this._refresh_grid();
		}));

		var actions = [
			{
				name:				'view',
				label:				this._("View Details"),
				isContextAction:	true,
				isStandardAction:	false,
				isMultiAction:		false,
				callback:	dojo.hitch(this, function(ids,items) {
					this._show_details(ids,items);
				})
			},
			// isStandardAction=true for the installer actions (install/deinstall/upgrade)
			// doesn't make sense as long as these actions aren't displayed as icons
			{
				name:				'install',
				label:				this._("Install"),
				isContextAction:	true,
				isStandardAction:	false,
				isMultiAction:		false,
				canExecute: dojo.hitch(this, function(values) {
					return this._can_install(values);
				}),
				callback:	dojo.hitch(this, function(ids,items) {
					this._call_installer('install',ids,items);
				})
			},
			{
				name:				'uninstall',
				label:				this._("Deinstall"),
				isContextAction:	true,
				isStandardAction:	false,
				isMultiAction:		false,
				canExecute: dojo.hitch(this, function(values) {
					return this._can_uninstall(values);
				}),
				callback:	dojo.hitch(this, function(ids,items) {
					this._call_installer('uninstall',ids,items);
				})
			},
			{
				name:				'upgrade',
				label:				this._("Upgrade"),
				isContextAction:	true,
				isStandardAction:	false,
				isMultiAction:		false,
				canExecute: dojo.hitch(this, function(values) {
					return this._can_upgrade(values);
				}),
				callback:	dojo.hitch(this, function(ids,items) {
					this._call_installer('upgrade',ids,items);
				})
			}
		];

		var columns = [
			{
				name:		'package',
				width:		'adjust',
				label:		this._("Package name")
			},
			{
				name:		'section',
				width:		'adjust',
				label:		this._("Section")
			},
			{
				name:		'status',
				label:		this._("Installation status"),		// notinstalled/installed/upgradeable
				width:		'adjust'
			},
			{
				name:		'summary',
				label:		this._("Package description")
			}
		];

		// create a grid in the 'center' region
		this._grid = new umc.widgets.Grid({
			region:			'center',
			actions:		actions,
			columns:		columns,
			moduleStore:	this.moduleStore,
			defaultAction:	'view',
			onFilterDone:	dojo.hitch(this, function() {
				this._form.allowSearchButton(true);
			})
		});

		// TODO create progress view widgets
		this._logview = new umc.widgets.Text({
			region:			'center',
			content:		'this is the log viewer',
			style:			'font-family:monospace;border:solid 1px #e0e0e0;background-color:#f0f0f0;overflow:auto;',
			scrollable:		true		// doesn't work?
		});

		this._progress = new umc.widgets.Text({
			region:			'top',
			content:		'this is the progress title zone'
		});
		// will be shown when the installer is finished
		this._back = new umc.widgets.Button({
			region:			'bottom',
			name:			'back',
			label:			this._( 'Back to overview' ),
			callback:		dojo.hitch(this, function() {
				this._switch_to_progress(false);
			})
		});

		this._switch_to_progress(false);
	},

	_refresh_grid: function() {

		var values = this._form.gatherFormValues();
		if (values['section'])
		{
			this._form.allowSearchButton(false);
			this._grid.filter(values);
		}
	},

	// shows details about a package in a popup dialog
	// ** NOTE ** 'items' is not processed here at all.
	_show_details: function(ids,items) {

		var id = ids;
		if (dojo.isArray(ids))
		{
			id = ids[0];
		}

		this._grid.standby(true);

		this.moduleStore.umcpCommand('packages/get',{'package':id}).then(
			dojo.hitch(this, function(data) {

				this._grid.standby(false);

				var head_style	= 'font-size:120%;font-weight:bold;margin:.5em;text-decoration:underline;';
				var label_style = 'vertical-align:top;text-align:right;padding-left:1em;padding-right:.5em;white-space:nowrap;font-weight:bold;';
				var data_style	= 'vertical-align:top;padding-bottom:.25em;';

				var txt = "<p style='" + head_style + "'>" +
					dojo.replace(this._("Details for package '{package}'"),data.result) +
					"</p>";
				txt += "<table>\n";
				var width = 550;	// mimic the default of umc.dialog.confirm
				var order = this._detail_field_order();
				for (var fi in  order)
				{
					var f = order[fi];
					if (typeof(data.result[f]) != 'undefined')
					{
						var fl = this._detail_field_label(f);
						if (fl)
						{
							txt += "<tr>\n";
							txt += "<td style='" + label_style + "'>" + fl + "</td>\n";
							// ----------------------------------------------------------------
							// if you think the following logic is not needed...
							// just open the 'devscripts' package and see for yourself.
							var dfv = this._detail_field_value(f,data.result[f]);
							var maxlen = 3000;
							if (dfv.length > maxlen)
							{
								// cut text at 'maxlen' chars, optionally adding a hint.
								dfv = dfv.substr(0,maxlen) + this._("...<br>[%d more chars]",dfv.length-maxlen);
							}
							if (f == 'description')
							{
								// adjust width according to the length of the 'description' field.
								width = 500 + (dfv.length / 10);
							}
							// ----------------------------------------------------------------
							txt += "<td style='" + data_style + "'>" + dfv + "</td>\n";
							txt += "</tr>\n";
						}
					}
				}
				txt += "</table>\n";
				var buttons = [];
				if (this._can_install(data.result))
				{
					buttons.push({
						name:		'install',
						label:		this._("Install"),
						callback:	dojo.hitch(this, function() {
							this._call_installer('install',data.result['package'],false);
						})
					});
				}
				if (this._can_uninstall(data.result))
				{
					buttons.push({
						name:		'uninstall',
						label:		this._("Deinstall"),
						callback:	dojo.hitch(this, function() {
							this._call_installer('uninstall',data.result['package'],false);
						})
					});
				}
				if (this._can_upgrade(data.result))
				{
					buttons.push({
						name:		'upgrade',
						label:		this._("Upgrade"),
						callback:	dojo.hitch(this, function() {
							this._call_installer('upgrade',data.result['package'],false);
						})
					});
				}
				// always: a button to close the dialog.
				buttons.push({
					name:		'cancel',
					label:		this._("Close")
				});

                var confirmDialog = new umc.widgets.ConfirmDialog({
                    title: this._('Package details'),
                    style: dojo.replace('min-width:500px;max-width: {width}px;',{width: width}),		// umc.dialog.confirm doesn't exceed 550px
                    message: txt,
                    options: buttons
	            });

	            // connect to 'onConfirm' event to close the dialog in any case
	            dojo.connect(confirmDialog, 'onConfirm', function(response) {
	                    confirmDialog.close();
	            });

	            // show the confirmation dialog
	            confirmDialog.show();


			}),
			dojo.hitch(this, function(data) {
				this._grid.standby(false);
				umc.dialog.alert(data.message);
			})
		);
	},

	// Helper function that returns the field names for the
	// detail view in a well-defined order
	_detail_field_order: function() {

		return (['package','summary','section','installed',
		         'installed_version','upgradable','size','priority','description'
		         ]);
	},

	// Helper function that translates field names for the detail view. This
	// is made for two purposes:-
	//
	//	(1)	this way, we can mention the entries in the source, so our
	//		automated .po file maintainer script can see them
	//	(2)	fields not mentioned here should not be displayed in the detail view
	_detail_field_label: function(name) {

		switch(name)
		{
			case 'package':				return this._("Package name");
			case 'section':				return this._("Section");
			case 'summary':				return this._("Summary");
			case 'description':			return this._("Description");
			case 'installed':			return this._("Is installed");
			case 'upgradable':			return this._("Is upgradeable");
			case 'size':				return this._("Package size");
			case 'priority':			return this._("Priority");
			case 'installed_version':	return this._("Installed version");
		}
		return null;
	},

	// Helper function that translates field values. Mainly used for:
	//
	//	(1)	boolean to text (according to field name)
	//	(2)	HTML-escaping free text (summary,description)
	//	(3)	adding (eventually) icons
	//
	_detail_field_value: function(name,value) {

		switch(name)
		{
			case 'summary':
			case 'description':
				// TODO find or write a decoder function
				return value;		// for now
			case 'installed':
			case 'upgradable':
				if ((value === 'true') || (value === true))
				{
					return this._("Yes");
				}
				return this._("No");
		}
		// fallback: return value unchanged
		return value;
	},

	// Helper functions that determine if a given function can be executed.
	// will be called from different places:-
	//
	//	(1)	in the 'canExecute' callbacks of grid rows
	//	(2)	in the detail view to determine which buttons to show
	//
	_can_install: function(values) {
		return ((values['installed'] === false) || (values['installed'] === 'false'));
	},
	_can_uninstall: function(values) {
		return ((values['installed'] === true) || (values['installed'] === 'true'));
	},
	_can_upgrade: function(values) {
		return (
				((values['installed'] === true) || (values['installed'] === 'true')) &&
				((values['upgradable'] === true) || (values['upgradable'] == 'true'))
				);
	},

	// prepares all data for the acutal execution of the installer.
	_call_installer: function(func,ids,confirm) {

		if (typeof(confirm) == 'undefined')
		{
			confirm = true;
		}
		var id = ids;
		// currently we strictly expect ONE id to be processed here.
		//
		// When the grid is capable of dealing with multi-actions in the context
		// of the 'canExecute' callback -> perhaps it would make sense to accept
		// multiple IDs here too.
		if (dojo.isArray(ids)) { id = ids[0]; }

		var verb = '';
		var verb1 = '';
		switch(func)
		{
			case 'install': 	verb = this._("install");	verb1 = this._("installing"); break;
			case 'uninstall':	verb = this._("uninstall");	verb1 = this._("uninstalling"); break;
			case 'upgrade':		verb = this._("upgrade");	verb1 = this._("upgrading"); break;
		}

		this._progress.set('content', dojo.replace(this._("<p>You're currently {verb} the '{id}' package:</p>"),{verb: verb1, id: id}));

		if (confirm)
		{
			var question = dojo.replace(this._("Do you really want to {verb} the '{id}' package?"),{verb: verb, id: id});

			umc.dialog.confirm(question,[
	            {
	            	name:			'cancel',
	            	label:			this._("No")
	            },
	            {
	            	name:			'submit',			// I want to catch <Enter> too
	            	'default':		true,
	            	label:			this._("Yes"),
	            	callback:		dojo.hitch(this, function() {
	            		this._execute_installer(func,id);
	            	})
	            }
			]);
		}
		else
		{
			this._execute_installer(func,id);
		}
	},

	// Starts the installer and switches to progress view.
	_execute_installer: function(func,id) {

		this.moduleStore.umcpCommand('packages/invoke',{'function':func, 'package':id}).then(
			dojo.hitch(this, function(data) {
				this._switch_to_progress(true);
				this._fetch_job_status();			// start logfile polling
			}),
			dojo.hitch(this, function(data) {
				umc.dialog.alert(data.message);
			})
		);
	},

	// switches between normal (search form + result grid) and progress (title + log tail) view
	_switch_to_progress: function(on) {

		if (on)
		{
			this._pane.removeChild(this._grid);
			this._pane.removeChild(this._form);
			this._pane.addChild(this._progress);
			// clear log view from previous content.
			this._logview.set('content','');
			this._pane.addChild(this._logview);
		}
		else
		{
			this._refresh_grid();

			this._pane.removeChild(this._logview);
			this._pane.removeChild(this._progress);
			this._pane.removeChild(this._back);
			this._pane.addChild(this._form);
			this._pane.addChild(this._grid);

		}
	},

	// schedules the next cycle of log file polling.
	// Made this a seperate function since it is called
	// from different places.
	//
	// Avoids starting next cycle if it encounters the job
	// is finished -> then it enables the 'back' button.
	_start_next_job_cycle: function() {

		this.moduleStore.umcpCommand('packages/running').then(
			dojo.hitch(this, function(data) {
				if (data.result)	// running?
				{
					window.setTimeout(dojo.hitch(this, function() {
						this._fetch_job_status();
					}),1000);
				}
				else
				{
					this._progress.set('content',this._("The current installer job is now finished."));
					this._pane.addChild(this._back);
				}
			}),
			dojo.hitch(this, function(data) {
				umc.dialog.notify(data.message);
				this._pane.addChild(this._back);
			})
		);

	},

	// Timeout handler that fetches the output of the current
	// installer job.
	_fetch_job_status: function() {

		this.moduleStore.umcpCommand('packages/logview',{count:-1}).then(
			dojo.hitch(this, function(data) {
				if (data.result != this._last_log_stamp)
				{
					this._last_log_stamp = data.result;
					// log file content changed -> fetch it.
					this.moduleStore.umcpCommand('packages/logview',{count:0}).then(
						dojo.hitch(this, function(data) {
							this._logview.set('content',data.result.join('<br/>'));
							this._start_next_job_cycle();
						}),
						dojo.hitch(this, function(data) {
							// error callback
							umc.dialog.notify(data.message);
							this._pane.addChild(this._back);	// allow the 'back' button on error.
						})
					);
				}
				else
				{
					// log file content unchanged, only continue polling.
					this._start_next_job_cycle();
				}
			}),
			dojo.hitch(this, function(data) {
				// error callback
				umc.dialog.notify(data.message);
				this._pane.addChild(this._back);	// allow the 'back' button on error.
			})
		);
	}

});
