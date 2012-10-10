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
/*global define require console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/when",
	"dojo/query",
	"dojo/dom-class",
	"dojo/store/Memory",
	"dojox/image/LightboxNano",
	"umc/dialog",
	"umc/tools",
	"umc/i18n!umc/modules/packages",
	"umc/modules/lib/server",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin",
	"umc/widgets/ProgressBar",
	"umc/widgets/ConfirmDialog",
	"umc/widgets/Text",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/TextBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/LabelPane",
	"umc/widgets/Button",
	"dgrid/List",
	"dgrid/OnDemandList",
	"dgrid/Selection",
	"put-selector/put"

], function(declare, lang, array, on, when, query, domClass, Memory, Lightbox, dialog, tools, _, libServer, Page, StandbyMixin, ProgressBar, ConfirmDialog, Text, ExpandingTitlePane, TextBox, ContainerWidget, LabelPane, Button, List, Grid, Selection, put) {
	var _GalleryPane = declare("umc.modules.packages._GalleryPane", [Grid, Selection], {

		postCreate: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcGalleryPane');
		},

		renderRow: function(item, options) {
			var div = put("div");
			div.innerHTML = lang.replace(
				'<div class="umcGalleryIcon {icon}"></div>' +
				'<div class="umcGalleryStatusIcon {status}"></div>' +
				'<div class="umcGalleryName">{name}</div>' +
				'<div class="umcGalleryDescription">{categories}</div>', {
					icon: this.getIconClass(item),
					status: this.getStatusIconClass(item),
					name: item.name,
					categories: item.categories.join(', ')
				}
			);
			domClass.add(div, 'umcGalleryItem');
			return div;
		},

		getIconClass: function(item) {
			return tools.getIconClass(item.icon, 50, 'umcAppCenter');
		},

		getStatusIconClass: function(item) {
			var iconClass = '';
			if (item.can_update) {
				iconClass = tools.getIconClass('packages-can_update', 24, 'umcAppCenter');
			} else if (item.is_installed) {
				iconClass = tools.getIconClass('packages-is_installed', 24, 'umcAppCenter');
			}
			return iconClass;
		}
	});

	var _SearchWidget = declare("umc.modules.packages._SearchWidget", [ContainerWidget], {

		category: null,

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

	return declare("umc.modules.packages.AppCenterPage", [ Page, StandbyMixin ], {

		_udm_accessible: false, // license depends on udm

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

			this._searchWidget = new _SearchWidget({
				region: 'left'
			});
			this.addChild(this._searchWidget);

			var titlePane = new ExpandingTitlePane({
				title: _('Applications')
			});

			this._grid = new _GalleryPane();

			titlePane.addChild(this._grid);
			this.addChild(titlePane);

			// load apps
			this.standby(true);
			when(this.getApplications(), lang.hitch(this, function(applications) {
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
			}));
		},

		postCreate: function() {
			this.inherited(arguments);

			// register event handlers
			this._searchWidget.on('search', lang.hitch(this, 'filterApplications'));

			this._grid.on('.dgrid-row:click', lang.hitch(this, function(evt) {
				this._show_details(this._grid.row(evt));
			}));
		},

		startup: function() {
			this.inherited(arguments);
		},

		// inspired by PackagesPage._show_details
		_show_details: function(app) {
			this.standby(true);

			tools.umcpCommand('packages/app_center/get', {'application': app.id}).then(
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
								if (data.result.licensefile) {
									// before installing, user must agree on license terms
									tools.umcpCommand('packages/app_center/app_license', {
										'application': data.result.id
									}).then(lang.hitch(this, function(result) {
										var content = '<h1>' + _('License agreement') + '</h1>';
										content += '<div style="max-height:250px; overflow:auto;">' + result.result + '</div>';
										dialog.confirm(content, [{
											name: 'decline',
											label: _('Cancel'),
											'default': true
										}, {
											name: 'accept',
											label: _('Accept license')
										}], _('License agreement')).then(lang.hitch(this, function(response) {
											if (response == 'accept') {
												this._call_installer('install', data.result.id, data.result.name);
											}
										}));
									}));
								}
								else {
									this._call_installer('install', data.result.id, data.result.name);
								}
							})
						});
					}
					if (data.result.allows_using && data.result.can_update) {
						buttons.push({
							name: 'update',
							label: _("Update"),
							callback: lang.hitch(this, function() {
								this._call_installer('update', data.result.id, data.result.name);
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
						content: txt
					});
					var confirmDialog = new ConfirmDialog({
						title: _('Application details'),
						message: dialogText,
						options: buttons
					});

					// decorate screenshot images with a Lightbox
					query('.umcScreenshot', confirmDialog.domNode).forEach(function(imgNode) {
						new Lightbox({ href: imgNode.src }, imgNode);
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
			var msg = lang.replace(_("Going to {verb} Application '{name}'"), {verb: verb, name: name});
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
			var allows_using = values.allows_using;
			if (allows_using && can_install && master_packages && master_packages.length) {
				if (!values.is_joined) {
					return '<strong>' + _('Attention!') + '</strong>' + ' ' + _('This application requires an extension of the LDAP schema.') + ' ' + _('Join a domain before you install this application!');
				}

				// prepare a command with max 50 characters length per line
				var MAXCHARS = 50;
				var cmdLine = lang.replace('univention-add-app {id} ', values);
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

		_detail_field_custom_emailrequired: function(values) {
			if (values.emailrequired) {
				return _('This application will inform the vendor if you (un)install it.');
			} else {
				return _('This application will not inform the vendor if you (un)install it.');
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
			return ['name',
				'version',
				'vendor',
				'contact',
				'categories',
				'longdescription',
				'screenshot',
				'defaultpackagesmaster',
				'cannot_install_reason',
				'emailrequired',
				'allows_using'
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
				'cannot_install_reason': _("Conflicts"),
				'screenshot': _("Screenshot")
			};
			return labels[key];
		},

		getApplications: function() {
			if (this._applications === undefined) {
				return tools.umcpCommand('packages/app_center/query', {}).then(lang.hitch(function(data) {
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

		filterApplications: function() {
			var regex  = new RegExp(this._searchWidget.get('value'), 'i');
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
			}
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
