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
/*global dojo umc */

dojo.provide("umc.modules._packages.AppCenterPage");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.tools");
dojo.require("umc.modules._packages.store");
//dojo.require("umc.store");

dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.ProgressBar");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.CategoryPane");
dojo.require("umc.modules._packages.Form");
//dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules._packages.AppCenterPage", [ umc.widgets.Page, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.packages',

	postMixInProperties: function() {
		this.inherited(arguments);

		dojo.mixin(this, {
			title: this._("App Center"),
			headerText: this._("Manage Applications for UCS"),
			helpText: this._("This page lets you install and remove applications that enhance your UCS installation.")
		});
	},

	buildRendering: function() {

		this.inherited(arguments);

		var widgets =
		[
			{
				type: 'TextBox',
				name: 'name',
				label: this._("Name")
			}
		];

		var layout =
		[
			{
				label: this._("Search"),
				layout:
				[
					['name']
				]
			}
		];
	
		this._form = new umc.modules._packages.Form({
			widgets: widgets,
			layout: layout,
			//buttons: buttons,
			//moduleStore: umc.modules._packages.store.getModuleStore('server', 'packages/settings'),
			scrollable: true
		});
		try {
			// hide form
			this._form._container.getChildren()[0].toggle();
		} catch(e) {
		}
		var widget = this._form.getWidget('name');
		this._form.connect(widget, 'onKeyUp', dojo.hitch(this, 'filterApplications'));
		this.container = new umc.widgets.ContainerWidget({
			scrollable: true
		});
		this.addChild(this.container);
		this.container.addChild(this._form);

		this._progressBar = new umc.widgets.ProgressBar();

		// load apps
		this.standby(true);
		dojo.when(this.getApplications(), dojo.hitch(this, function(applications) {
			this.standby(false);
			this._category_pane = umc.widgets.CategoryPane({
				useCategories: true,
				modules: applications,
				title: 'Applications',
				open: true
			});
			this.connect(this._category_pane, 'onOpenModule', dojo.hitch(this, '_show_details'));
			this.container.addChild(this._category_pane);
		}));
		//this._form.load({}); // ID doesn't matter here but must be dict
	},

	// inspired by PackagesPage._show_details
	_show_details: function(app) {
		this.standby(true);

		umc.tools.umcpCommand('packages/app_center/get', {'application': app.id}).then(
			dojo.hitch(this, function(data) {
				// TODO:
				// email_sending AND NOT email_agreed

				this.standby(false);

				var head_style	= 'font-size:120%;font-weight:bold;margin:.5em;text-decoration:underline;';
				var label_style = 'vertical-align:top;text-align:right;padding-left:1em;padding-right:.5em;white-space:nowrap;font-weight:bold;';
				var data_style	= 'vertical-align:top;padding-bottom:.25em;';

				var txt = "<p style='" + head_style + "'>" +
					dojo.replace(this._("'{id} - {name}'"), data.result) +
					"</p>";
				txt += "<table>\n";
				var width = 550;	// mimic the default of umc.dialog.confirm
				dojo.forEach(this._detail_field_order(), dojo.hitch(this, function(key) {
					var label = this._detail_field_label(key);
					var value = data.result[key];
					var detail_func = this['_detail_field_custom_' + key]
					if (undefined !== detail_func) {
						value = detail_func(data.result);
						if (undefined === value) {
							return; // continue
						}
					}
					if (label) {
						txt += "<tr>\n";
						txt += "<td style='" + label_style + "'>" + label + "</td>\n";
						txt += "<td style='" + data_style + "'>" + value + "</td>\n";
						txt += "</tr>\n";
					}
				}));
				txt += "</table>\n";
				var buttons = [];
				if (data.result.can_install) {
					buttons.push({
						name: 'install',
						label: this._("Install"),
						callback: dojo.hitch(this, function() {
							this._call_installer('install', data.result.id);
						})
					});
				}
				if (data.result.can_uninstall) {
					buttons.push({
						name: 'uninstall',
						label: this._("Uninstall"),
						callback: dojo.hitch(this, function() {
							this._call_installer('uninstall', data.result.id);
						})
					});
				}
				// always: a button to close the dialog.
				buttons.push({
					name: 'cancel',
					'default': true,
					label: this._("Close")
				});

				var confirmDialog = new umc.widgets.ConfirmDialog({
					title: this._('Application details'),
					style: dojo.replace('min-width:500px;max-width: {width}px;', {width: width}), 		// umc.dialog.confirm doesn't exceed 550px
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
				this.standby(false);
				umc.dialog.alert(data.message);
			})
		);
	},

	_call_installer: function(func, id) {
		this.standby(true);
		var verb = '';
		switch(func) {
			case 'install':
				verb = this._("install");
				break;
			case 'uninstall':
				verb = this._("uninstall");
				break;
			case 'upgrade':
				verb = this._("upgrade");
				break;
		}
		var msg = dojo.replace(this._("Going to {verb} Application '{id}'"), {verb: verb, id: id});
		// TODO: confirm
		umc.tools.umcpCommand('packages/app_center/invoke', {'function': func, 'application': id}).then(
			dojo.hitch(this, function(data) {
				this.standby(false);
				if (data.result) {
					this._switch_to_progress_bar(msg);
				} else {
					umc.dialog.alert(this._('Application not found: ') + id)
				}
			}),
			dojo.hitch(this, function(data) {
				this.standby(false);
				umc.dialog.alert(data.message);
			})
		);
	},

	_detail_field_custom_master_packages: function(values) {
		var master_packages = values.master_packages;
		if (master_packages) {
			if (!values.is_joined) {
				return '<strong>ATTENTION!</strong> You did not join a domain, but the application requires installation of domain wide packages. Join a domain before you install this application!';
			}
			if (values.is_master) {
				return '<strong>ATTENTION!</strong> The following packages will be installed that change your LDAP schemas and should also be installed on your backup(s): "' + master_packages.join('", "') + '"';
			} else {
				return '<strong>ATTENTION!</strong> <em>Prior</em> to installing this application, you need to install the following packages on your DC master and backup(s): "' + master_packages.join('", "') + '"';
			}
		}
	},

	_detail_field_custom_categories: function(values) {
		return values.categories.join(' and ');
	},

	_detail_field_custom_email_sending: function(values) {
		if (values.email_sending) {
			return 'This application will inform the producer if you (un)install it';
		} else {
			return 'This application will not inform the producer if you (un)install it';
		}
	},

	_detail_field_order: function() {
		return (['name', 
			 'categories',
			 'commercial_support',
			 'description',
			 'master_packages',
			 'email_sending'
		         ]);
	},

	_detail_field_label: function(key) {
		labels = {
			'name': this._("Name"),
			'categories': this._("Section"),
			'commercial_support': this._("Commercial support"),
			'description': this._("Description"),
			'email_sending': this._("Email notification"),
			'master_packages': this._("Packages for master system")
		};
		return labels[key];
	},

	getApplications: function() {
		if (this._applications === undefined) {
			return umc.tools.umcpCommand('packages/app_center/query', {}).then(dojo.hitch(function(data) {
				this._applications = data.result;
				return this._applications;
			}));
		}
		return this._applications;
	},

	filterApplications: function() {
		var search_string = this._form.getWidget('name').get('value').toLowerCase();
		dojo.forEach(this._category_pane.getChildren(), function(app) {
			var visible = false;
			if (!search_string) {
				visible = true;
			} else {
				if (app.label.toLowerCase().search(search_string) > -1) {
					visible = true;
				} else {
					dojo.forEach(app.categories, function(category) {
						if (category.toLowerCase().search(search_string) > -1) {
							visible = true;
							return false; // break
						}
					});
				}
			}
			app.set('style', visible ? 'display:inline-block;' : 'display:none;');
		});
	},

	_switch_to_progress_bar: function(msg) {
		this.standby(true, this._progressBar);
		this._progressBar.reset(msg);
		this._progressBar.auto('packages/app_center/progress',
			{},
			dojo.hitch(this, '_restartOrReload')
		);
	},

	_restartOrReload: function() {
		umc.modules.lib.server.askRestart(this._('A restart of the UMC server components may be necessary for the software changes to take effect.')).then(
		function() {
			// if user confirms, he is redirected to the login page
			// no need to do anythin fancy here :)
		},
		dojo.hitch(this, function() {
			// user canceled -> switch back to initial view
			this.standby(false);
		}));
	}

});
