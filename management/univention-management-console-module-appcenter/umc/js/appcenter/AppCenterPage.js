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
	"dojo/query",
	"dojo/dom-class",
	"dojo/store/Memory",
	"dojo/regexp",
	"dojox/image/LightboxNano",
	"umc/dialog",
	"umc/tools",
	"umc/modules/lib/server",
	"umc/widgets/Page",
	"umc/widgets/ProgressBar",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/Text",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/TextBox",
	"umc/widgets/CheckBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"umc/widgets/Button",
	"umc/widgets/GalleryPane",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, array, when, query, domClass, Memory, regexp, Lightbox, dialog, tools, libServer, Page, ProgressBar, ConfirmDialog, Text, ExpandingTitlePane, TextBox, CheckBox, ContainerWidget, LabelPane, Button, GalleryPane, _) {

	var _SearchWidget = declare("umc.modules.appcenter._SearchWidget", [ContainerWidget], {

		category: null,

		style: 'overflow: auto;',

		buildRendering: function() {
			this.inherited(arguments);

			var widthContainer = new ContainerWidget();
			this._searchTextBox = new TextBox({
				label: _("Search term"),
				style: 'width: 135px;'
			});
			var searchLabel = new LabelPane({
				content: this._searchTextBox
			});
			widthContainer.addChild(searchLabel);
			this.addChild(widthContainer);

			this._categoryContainer = new ContainerWidget({
				label: _("Categories")
			});
			var categoryLabel = new LabelPane({
				content: this._categoryContainer
			});
			this.addChild(categoryLabel);
		},

		postCreate: function() {
			this.inherited(arguments);
			this._searchTextBox.on('keyup', lang.hitch(this, 'onSearch'));
		},

		_getValueAttr: function() {
			return this._searchTextBox.get('value');
		},

		_getCategoryAttr: function() {
			return this.category;
		},

		_setCategoriesAttr: function(categories) {
			// remove all existing categories
			array.forEach(this._categoryContainer.getChildren(), lang.hitch(this, function(category) {
				this._categoryContainer.removeChild(category);
				category.destroyRecursive();
			}));

			// add new categories
			this._categoryContainer.addChild(new Button({
				label: _('All'),
				callback: lang.hitch(this, function() {
					this.category = null;
					this._updateCss();
					this.onSearch();
				})
			}));
			array.forEach(categories, lang.hitch(this, function(category) {
				this._categoryContainer.addChild(new Button({
					label: category,
					callback: lang.hitch(this, function() {
						this.category = category;
						this._updateCss();
						this.onSearch();
					})
				}));
			}));

			this._updateCss();
		},

		_updateCss: function() {
			var categories = this._categoryContainer.getChildren();
			var label;
			array.forEach(categories, lang.hitch(this, function(category) {
				label = category.get('label');
				if (this.category == label || (! this.category && label == _('All'))) {
					domClass.add(category.domNode, 'umcCategorySelected');
				} else {
					domClass.remove(category.domNode, 'umcCategorySelected');
				}
			}));
		},

		onSearch: function() {
		}
	});

	var formatTxt = function(txt) {
		// don't allow HTML
		txt = txt.replace(/</g, '&lt;');
		txt = txt.replace(/>/g, '&gt;');

		// insert links
		txt = txt.replace(/(http:\/\/\S*)\>/g, '<a href="$1">$1</a>');

		// format line breakes
		txt = txt.replace(/\n\n\n/g, '\n<br>\n<br>\n<br>\n');
		txt = txt.replace(/\n\n/g, '\n<br>\n<br>\n');

		return txt;
	};

	return declare("umc.modules.appcenter.AppCenterPage", [ Page ], {

		_udm_accessible: false, // license depends on udm
		standby: null, // parents standby method must be passed. weird IE-Bug (#29587)

		// the widget's class name as CSS class
		'class': 'umcAppCenter',

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

			this._progressBar = new ProgressBar();
			this.own(this._progressBar);

			this._searchWidget = new _SearchWidget({
				region: 'left'
			});
			this.addChild(this._searchWidget);

			var titlePane = new ExpandingTitlePane({
				title: _('Applications')
			});

			this._grid = new GalleryPane({
				baseClass: "umcAppCenter",

				style: 'height: 100%; width: 100%;',

				getIconClass: function(item) {
					return tools.getIconClass(item.icon, 50, 'umcAppCenter');
				},

				getStatusIconClass: function(item) {
					var iconClass = '';
					if (item.can_update) {
						iconClass = tools.getIconClass('appcenter-can_update', 24, 'umcAppCenter');
					} else if (item.is_installed) {
						iconClass = tools.getIconClass('appcenter-is_installed', 24, 'umcAppCenter');
					}
					return iconClass;
				}
			});

			titlePane.addChild(this._grid);
			this.addChild(titlePane);

			tools.getUserPreferences().then(lang.hitch(this, function(prefs) {
				if (prefs.appcenterSeen === 'yes') {
					// load apps
					this.updateApplications();
				} else {
					dialog.confirmForm({
						title: _('Univention App Center'),
						widgets: [
							{
								type: Text,
								name: 'help_text',
								content: '<div style="width: 535px"><p>' + _('Univention App Center is the simplest method to install or uninstall applications on Univention Corporate Server.') + '</p>' +
								'<p>' + _('Univention always receives an estranged notification for statistical purposes upon installation and uninstallation of an application in Univention App Center that is only saved at Univention for data processing and will not be forwarded to any third party.') + '</p>' +
								'<p>' + _('Depending on the guideline of the respective application vendor an updated UCS license key with so-called key identification (Key ID) is required for the installation of an application. In this case, the Key ID will be sent to Univention together with the notification. As a result the application vendor receives a message from Univention with the following information:') +
									'<ul>' +
										'<li>' + _('Name of the installed application') + '</li>' +
										'<li>' + _('Registered email address') + '</li>' +
									'</ul>' +
								_('The description of every application includes a respective indication for such cases.') + '</p>' +
								'<p>' + _('If your UCS environment does not have such a key at it\'s disposal (e.g. UCS Free-for-personal-Use Edition) and the vendor requires a Key ID, you will be asked to request an updated license key directly from Univention. Afterwards the new key can be applied.') + '</p>' +
								'<p>' + _('The sale of licenses, maintenance or support for the applications uses the default processes of the respective vendor and is not part of Univention App Center.') + '</p></div>'
							},
							{
								type: CheckBox,
								name: 'show_again',
								label: _("Show this message again")
							}
						],
						buttons: [{
							name: 'submit',
							'default': true,
							label: _('Continue')
						}]
					}).then(
						lang.hitch(this, function(data) {
							tools.setUserPreference({appcenterSeen: data.show_again ? 'no' : 'yes'});
							this.updateApplications();
						}),
						lang.hitch(this, function() {
							this.updateApplications();
						})
					);
				}
			}), lang.hitch(this, function() {
				this.updateApplications();
			}));
		},

		postCreate: function() {
			this.inherited(arguments);

			// register event handlers
			this._searchWidget.on('search', lang.hitch(this, 'filterApplications'));

			this.own(this._grid.on('.dgrid-row:click', lang.hitch(this, function(evt) {
				this._show_details(this._grid.row(evt));
			})));
		},

		startup: function() {
			this.inherited(arguments);
		},

		// inspired by PackagesPage._show_details
		_show_details: function(app) {
			this.standby(true);

			tools.umcpCommand('appcenter/get', {'application': app.id}).then(
				lang.hitch(this, function(data) {
					this.standby(false);
					var width = 550;	// mimic the default of dialog.confirm

					var label_style = 'vertical-align:top;text-align:right;padding-left:1em;padding-right:.5em;white-space:nowrap;font-weight:bold;';
					var data_style	= 'vertical-align:top;padding-bottom:.25em;';

					var txt = "<h1>" + lang.replace(_("Details for Application '{name}'"), data.result) + "</h1>";
					txt += lang.replace("<table style=\"width: {0}px;\">\n", [ width ]);
					var fields = this._detail_field_order();
					array.forEach(fields, lang.hitch(this, function(key) {
						var label = this._detail_field_label(key);
						var value = data.result[key];
						var detail_func = this['_detail_field_custom_' + key];
						if (detail_func) {
							value = lang.hitch(this, detail_func)(data.result);
							if (!value) {
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
					var app = data.result;
					if (!app.allows_using && this._udm_accessible && !app.can_uninstall) {
						buttons.push({
							name: 'request',
							label: _("Install"), // call it Install, although it is request
							callback: lang.hitch(this, function() {
								this._show_license_request();
							})
						});
					}
					if (app.allows_using && app.can_install) {
						buttons.push({
							name: 'install',
							label: _("Install"),
							callback: lang.hitch(this, function() {
								var masterInstallConfirmend = 'yes';
								if (app.defaultpackagesmaster && app.defaultpackagesmaster.length && app.show_ldap_schema_confirmation) {
									masterInstallConfirmend = dialog.confirm(
										_('This application requires an extension of the LDAP schema.') + ' ' +
										_('Was the domain prepared as asked in the dialog before?'), [{
											label: _('No'),
											name: 'no',
											'default': true
										}, {
											label: _('Yes'),
											name: 'yes'
										}]);
								}
								when(masterInstallConfirmend, lang.hitch(this, function(answer) {
									if (answer === 'yes') {
										if (app.licenseagreement) {
											// before installing, user must agree on license terms
											var content = '<h1>' + _('License agreement') + '</h1>';
											content += '<div style="max-height:250px; overflow:auto;">' +
												formatTxt(app.licenseagreement) +
												'</div>';
											dialog.confirm(content, [{
												name: 'decline',
												label: _('Cancel'),
												'default': true
											}, {
												name: 'accept',
												label: _('Accept license')
											}], _('License agreement')).then(lang.hitch(this, function(response) {
												if (response == 'accept') {
													this._call_installer('install', app);
												}
											}));
										} else {
											this._call_installer('install', app);
										}
									}
								}));
							})
						});
					}
					if (app.allows_using && app.can_update) {
						buttons.push({
							name: 'update',
							label: _("Upgrade"),
							callback: lang.hitch(this, function() {
								if (app.readmeupdate) {
									// before updating, show update README file
									var content = '<h1>' + _('Upgrade information') + '</h1>';
									content += '<div style="max-height:250px; overflow:auto;">' +
										formatTxt(app.readmeupdate) +
										'</div>';
									dialog.confirm(content, [{
										name: 'decline',
										label: _('Cancel'),
										'default': true
									}, {
										name: 'update',
										label: _('Upgrade')
									}], _('Upgrade information')).then(lang.hitch(this, function(response) {
										if (response == 'update') {
											this._call_installer('update', app);
										}
									}));
								}
								else {
									this._call_installer('update', app);
								}
							})
						});
					}
					if (app.can_uninstall) {
						buttons.push({
							name: 'uninstall',
							label: _("Uninstall"),
							callback: lang.hitch(this, function() {
								this._call_installer('uninstall', app);
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
						content: txt
					});
					var confirmDialog = new ConfirmDialog({
						title: _('Application details'),
						message: dialogText,
						options: buttons
					});

					// decorate screenshot images with a Lightbox
					var lightbox;
					query('.umcScreenshot', confirmDialog.domNode).forEach(function(imgNode) {
						lightbox = new Lightbox({ href: imgNode.src }, imgNode);
						imgNode.onload = function() {
							confirmDialog.resize();
						};
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
				})
			);
		},

		_call_installer: function(func, app, force) {
			var verb = '';
			var verb1 = '';
			switch(func) {
			case 'install':
				verb = _("install");
				verb1 = _("installing");
				break;
			case 'uninstall':
				verb = _("uninstall");
				verb1 = _("uninstalling");
				break;
			case 'upgrade':
				verb = _("upgrade");
				verb1 = _("upgrading");
				break;
			}

			var confirmationRequired = false;
			var commandArguments = {
				'function': func,
				'application': app.id,
				'force': force === true
			};

			this.standby(true);
			tools.umcpCommand('appcenter/invoke', commandArguments).then(
				lang.hitch(this, function(data) {
					this.standby(false);
					var result = data.result;
					var txt = '';
					var label = '';
					var headline = '';
					var buttons = [];

					if (!result.can_continue) {
						confirmationRequired = true;
						if (result.remove.length) {
							label = _('The following packages will be removed:');
							txt += '<p>' + label + '<ul><li>' + result.remove.join('</li><li>') + '</li></ul></p>';
							headline = lang.replace(_("Do you really want to {verb} {ids}?"),
										{verb: verb, ids: app.name});
							buttons = [{
								name: 'cancel',
								'default': true,
								label: _("No")
							}, {
								name: 'submit',
								label: _("Yes"),
								callback: lang.hitch(this, function() {
									this._call_installer(func, app, true);
								})
							}];
						}
						if (result.broken.length) {
							label = _('This operation causes problems in the following packages that cannot be resolved:');
							txt += '<p>' + label + '<ul><li>' + result.broken.join('</li><li>') + '</li></ul></p>';
							headline = _('You cannot continue');
							buttons = [{
								name: 'cancel',
								'default': true,
								label: _("Cancel")
							}];
						}
					}

					if (confirmationRequired) {
						dialog.confirm('<p><strong>' + headline + '</strong></p>' + txt, buttons);
					} else {
						var progressMessage = lang.replace(_("Going to {verb} Application '{name}'"),
										   {verb: verb, name: app.name});

						this._switch_to_progress_bar(progressMessage);
					}
				}),
				lang.hitch(this, function(data) {
					this.standby(false);
				})
			);
		},

		_detail_field_custom_website: function(values) {
			var name = values.name;
			var website = values.website;
			if (name && website) {
				return '<a href="' + website + '" target="_blank">' + name + '</a>';
			}
		},

		_detail_field_custom_vendor: function(values) {
			var vendor = values.vendor;
			var website = values.websitevendor;
			if (vendor && website) {
				return '<a href="' + website + '" target="_blank">' + vendor + '</a>';
			} else if (vendor) {
				return vendor;
			}
		},

		_detail_field_custom_maintainer: function(values) {
			var maintainer = values.maintainer;
			var vendor = values.vendor;
			if (vendor == maintainer) {
				return null;
			}
			var website = values.websitemaintainer;
			if (maintainer && website) {
				return '<a href="' + website + '" target="_blank">' + maintainer + '</a>';
			} else if (maintainer) {
				return maintainer;
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
				var txt = _('For the installation of this application an updated UCS license key with a so-called key identification (Key ID) is required.');
				if (!this._udm_accessible) {
					txt += ' ' + _('You need to have access to the Univention Directory Manager (UDM) module to fully use the App Center.');
				}
				return txt;
			}
		},

		_detail_field_custom_defaultpackagesmaster: function(values) {
			var master_packages = values.defaultpackagesmaster;
			var can_install = values.can_install;
			var allows_using = values.allows_using;
			if (allows_using && values.cannot_install_reason == 'not_joined') {
				return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('The system has to join a domain before the application can be installed!');
			}
			if (allows_using && can_install && master_packages && master_packages.length) {
				// prepare a command with max 50 characters length per line
				var MAXCHARS = 50;
				var cmdLine = lang.replace('univention-add-app {component_id} ', values);
				var cmdLines = [];
				array.forEach(master_packages, function(icmd) {
					if (icmd.length + cmdLine.length > MAXCHARS) {
						cmdLines.push(cmdLine);
						cmdLine = '    ';
					}
					cmdLine += icmd + ' ';
				});
				if (cmdLine) {
					cmdLines.push(cmdLine);
				}
				var commandStr = cmdLines.join('\\\n');

				// print out note for master and backup servers
				if (values.is_master) {
					return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following commands as root on all of your backup servers.') + '</td></tr><tr><td colspan="2"><pre>' + commandStr + '</pre>';
				} else {
					return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Be sure to execute the following commands as root on your DC master and all of your backup servers <em>prior</em> to installing the application on this system.') + '</td></tr><tr><td colspan="2"><pre>' + commandStr + '</pre>';
				}
			}
		},

		_detail_field_custom_cannot_install_reason: function(values) {
			var cannot_install_reason = values.cannot_install_reason;
			var cannot_install_reason_detail = values.cannot_install_reason_detail;
			if (!values.allows_using) {
				return '';
			}

			var txt = '';
			if (cannot_install_reason == 'conflict') {
				txt = _('This application conflicts with the following Applications/Packages. Uninstall them first.');
				txt += '<ul><li>' + cannot_install_reason_detail.join('</li><li>') + '</li></ul>';
			}
			if (cannot_install_reason == 'wrong_serverrole') {
				txt = _('<p>This application cannot be installed on the current server role (%s). In order to install the application, one of the following roles is necessary: %s</p>', cannot_install_reason_detail, values.serverrole.join(', '));
			}
			return txt;
		},

		_detail_field_custom_categories: function(values) {
			if (values.categories) {
				return values.categories.join(', ');
			}
		},

		_detail_field_custom_notifyvendor: function(values) {
			var maintainer = values.maintainer && values.maintainer != values.vendor;
			if (values.notifyvendor) {
				if (maintainer) {
					return _('This application will inform the maintainer if you (un)install it.');
				} else {
					return _('This application will inform the vendor if you (un)install it.');
				}
			} else {
				if (maintainer) {
					return _('This application will not inform the maintainer if you (un)install it.');
				} else {
					return _('This application will not inform the vendor if you (un)install it.');
				}
			}
		},

		_detail_field_custom_screenshot: function(values) {
			if (values.screenshot) {
				return lang.replace('<img src="{url}" style="max-width: 90%; height:200px;" class="umcScreenshot" />', {
					url: values.screenshot,
					id: this.id
				});
			}
		},

		_detail_field_order: function() {
			return [
				//'name',
				'vendor',
				'maintainer',
				'contact',
				'website',
				'version',
				'categories',
				'longdescription',
				'screenshot',
				'defaultpackagesmaster',
				'cannot_install_reason',
				'notifyvendor',
				'allows_using'
			];
		},

		_detail_field_label: function(key) {
			var labels = {
				// 'name': _("Name"),
				'vendor': _("Vendor"),
				'maintainer': _("Maintainer"),
				'contact': _("Contact"),
				'website': _("Website"),
				'version': _('Version'),
				'categories': _("Section"),
				'longdescription': _("Description"),
				'screenshot': _("Screenshot"),
				'defaultpackagesmaster': _("Packages for master system"),
				'cannot_install_reason': _("Conflicts"),
				'notifyvendor': _("Email notification"),
				'allows_using': _("UCS License Key")
			};
			return labels[key];
		},

		getApplications: function() {
			if (!this._applications) {
				return tools.umcpCommand('appcenter/query', {}).then(lang.hitch(function(data) {
					// sort by name
					this._applications = data.result;
					this._applications.sort(tools.cmpObjects({
						attribute: 'name',
						ignoreCase: true
					}));
					return this._applications;
				}));
			}
			return this._applications;
		},

		updateApplications: function() {
			// query all applications
			this._applications = null;
			this.standby(true);
			when(this.getApplications(),
				lang.hitch(this, function(applications) {
					this.standby(false);
					this._grid.set('store', new Memory({data: applications}));

					var categories = [];
					array.forEach(applications, function(application) {
						array.forEach(application.categories, function(category) {
							if (array.indexOf(categories, category) < 0) {
							     categories.push(category);
							}
						});
					});
					this._searchWidget.set('categories', categories.sort());
				}),
				lang.hitch(this, function() {
					this.standby(false);
				})
			);
		},

		filterApplications: function() {
			// sanitize the search pattern
			var searchPattern = lang.trim(this._searchWidget.get('value'));
			searchPattern = regexp.escapeString(searchPattern);
			searchPattern = searchPattern.replace(/\\\*/g, '.*');
			searchPattern = searchPattern.replace(/ /g, '\\s+');

			var regex  = new RegExp(searchPattern, 'i');
			var category = this._searchWidget.get('category');

			var query = {
				test: function(value, obj) {
					var string = lang.replace(
						'{name} {description} {categories}', {
							name: obj.name,
							description: obj.description,
							categories: category ? '' : obj.categories.join(' ')
						});
					return regex.test(string);
				}
			};
			this._grid.query.name = query;

			if (! category) {
				delete this._grid.query.categories;
			} else {
				this._grid.query.categories = {
					test: function(categories) {
						return (array.indexOf(categories, category) >= 0);
					}
				};
			}

			this._grid.refresh();
		},

		_show_license_request: function() {
			if (this._udm_accessible) {
				dialog.confirmForm({
					title: _('Request updated license key with identification'),
					widgets: [
						{
							type: Text,
							name: 'help_text',
							content: '<div style="width: 535px"><p>' + _('The installation of applications with Univention App Center requires an individually issued license key with a unique key identification. You are currently using a license key without identification. Please fill in the form and provide a valid email address. Afterwards an updated license will be sent to you in a couple of minutes that can be applied and updated directly in the license dialog.') + '</p>' +
							'<p>' + _('The UCS system sends your current license key to Univention. The key will be extended by the identification and will be sent back to the provided email address. The license scope remains unchanged.') + '</p>' +
							'<p>' + _('Right after this form, you will see another dialog where you can upload your new license.') + '</p></div>'
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
				}).then(lang.hitch(this, function(values) {
					this.standby(true);
					tools.umcpCommand('appcenter/request_new_license', values).then(
						lang.hitch(this, function(data) {
							// cannot require in the beginning as
							// udm might be not installed
							this.standby(false);
							require(['umc/modules/udm/LicenseDialog'], function(LicenseDialog) {
								if (data.result) {
									var dlg = new LicenseDialog();
									dlg.show();
								}
							});
						}),
						lang.hitch(this, function() {
							this.standby(false);
						}));
				}));
			}
		},

		_switch_to_progress_bar: function(msg) {
			this.standby(true, this._progressBar);
			this._progressBar.reset(msg);
			this._progressBar.auto('appcenter/progress',
				{},
				lang.hitch(this, '_restartOrReload')
			);
		},

		_restartOrReload: function() {
			// update the list of apps
			this.updateApplications();

			// TODO: only if necessary? these apps probably will require a restart
			libServer.askRestart(_('A restart of the UMC server components may be necessary for the software changes to take effect.'));
		}

	});
});
