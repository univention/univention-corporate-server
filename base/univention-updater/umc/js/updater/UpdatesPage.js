/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"dojo/dom-class",
	"dojo/topic",
	"dojo/Deferred",
	"dijit/registry",
	"dojox/string/sprintf",
	"umc/app",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/modules/lib/server",
	"umc/widgets/TitlePane",
	"umc/widgets/Text",
	"umc/widgets/HiddenInput",
	"umc/widgets/ComboBox",
	"umc/modules/updater/Page",
	"umc/modules/updater/Form",
	"umc/i18n!umc/modules/updater"
], function(declare, lang, array, all, domClass, topic, Deferred, dijitRegistry, sprintf, UMCApplication, tools, dialog, store, server, TitlePane, Text, HiddenInput, ComboBox, Page, Form, _) {
	var _getParentWidget = function(widget) {
		try {
			return dijitRegistry.getEnclosingWidget(widget.domNode.parentNode);
		} catch(e) {
			// could not access _widget.domNode.parentNode
			return null;
		}
	};

	return declare("umc.modules.updater.UpdatesPage", Page, {

		_update_prohibited: false,
		standby: null, // parents standby method must be passed. weird IE-Bug (#29587)
		standbyDuring: null, // parents standby method must be passed. weird IE-Bug (#29587)

		postMixInProperties: function() {

			this.inherited(arguments);

			lang.mixin(this, {
				title: _("Updates"),
				headerText: _("Available system updates"),
				helpText: _("Overview of all updates that affect the system as a whole.")
			});
		},

		_getEnclosingTitlePane: function(widgetName) {
			var _widget = this._form.getWidget(widgetName) || this._form.getButton(widgetName);
			while (_widget !== null) {
				if (_widget.isInstanceOf(TitlePane)) {
					// we successfully found the enclosing TitlePane of the given widget
					return _widget;
				}
				if (_widget.isInstanceOf(Form)) {
					// do not search beyond the form widget
					return null;
				}
				_widget = _getParentWidget(_widget);
			}
		},

		buildRendering: function() {

			this.inherited(arguments);

			var widgets = [{ // --------------------- Reboot pane -----------------------------
					type: HiddenInput,
					name: 'reboot_required'
				}, {
					type:			'Text',
					name:			'version_out_of_maintenance_text',
					'class':		'umcUpdaterWarningText',
					visible:		false,
					label:			'',
					content:		'' // will be set below as soon as the UCS version is known
				}, {
					type: Text,
					name: 'reboot_text',
					label: ' ',
					content: _("In order to complete the recently executed action, it is required to reboot the system."),
					size: 'One',
					labelPosition: 'bottom'
				}, { // ------------------- Update failed pane ------------------------
					type: Text,
					name: 'update_failed',
					label: ' ',
					content: _("The update to %s failed. The log file /var/log/univention/updater.log may contain more information about this.", _("a new UCS version")),
					size: 'One',
					labelPosition: 'bottom'
				}, { // ------------------- Easy upgrade mode -------------------------
					type: HiddenInput,
					name: 'easy_mode'
				}, {
					type: HiddenInput,
					name: 'easy_update_available'
				}, {
					type: Text,
					name: 'easy_release_text',
					label: '',
					content: 'easy_release_text',			// set in onLoaded event
					size: 'One'
				}, {
					type: Text,
					name: 'easy_available_text',
					label: ' ',
					content: 'easy_available_text',		// changed in onLoaded event
					size: 'One',
					labelPosition: 'bottom'
				}, { // -------------------- Release updates --------------------------
					type: HiddenInput,
					name: 'release_update_available'
				}, {
					type: HiddenInput,
					name: 'appliance_mode'
				}, {
					type: HiddenInput,
					name: 'release_update_blocking_components'
				}, {
					type: ComboBox,
					name: 'releases',
					label: _('Update system up to release'),
					// No matter what has changed: the 'serial' API will reflect it.
					// These dependencies establish the auto-refresh of the combobox
					// whenever the form itself has been reloaded.
					depends: ['ucs_version', 'erratalevel', 'serial', 'timestamp'],
					dynamicValues: 'updater/updates/query',
					size: 'One',
					onValuesLoaded: lang.hitch(this, function(values) {
						// TODO check updater/installer/running, don't do anything if something IS running
						try {
							this.onQuerySuccess('updater/updates/query');
							var element_releases = this._form.getWidget('releases');
							var to_show = false;

							var element_updatestext = this._form.getWidget('ucs_updates_text');
							element_updatestext.set('content', _("There are no release updates available."));

							if (values.length) {
								var val = values[values.length-1].id;
								to_show = true;
								element_releases.set('value', val);
							}

							var componentQueryDeferred = new Deferred();
							var appliance_mode = (this._form.getWidget('appliance_mode').get('value') === 'true');
							var blockingComponents = this._form.getWidget('release_update_blocking_components').get('value');
							if (blockingComponents === '') {
								blockingComponents = [];
							} else {
								blockingComponents = blockingComponents.split(' ');
							}
							var updatestext = '';
							var updatesTextComponentsUnknown = '';
							var componentsUnknown = blockingComponents;
							if (blockingComponents.length && !appliance_mode) {
								updatestext = _('Further release updates are available but cannot be installed.');
								var updatesTextComponentsApps = '';
								var askAppCenter = tools.umcpCommand('appcenter/get_by_component_id', {component_id: blockingComponents}, false).then(lang.hitch(this, function(data) {
									var apps = data.result;
									componentsUnknown = [];
									var componentApps = [];
									array.forEach(apps, function(app, i) {
										if (app) {
											componentApps.push(app);
										} else {
											componentsUnknown.push(blockingComponents[i]);
										}
									});
									if (componentApps.length) {
										componentApps.sort(function(app1, app2) {
											if (app1.is_installed && app1.candidate_version) {
												return -1;
											}
											if (app2.is_installed && app2.candidate_version) {
												return 1;
											}
											return 0;
										});
										var firstApp = componentApps[0];
										var otherApps = componentApps.slice(1);
										updatesTextComponentsApps = _('The currently installed version of the application %(name)s is not available for all newer UCS releases.', {name: componentApps[0].name});
										if (firstApp.is_installed && firstApp.candidate_version) {
											updatesTextComponentsApps += ' ' + _('An update for the app is available which may solve this issue.');
										} else {
											updatesTextComponentsApps += ' ' + _('You may wait for the app to be released for the new UCS version.');
										}
										updatesTextComponentsApps += ' ' + _('Using the %(app_center)s, you may also search for alternative apps or uninstall the application.', {app_center: UMCApplication.linkToModule('appcenter', 'appcenter')});
										if (otherApps.length) {
											updatesTextComponentsApps += '<br />' + _('This also holds for:') + '<ul>';
											array.forEach(otherApps, function(app) {
												var updateHint = null;
												if (app.is_installed && app.candidate_version) {
													updateHint = _('update available');
												} else {
													updateHint = _('no update available yet');
												}
												updatesTextComponentsApps += lang.replace('<li>{name} ({updateHint})</li>', {name: app.name, updateHint: updateHint});
											});
											updatesTextComponentsApps += '</ul>';
										}
									}
								}));
								askAppCenter.then(lang.hitch(componentQueryDeferred, 'resolve'), lang.hitch(componentQueryDeferred, 'resolve'));
								componentQueryDeferred.then(lang.hitch(this, function() {
									if (componentsUnknown.length) {
										if (componentsUnknown.length === 1) {
											updatesTextComponentsUnknown = _('Component \'%(component)s\' is not yet available for newer release versions.', {component: componentsUnknown[0]});
										} else {
											updatesTextComponentsUnknown = _('The components \'%(components)s\' are not yet available for newer release versions.', {components: componentsUnknown.join('\', \'')});
										}
									}
									updatestext = updatestext + ' ' + updatesTextComponentsApps + ' ' + updatesTextComponentsUnknown;
									element_updatestext.set('content', updatestext);
									this._form.showWidget('ucs_updates_text', true);
								}));
							} else {
								componentQueryDeferred.resolve();
							}

							// hide or show combobox, spacers and corresponding button
							this._form.showWidget('releases', to_show);

							var but = this._form._buttons.run_release_update;
							but.set('visible', to_show);

							// renew affordance to check for package updates, but only
							// if we didn't see availability yet.
							if (!this._updates_available) {
								this._set_updates_button(false, _("Package update status not yet checked"));
							}

							this.standbyDuring(all([componentQueryDeferred, this._check_dist_upgrade(), this._check_app_updates()]));
						} catch(error)
						{
							console.error("onValuesLoaded: " + error.message);
						}
					})
				}, {
					type: HiddenInput,
					name: 'ucs_version'
				}, {
					type: HiddenInput,
					name: 'serial'
				}, {
					type: HiddenInput,
					name: 'language'
				}, {
					type: HiddenInput,
					name: 'timestamp'
				}, {
					type: HiddenInput,
					name: 'components'
				}, {
					type: HiddenInput,
					name: 'enabled'
				}, {
					type: Text,
					label: '',
					name: 'ucs_version_text',
					content: _("... loading data ..."),
					style: 'margin-bottom:1em',
					size: 'One'
				}, {
					type: Text,
					label: '',
					name: 'ucs_updates_text',
					content: _("There are no release updates available."),
					size: 'One'
				}, { // ---------------------- Errata updates -----------------------
					type: 'HiddenInput',
					name: 'erratalevel'
				}, { // -------------------- Package updates ------------------------
					type: Text,
					label: ' ',
					name: 'package_update_text1',
					// FIXME Manual placement: should be done by the layout framework some day.
					content: _("Package update status not yet checked"),
					size: 'One',
					labelPosition: 'bottom'
				}, {
					type: Text,
					label: '',
					name: 'app_center_updates_text',
					content: _('... loading data ...'),
					size: 'Two'
				}, {
					type: Text,
					label: '',
					name: 'app_center_updates_apps',
					size: 'Two',
					content: ''
				}
			];

			// All buttons are initialized with the CSS class that will initially hide them.
			// (except the 'package updates' button that has different functions)
			// We don't want to have clickable buttons before their underlying data
			// has been fetched.
			var buttons = [{
				name: 'run_release_update',
				label: _('Install release update'),
				callback: lang.hitch(this, function() {
					var element = this._form.getWidget('releases');
					var release = element.get('value');
					// TODO check updater/installer/running, don't do action if a job is running
					this.onRunReleaseUpdate(release);
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'release-update');
				}),
				visible: false,
				style: 'margin:0',
				size: 'One'
			}, {
				name: 'run_packages_update',
				label: _("Check for package updates"),
				callback: lang.hitch(this, function() {
					var distUpdgradeDeferred = this._check_dist_upgrade();
					if (distUpdgradeDeferred) {
						this.standbyDuring(distUpdgradeDeferred);
					}
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'package-update');
				}),
				style: 'margin:0',
				size: 'One'
			}, {
				name: 'reboot',
				label: _("Reboot"),
				callback: lang.hitch(this, function() {
					server.askReboot();
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'reboot');
				}),
				style: 'margin:0',
				size: 'One'
			}, {
				name: 'view_log_file',
				label: _("View log file"),
				callback: lang.hitch(this, function() {
					this.onViewLog();
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'view-log');
				}),
				style: 'margin:0',
				size: 'One'
			}, {
				name: 'easy_upgrade',
				label: _("Start Upgrade"), 		// FIXME Label not correct
				callback: lang.hitch(this, function() {
					// TODO check updater/installer/running, don't do action if a job is running
					this.onRunEasyUpgrade();
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'easy-upgrade');
				}),
				style: 'margin:0',
				size: 'One'
			}];

			var layout = [
				'version_out_of_maintenance_text',
			{
				label: _("Reboot required"),
				layout: [
					['reboot_text', 'reboot']
				]
			}, {
				label: _("Update failed"),
				layout: [
					['update_failed', 'view_log_file'],
				]
			}, {
				label: _("Release information"),
				layout: [
					['easy_release_text'],
					['easy_available_text', 'easy_upgrade']
				]
			}, {
				label: _("Release updates"),
				layout: [
					['ucs_version_text'],
					['releases', 'run_release_update'],
					['ucs_updates_text']
				]
			}, {
				label: _("Package updates"),
				layout: [
					['package_update_text1', 'run_packages_update']
				]
			}, {
				label: _("App Center updates"),
				layout: [
					['app_center_updates_text'],
					['app_center_updates_apps']
				]
			}];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				buttons: buttons,
				moduleStore: store(null, 'updater/updates')
			});

			// fetch all known/initial titlepanes and save them with their name
			// so they can be used later on
			this._titlepanes = {
				reboot: this._getEnclosingTitlePane('reboot'),
				update_failed: this._getEnclosingTitlePane('update_failed'),
				easymode: this._getEnclosingTitlePane('easy_upgrade'),
				release: this._getEnclosingTitlePane('run_release_update'),
				packages: this._getEnclosingTitlePane('run_packages_update')
			};

			// Before we attach the form to our page, just switch off all title panes.
			// This delays showing the right panes until we know the value of 'easy_mode'.
			this._show_updater_panes(false);

			this.addChild(this._form);
			this._form.showWidget('releases', false);
			this._form.showWidget('ucs_updates_text', false);

			this._form.on('loaded', lang.hitch(this, function() {
				try {
					this.onQuerySuccess('updater/updates/get');
					var values = this._form.get('value');

					// send event that value have been loaded
					this.onStatusLoaded(values);

					// before we do anything else: switch visibility of panes dependent of the 'easy mode'
					this._switch_easy_mode((values.easy_mode === true) || (values.easy_mode === 'true'));

					// set text that shows release updates.
					// *** NOTE *** Availability of release updates (and visibility of 'Execute' button) can't be
					//				processed here since we have to wait for the 'onValuesLoaded' event of the
					//				combobox.
					var vtxt;
					if (values.erratalevel !== 0 && values.erratalevel !== '0') {
						vtxt = lang.replace(_("The currently installed release version is {ucs_version} errata{erratalevel}."), values);
					} else {
						vtxt = lang.replace(_("The currently installed release version is {ucs_version}."), values);
					}
					this._form.getWidget('ucs_version_text').set('content', vtxt);

					// Text (and button visibility) in EASY mode. We reuse the 'vtxt' variable
					this._form.getWidget('easy_release_text').set('content', vtxt);

					// easy_update_available -> easy_available_text
					var element = this._form.getWidget('easy_available_text');
					var ava = ((values.easy_update_available === true) || (values.easy_update_available === 'true'));
					var appliance_mode = ((values.appliance_mode === true) || (values.appliance_mode === 'true'));
					var blocking_component = this._form.getWidget('release_update_blocking_components').get('value').split(' ')[0];
					if (ava) {
						element.set('content', _("There are updates available."));
					} else if ((blocking_component) && (!appliance_mode)) {
						element.set('content', lang.replace(_("Further release updates are available but cannot be installed because the component '{0}' is not available for newer release versions."), [blocking_component]));
					} else {
						element.set('content', _("There are no updates available."));
					}
					var ebu = this._form._buttons.easy_upgrade;
					domClass.toggle(ebu.domNode, 'dijitDisplayNone', ! ava);

					this._show_reboot_pane(tools.isTrue(values.reboot_required));



				} catch(error) {
					console.error("onLoaded: " + error.message);
				}
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

			tools.umcpCommand('updater/hooks/call', { hooks: ['updater_show_message', 'updater_prohibit_update'] }).then(lang.hitch(this, function(result) {
				this._update_prohibited = false;
				var newpane;
				array.forEach(result.result.updater_show_message, function(hookresult) {
					if (hookresult.valid) {
						newpane = new TitlePane({
							title: hookresult.title,
							content: hookresult.message
						});
						this._form._container.addChild(newpane, 0);
					}
				}, this);
				array.forEach(result.result.updater_prohibit_update, function(hookresult) {
					if (hookresult) {
						this._update_prohibited = true;
						this._show_updater_panes(false);
					}
				}, this);
			}));
		},

		_get_errata_link: function(version) {
			var versionWithoutPatchlevel;
			try {
				// 3.1-0 -> 3.1
				versionWithoutPatchlevel = version.match(/(\d\.\d)-\d+/)[1];
			} catch(e) {
				console.warn('Malformed version: ', version);
			}
			if (versionWithoutPatchlevel) {
				var erratalink = lang.replace('<a href="https://errata.software-univention.de/ucs/{version}/" target="_blank">{label}</a>', {
					version: versionWithoutPatchlevel,
					label: _('Detailed information about the updates.')
				});
				return erratalink;
			}
		},

		// Internal function that sets the 'updates available' button and
		// corresponding text widget.
		_set_updates_button: function(avail, msg) {
			try {
				this._updates_available = avail;
				var but = this._form._buttons.run_packages_update;
				but.set('label', avail ?
					_("Install package updates") :
					_("Check for package updates"));
				this._form.getWidget('package_update_text1').set('content', msg);
			} catch(error) {
				console.error("set_updates_button: " + error.message);
			}
		},

		_check_app_updates: function() {
			return tools.umcpCommand('appcenter/app_updates', {}, false).then(
				lang.hitch(this, function(data) {
					var apps = array.filter(data.result, function(item) {
						if (item.candidate_version) {
							return item;
						}
					}, this);
					var msg;
					if (apps.length) {
						msg = _('There are App Center updates available.');
						var appUpdatesInfo = array.map(apps, function(app) {
							var link = sprintf('<a href="javascript:void(0)" onclick="require(\'umc/app\').openModule(\'apps\', \'%(id)s\')">%(name)s</a>', app);
							return _('%(name)s: Version %(old)s can be updated to %(new)s', {name: link, old: app.version, 'new': app.candidate_version});
						});
						var appUpdatesList = '<ul><li>' + appUpdatesInfo.join('</li><li>') + '</li></ul>';
						this._form.getWidget('app_center_updates_apps').set('content', appUpdatesList);
					} else {
						msg = _('There are no App Center updates available.');
					}
					this._form.getWidget('app_center_updates_text').set('content', msg);
				}),
				lang.hitch(this, function(data) {
					var msg = _('The App Center is not available or currently unreachable');
					this._form.getWidget('app_center_updates_text').set('content', msg);
				})
			);
		},

		// Internal function that does different things about package updates:
		//
		//	- if no package updates are available: check for availability
		//	- if some are available -> invoke 'onRunDistUpgrade()' callback.
		_check_dist_upgrade: function() {

			if (this._updates_available) {
				this.onRunDistUpgrade();
			} else {
				return tools.umcpCommand('updater/updates/available').then(
					lang.hitch(this, function(data) {
						this._set_updates_button(data.result,
							data.result ?
								_("Package updates are available. %(link)s", {link: this._get_errata_link(this._form.gatherFormValues().ucs_version)}) :
								_("There are no package updates available."));
					}),
					lang.hitch(this, function() {
						this._set_updates_button(false, _("Update availability could not be checked."));
					})
				);
			}
		},

		// This function switches the visibilty of all relevant titlepanes used for updates.
		// Other titlepanes (e.g. reboot) are not affected.
		_show_updater_panes: function(yes) {
			array.forEach(['easymode', 'release', 'packages'], function(iname) {
				domClass.toggle(this._titlepanes[iname].domNode, 'dijitDisplayNone', ! yes);
			}, this);
		},

		// Switches easy mode on or off. If the update is prohibited via hook, this
		// function hides the updater titlepanes. Doesn't touch other panes like the
		// 'reboot required' pane.
		_switch_easy_mode: function(yes) {
			if (this._update_prohibited) {
				this._show_updater_panes(false);
			} else {
				domClass.toggle(this._titlepanes.easymode.domNode, 'dijitDisplayNone', ! yes);
				domClass.toggle(this._titlepanes.release.domNode, 'dijitDisplayNone', yes);
				domClass.toggle(this._titlepanes.packages.domNode, 'dijitDisplayNone', yes);
			}
		},

		// Switches visibility of the reboot pane on or off
		_show_reboot_pane: function(yes) {
			domClass.toggle(this._titlepanes.reboot.domNode, 'dijitDisplayNone', !yes);

			if (yes) {
				this._form.showWidget('reboot_text', yes);

				var but = this._form._buttons.reboot;
				domClass.toggle(but.domNode, 'dijitDisplayNone', false);
			}

		},

		// Switches visibility of the update_failed pane on or off
		_show_update_failed_pane: function(yes) {
			domClass.toggle(this._titlepanes.update_failed.domNode, 'dijitDisplayNone', !yes);
		},

		postCreate: function() {
			this.inherited(arguments);
			this._checkOutOfMaintenance();
		},

		_checkOutOfMaintenance: function() {
			// load maintenance information and show message if current UCS version is out of maintenance
			tools.umcpCommand('updater/maintenance_information').then(lang.hitch(this, function(data) {
				var info = data.result;

				if (info.last_update_failed) {
					var version = _("a new UCS version");
					if (info.last_update_version) {
						version = "UCS " + info.last_update_version;
					}
					var warning = _("The update to %s failed. The log file /var/log/univention/updater.log may contain more information about this.", version);

					// display out of maintenance message
					var updateFailedWidget = this._form.getWidget('update_failed');
					updateFailedWidget.set('content', warning);
				}
				this._show_update_failed_pane(!!info.last_update_failed);

				if (!info.show_warning) {
					return;
				}

				var baseMsg = lang.replace(_("<b>Warning</b>: You are currently using UCS {0}. No more security updates will be released for this version. Please update the system to a newer UCS version!"), [info.ucs_version]);
				var enterpriseSubscriptionAd = _("<br>Enterprise subscriptions offer extended maintenance for some UCS versions. Detailed information can be found at the <a target='_blank' href='https://www.univention.com/products/prices-and-subscriptions/'>Univention Website</a>.");
				var extendedEnterpriseMsg = lang.replace(_("<b>Warning</b>: You are currently using UCS {0}. No more regular security updates will be released for this version!<br>Update the system to a newer UCS version or, alternatively, request an extended maintenance for this version. <a target='_blank' href='https://www.univention.com/contact/'>Feel free to contact us if you want to know more</a>."), [info.ucs_version]);

				// construct the correct message
				var msg = '';
				if (tools.isFreeLicense(info.base_dn)) {
					// UCS core edition
					msg = baseMsg + enterpriseSubscriptionAd;
				} else {
					// UCS Base/Standard/Premium subscription
					if (info.maintenance_extended) {
						msg = extendedEnterpriseMsg;
					} else {
						msg = baseMsg;
					}
				}

				// display out of maintenance message
				var outOfMaintenanceWidget = this._form.getWidget('version_out_of_maintenance_text');
				outOfMaintenanceWidget.set('content', msg);
				outOfMaintenanceWidget.set('visible', true);
			}));
		},

		// First page refresh doesn't work properly when invoked in 'buildRendering()' so
		// we defer it until the UI is being shown
		startup: function() {

			this.inherited(arguments);
			this._show_reboot_pane(false);
			this._show_update_failed_pane(false);

		},

		// ensures refresh whenever we're returning from any action.
		_onShow: function() {

			this.inherited(arguments);
			// show standby while loading data
			this.standby(true);
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
			this._form.load({});
		},

		// gives a means to restart polling after reauthentication
		startPolling: function() {
			// not needed anymore.
			// this._form.startPolling();
		},

		// These functions are stubs that the 'updater' Module is listening to,
		// to start the corresponding installer call.
		onRunReleaseUpdate: function(release) {
		},
		onRunErrataUpdate: function() {
		},
		onRunDistUpgrade: function() {
		},
		onRunEasyUpgrade: function() {
		},
		onViewLog: function() {
		},

		onStatusLoaded: function(vals) {
			// event stub
		}

	});
});
