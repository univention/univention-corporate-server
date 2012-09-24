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
/*global define require*/

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
	"umc/widgets/Text",
	"umc/modules/lib/server",
	"umc/modules/packages/Form",
	"umc/widgets/TextBox",
	"umc/i18n!umc/modules/packages"
], function(declare, lang, array, when, dialog, tools, Page, StandbyMixin, ProgressBar, ContainerWidget, CategoryPane, ConfirmDialog, Text, libServer, Form, TextBox, _) {
	return declare("umc.modules.packages.AppCenterPage", [ Page, StandbyMixin ], {

		_udm_accessible: false, // license depends on udm

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				title: _("App management"),
				headerText: _("Manage Applications for UCS"),
				helpText: _("This page lets you install and remove applications that enhance your UCS installation.")
			});
		},

		buildRendering: function() {

			this.inherited(arguments);

			var widgets =
			[
				{
					type: TextBox,
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
			widget.on('keyup', lang.hitch(this, 'filterApplications'));
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
				this._category_pane = new CategoryPane({
					useCategories: true,
					modules: applications,
					title: _('Applications'),
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
					this.standby(false);

					var head_style	= 'font-size:120%;font-weight:bold;margin:.5em;text-decoration:underline;';
					var label_style = 'vertical-align:top;text-align:right;padding-left:1em;padding-right:.5em;white-space:nowrap;font-weight:bold;';
					var data_style	= 'vertical-align:top;padding-bottom:.25em;';

					var txt = "<p style='" + head_style + "'>" +
						lang.replace(_("Details for Application '{name}'"), data.result) +
						"</p>";
					txt += "<table>\n";
					var width = 550;	// mimic the default of dialog.confirm
					var fields;
					if (data.result.allows_using) {
						fields = this._detail_field_order();
					} else {
						fields = ['allows_using'];
					}
					array.forEach(fields, lang.hitch(this, function(key) {
						var label = this._detail_field_label(key);
						var value = data.result[key];
						var detail_func = this['_detail_field_custom_' + key];
						if (undefined !== detail_func) {
							value = lang.hitch(this, detail_func)(data.result);
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
					if (!data.result.allows_using && this._udm_accessible) {
						buttons.push({
							name: 'request',
							label: _("Request"),
							callback: lang.hitch(this, function() {
								this._show_license_request();
							})
						});
					}
					if (data.result.allows_using && data.result.can_install) {
						buttons.push({
							name: 'install',
							label: _("Install"),
							callback: lang.hitch(this, function() {
								this._call_installer('install', data.result.id, data.result.name);
							})
						});
					}
					if (data.result.allows_using && data.result.can_uninstall) {
						buttons.push({
							name: 'uninstall',
							label: _("Uninstall"),
							callback: lang.hitch(this, function() {
								this._call_installer('uninstall', data.result.id, data.result.name);
							})
						});
					}
					// always: a button to close the dialog.
					buttons.push({
						name: 'cancel',
						'default': true,
						label: _("Close")
					});

					var dialogText = new Text({
						'class': 'umcConfirmDialogText',
						style: 'overflow:auto', // commands can be long...
						content: txt
					});
					var confirmDialog = new ConfirmDialog({
						title: _('Application details'),
						style: lang.replace('min-width:500px;max-width:{width}px;', {width: width}), // dialog.confirm doesn't exceed 550px
						message: dialogText,
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

		_call_installer: function(func, id, name) {
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
			var msg = lang.replace(_("Going to {verb} Application '{name}'"), {verb: verb, id: name});
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

		_detail_field_custom_vendor: function(values) {
			var vendor = values.vendor;
			var website = values.website;
			if (vendor && website) {
				return '<a href="' + website + '" target="_blank">' + vendor + '</a>';
			} else if (vendor) {
				return vendor;
			}
		},

		_detail_field_custom_contact: function(values) {
			var contact = values.contact;
			if (contact) {
				return '<a href="mailto:' + contact + '">' + contact + '</a>';
			}
		},

		_detail_field_custom_allows_using: function(values) {
			var allows_using = values.allows_using;
			if (!allows_using) {
				if (this._udm_accessible) {
					return _('Your current license forbids to use this application.') + ' ' + _('You can request an extended license from Univention for free.');
				} else {
					return _('Your current license forbids to use this application.') + ' ' + _('You need to have access to the Univention Directory Manager (UDM) module to fully use the App Center.');
				}
			}
		},

		_detail_field_custom_defaultpackagesmaster: function(values) {
			var master_packages = values.defaultpackagesmaster;
			var can_install = values.can_install;
			if (can_install && master_packages && master_packages.length) {
				if (!values.is_joined) {
					return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Join a domain before you install this application!');
				}
				var commands = [
					lang.replace('ucr set repository/online/component/{id}=enabled \\', values),
					lang.replace('        repository/online/component/{id}/parts=maintained \\', values),
					lang.replace('        repository/online/component/{id}/version=current \\', values),
					lang.replace('        repository/online/component/{id}/server={server}', values),
					lang.replace('univention-install {packages}', {packages: master_packages.join(' ')})
				].join('\n');
				if (values.is_master) {
					return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following commands as root on all of your backup servers.') + '<pre>' + commands + '</pre>';
				} else {
					return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following commands as root on your DC master and all of your backup servers <em>prior</em> to installing the application on this system.') + '<pre>' + commands + '</pre>';
				}
			}
		},

		_detail_field_custom_cannot_install_reason: function(values) {
			var cannot_install_reason = values.cannot_install_reason;
			var cannot_install_reason_detail = values.cannot_install_reason_detail;
			if (cannot_install_reason == 'conflict') {
				var txt = _('This application conflicts with the following Applications/Packages. Uninstall them first.');
				txt += '<ul><li>' + cannot_install_reason_detail.join('</li><li>') + '</li></ul>';
				return txt;
			}
		},

		_detail_field_custom_categories: function(values) {
			if (values.categories) {
				return values.categories.join(', ');
			}
		},

		_detail_field_custom_emailrequired: function(values) {
			if (values.emailrequired) {
				return _('This application will inform the vendor if you (un)install it.');
			} else {
				return _('This application will not inform the vendor if you (un)install it.');
			}
		},

		_detail_field_order: function() {
			return ['name',
				'version',
				'vendor',
				'contact',
				'categories',
				'longdescription',
				'emailrequired',
				'allows_using',
				'defaultpackagesmaster',
				'cannot_install_reason'
			];
		},

		_detail_field_label: function(key) {
			var labels = {
				'name': _("Name"),
				'vendor': _("Vendor"),
				'website': _('Website'),
				'contact': _("Contact"),
				'categories': _("Section"),
				'version': _('Version'),
				'longdescription': _("Description"),
				'emailrequired': _("Email notification"),
				'allows_using': _("License restrictions"),
				'defaultpackagesmaster': _("Packages for master system"),
				'cannot_install_reason': _("Conflicts")
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

		_show_license_request: function() {
			if (this._udm_accessible) {
				dialog.confirmForm({
					title: _('Request a new License'),
					widgets: [
						{
							type: Text,
							name: 'help_text',
							content: '<p>' + _('Some applications require an advanced license.') + ' ' + _('Please complete the form below and you will be sent a new license to your mail address. Right after this form, you will see another dialog where you can upload your new license.') + '</p>'
						},
						{
							type: TextBox,
							name: 'email',
							required: true,
							regExp: '.+@.+',
							label: _("Email address")
						}
					],
					autoValidate: true
				}).then(function(values) {
					tools.umcpCommand('packages/app_center/request_new_license', values).then(function(data) {
						// cannot require in the beginning as
						// udm might be not installed
						require(['umc/modules/udm/LicenseDialog'], function(LicenseDialog) {
							if (data.result) {
								var dlg = new LicenseDialog();
								dlg.show();
							}
						});
					});
				});
			}
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
			// TODO: only if necessary? these apps probably will require a restart
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
