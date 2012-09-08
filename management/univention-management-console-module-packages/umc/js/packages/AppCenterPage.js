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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/when",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/ProgressBar",
	"umc/widgets/ContainerWidget",
	"umc/widgets/CategoryPane",
	"umc/widgets/ConfirmDialog",
	"umc/modules/lib/server",
	"umc/modules/packages/Form",
	"umc/i18n!umc/modules/packages"
], function(declare, lang, array, when, dialog, tools, Page, StandbyMixin, ProgressBar, ContainerWidget, CategoryPane, ConfirmDialog, libServer, Form, _) {
	return declare("umc.modules.packages.AppCenterPage", [ Page, StandbyMixin ], {

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				title: _("App Center"),
				headerText: _("Manage Applications for UCS"),
				helpText: _("This page lets you install and remove applications that enhance your UCS installation.")
			});
		},

		buildRendering: function() {

			this.inherited(arguments);

			var widgets =
			[
				{
					type: 'TextBox',
					name: 'name',
					label: _("Name")
				}
			];

			var layout =
			[
				{
					label: _("Search"),
					layout:
					[
						['name']
					]
				}
			];
		
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				scrollable: true
			});
			try {
				// hide form
				this._form._container.getChildren()[0].toggle();
			} catch(e) {
			}
			var widget = this._form.getWidget('name');
			this._form.connect(widget, 'onKeyUp', lang.hitch(this, 'filterApplications'));
			this.container = new ContainerWidget({
				scrollable: true
			});
			this.addChild(this.container);
			this.container.addChild(this._form);

			this._progressBar = new ProgressBar();

			// load apps
			this.standby(true);
			when(this.getApplications(), lang.hitch(this, function(applications) {
				this.standby(false);
				this._category_pane = CategoryPane({
					useCategories: true,
					modules: applications,
					title: 'Applications',
					open: true
				});
				this._category_pane.on('openmodule', lang.hitch(this, '_show_details'));
				this.container.addChild(this._category_pane);
			}));
			//this._form.load({}); // ID doesn't matter here but must be dict
		},

		// inspired by PackagesPage._show_details
		_show_details: function(app) {
			this.standby(true);

			tools.umcpCommand('packages/app_center/get', {'application': app.id}).then(
				lang.hitch(this, function(data) {
					// TODO:
					// email_sending AND NOT email_agreed

					this.standby(false);

					var head_style	= 'font-size:120%;font-weight:bold;margin:.5em;text-decoration:underline;';
					var label_style = 'vertical-align:top;text-align:right;padding-left:1em;padding-right:.5em;white-space:nowrap;font-weight:bold;';
					var data_style	= 'vertical-align:top;padding-bottom:.25em;';

					var txt = "<p style='" + head_style + "'>" +
						lang.replace(_("'{id} - {name}'"), data.result) +
						"</p>";
					txt += "<table>\n";
					var width = 550;	// mimic the default of dialog.confirm
					array.forEach(this._detail_field_order(), lang.hitch(this, function(key) {
						var label = this._detail_field_label(key);
						var value = data.result[key];
						var detail_func = this['_detail_field_custom_' + key];
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
							label: _("Install"),
							callback: lang.hitch(this, function() {
								this._call_installer('install', data.result.id);
							})
						});
					}
					if (data.result.can_uninstall) {
						buttons.push({
							name: 'uninstall',
							label: _("Uninstall"),
							callback: lang.hitch(this, function() {
								this._call_installer('uninstall', data.result.id);
							})
						});
					}
					// always: a button to close the dialog.
					buttons.push({
						name: 'cancel',
						'default': true,
						label: _("Close")
					});

					var confirmDialog = new ConfirmDialog({
						title: _('Application details'),
						style: lang.replace('min-width:500px;max-width: {width}px;', {width: width}), 		// dialog.confirm doesn't exceed 550px
						message: txt,
						options: buttons
					});

					// connect to 'onConfirm' event to close the dialog in any case
					confirmDialog.on('confirm', function() {
						confirmDialog.close();
					});

					// show the confirmation dialog
					confirmDialog.show();

				}),
				lang.hitch(this, function(data) {
					this.standby(false);
					dialog.alert(data.message);
				})
			);
		},

		_call_installer: function(func, id) {
			this.standby(true);
			var verb = '';
			switch(func) {
				case 'install':
					verb = _("install");
					break;
				case 'uninstall':
					verb = _("uninstall");
					break;
				case 'upgrade':
					verb = _("upgrade");
					break;
			}
			var msg = lang.replace(_("Going to {verb} Application '{id}'"), {verb: verb, id: id});
			// TODO: confirm
			tools.umcpCommand('packages/app_center/invoke', {'function': func, 'application': id}).then(
				lang.hitch(this, function(data) {
					this.standby(false);
					if (data.result) {
						this._switch_to_progress_bar(msg);
					} else {
						dialog.alert(_('Application not found: ') + id);
					}
				}),
				lang.hitch(this, function(data) {
					this.standby(false);
					dialog.alert(data.message);
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
			var labels = {
				'name': _("Name"),
				'categories': _("Section"),
				'commercial_support': _("Commercial support"),
				'description': _("Description"),
				'email_sending': _("Email notification"),
				'master_packages': _("Packages for master system")
			};
			return labels[key];
		},

		getApplications: function() {
			if (this._applications === undefined) {
				return tools.umcpCommand('packages/app_center/query', {}).then(lang.hitch(function(data) {
					this._applications = data.result;
					return this._applications;
				}));
			}
			return this._applications;
		},

		filterApplications: function() {
			var search_string = this._form.getWidget('name').get('value').toLowerCase();
			array.forEach(this._category_pane.getChildren(), function(app) {
				var visible = false;
				if (!search_string) {
					visible = true;
				} else {
					if (app.label.toLowerCase().search(search_string) > -1) {
						visible = true;
					} else {
						array.forEach(app.categories, function(category) {
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
				lang.hitch(this, '_restartOrReload')
			);
		},

		_restartOrReload: function() {
			libServer.askRestart(_('A restart of the UMC server components may be necessary for the software changes to take effect.')).then(
			function() {
				// if user confirms, he is redirected to the login page
				// no need to do anythin fancy here :)
			},
			lang.hitch(this, function() {
				// user canceled -> switch back to initial view
				this.standby(false);
			}));
		}

	});
});
