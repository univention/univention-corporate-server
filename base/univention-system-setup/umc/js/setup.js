/*
 * Copyright 2011-2014 Univention GmbH
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
/*global define require window setTimeout*/

define([
	"dojo/_base/kernel",
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"dojo/topic",
	"dojo/Deferred",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Module",
	"umc/widgets/TabContainer",
	"umc/widgets/ProgressBar",
	"umc/modules/lib/server",
	"./setup/ApplianceWizard",
	"umc/i18n!umc/modules/setup",
// Pages:
	"./setup/LanguagePage",
	"./setup/BasisPage",
	"./setup/NetworkPage",
	"./setup/CertificatePage"
], function(dojo, declare, lang, array, all, topic, Deferred,
	tools, dialog, Module, TabContainer, ProgressBar, libServer, ApplianceWizard, _) {

	var CancelDialogException = declare("umc.modules.setup.CancelDialogException", null, {
		// empty class that indicates that the user canceled a dialog
	});

	var _alert = function(msg) {
		dialog.alert(msg, _('Validation error'));
	};

	return declare("umc.modules.setup", [ Module ], {

		// pages: String[]
		//		List of all setup-pages that are visible.
		pages: [ 'LanguagePage', 'BasisPage', 'NetworkPage', 'CertificatePage' ],

		wizard: null,

		// this module can only be opened once
		unique: true,

		// 100% opacity during rendering the module
		//standbyOpacity: 1,

		_pages: null,

		_orgValues: null,

		_currentPage: -1,

		_progressBar: null,

		// internal dict to save error messages while polling
		_saveErrors: null,

		// Date when page was last changed
		_timePageChanges: new Date(),

		buildRendering: function() {
			this.inherited(arguments);

			// query the system role
			this.standby(true);

			// load some ucr variables
			var deferred_ucr = tools.ucr([
				'server/role',
				'system/setup/boot/select/role',
				'system/setup/boot/pages/whitelist',
				'system/setup/boot/pages/blacklist',
				'umc/modules/setup/network/disabled/by'
			]);
			// load system setup values (e.g. join status)
			var deferred_variables = this.umcpCommand('setup/load');
			// wait for deferred objects to be completed
			var deferredlist = new all([deferred_ucr, deferred_variables]);
			deferredlist.then(lang.hitch(this, function(data) {
				// pass ucr and values to renderPages()
				this.renderPages(data[0], data[1].result);
				this.standbyOpacity = 0.75;  // set back the opacity to 75%
			}));
		},

		renderPages: function(ucr, values) {
			this._progressBar = new ProgressBar();
			this.own(this._progressBar);
			this.standby(true);

			// console.log('joined=' + values.joined);
			// console.log('select_role=' + ucr['system/setup/boot/select/role']);

			var allPages = lang.clone(this.pages);

			var system_role = ucr['server/role'];

			// set wizard mode only on unjoined DC Master
			this.wizard_mode = (system_role == 'domaincontroller_master') && (!values.joined);

			// we are in local mode if the user is __systemsetup__
			this.local_mode = tools.status('username') == '__systemsetup__';

			// save current values
			this._orgValues = lang.clone(values);

			// disable network page, See Bug #33006
			var networkDisabledBy = ucr['umc/modules/setup/network/disabled/by'];
			if (networkDisabledBy) {
				this._displayNetworkPageWarning(networkDisabledBy);
				allPages.splice(allPages.indexOf('NetworkPage'), 1);
			}

			// add the SoftwarePage and SystemRolePage to the list of pages for the wizard mode
			if (this.wizard_mode) {
				// add the SystemRolePage to the list of pages for the wizard mode if the packages have been downloaded
				if (tools.isTrue(ucr['system/setup/boot/select/role'])) {
					allPages.unshift('SystemRolePage');
				}

				// SoftwarePage is only available in appliance mode. Otherwise software components should be managed by
				// the App Center
				allPages.push('SoftwarePage');

				// alter pages by a whitelist and/or blacklist. the pages will be removed without any replacement.
				// empty lists are treated as if they were not defined at all (show all pages). list names should
				// match the names in this.pages and can be separated by a ' '.
				var white_list = ucr['system/setup/boot/pages/whitelist'];
				if (white_list) {
					white_list = white_list.split(' ');
					allPages = array.filter(allPages, function(page) { return array.indexOf(white_list, page) > -1; });
				}
				var black_list = ucr['system/setup/boot/pages/blacklist'];
				if (black_list) {
					black_list = black_list.split(' ');
					allPages = array.filter(allPages, function(page) { return array.indexOf(black_list, page) === -1; });
				}
				this._renderWizard(allPages, values);
			}
			else {
				this._renderTabs(allPages, values);
			}

			this.startup();
			this.standby(false);
		},

		_renderTabs: function(allPages, values) {
			var tabContainer = new TabContainer({
				nested: true
			});

			// each page has the same buttons for saving/resetting
			var buttons = [ {
				name: 'close',
				label: _( 'Close' ),
				align: 'left',
				callback: lang.hitch( this, function() {
					dialog.confirm( _( 'Should the UMC module be closed? All unsaved modification will be lost.' ), [ {
						label: _( 'Close' ),
						callback: lang.hitch( this, function() {
							topic.publish('/umc/tabs/close', this );
						} )
					}, {
						label: _( 'Cancel' ),
						'default': true
					} ] );
				} )
			}, {
				name: 'submit',
				label: _( 'Apply changes' ),
				callback: lang.hitch(this, function() {
					this.save();
				})
			}, {
				name: 'restore',
				label: _('Reset'),
				callback: lang.hitch(this, function() {
					this.load();
					topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'reset');
				})
			}];

			// create all pages dynamically
			this._pages = [];
			var tabInDomDeferred = new Deferred();
			array.forEach(allPages, function(iclass) {
				// create new page
				var ipath = 'umc/modules/setup/' + iclass;
				var Class = require(ipath);
				var ipage = new Class({
					umcpCommand: lang.hitch(this, 'umcpCommand'),
					footerButtons: buttons,
					moduleFlavor: this.moduleFlavor,
					wizard_mode: this.wizard_mode,
					local_mode: this.local_mode,
					onSave: lang.hitch(this, function() {
						this.save();
					}),
					addNotification: lang.hitch(this, 'addNotification'),
					addWarning: lang.hitch(this, 'addWarning'),
					isLoading: lang.hitch(this, 'isLoading')
				});
				tabContainer.addChild(ipage);
				this._pages.push(ipage);

				// hide tab if page is not visible
				this.own(ipage.watch('visible', function(name, oldval, newval) {
					if ((newval === true) || (newval === undefined)) {
						tabContainer.showChild(ipage);
					} else {
						tabContainer.hideChild(ipage);
					}
				}));

				// evaluate initial visibility
				tabInDomDeferred.then(function() {
					if (ipage.get('visible') === false) {
						tabContainer.hideChild(ipage);
					}
				});
			}, this);

			this.addChild(tabContainer);
			tabInDomDeferred.resolve();

			// connect to valuesChanged callback of every page
			array.forEach(this._pages, lang.hitch(this, function(ipage) {
				ipage.on('valuesChanged', lang.hitch(this, function() {
					this.ready().then(lang.hitch(this, 'updateAllValues'));
				}));
				ipage.setValues(values);
			}));
		},

		_renderWizard: function(allPages, values) {
			this.wizard = new ApplianceWizard({
				//progressBar: progressBar
				moduleID: this.moduleID,
				visiblePages: allPages,
				local_mode: this.local_mode,
				values: values
			});
			this.addChild(this.wizard);
			this.wizard.on('Finished', lang.hitch(this, function(newValues) {
				// wizard is done -> call cleanup command and redirect browser to new web address
				topic.publish('/umc/actions', this.moduleID, 'wizard', 'done');
				tools.umcpCommand('setup/cleanup', {}, undefined, undefined, {
					// long polling options
					messageInterval: 30,
					xhrTimeout: 40
				}).then(lang.hitch(this, function() {
					this._redirectBrowser(newValues.interfaces, newValues['interfaces/primary']);
				}));
			}));
			this.wizard.on('Reload', lang.hitch(this, '_reloadWizard', allPages, values));
		},

		_reloadWizard: function(allPages, values, newLocale) {
			// update internal locale settings
			var _setLocale = function() {
				dojo.locale = newLocale;
				var locale = newLocale.replace('-', '_');
				var deferreds = [];
				deferreds.push(tools.umcpCommand('set', {
					locale: locale
				}, false));
				deferreds.push(tools.umcpCommand('setup/set_locale', {
					locale: locale
				}, false));
				deferreds.push(_.load());
				return all(deferreds);
			};

			// remove wizard and render it again
			var _cleanup = lang.hitch(this, function() {
				this.removeChild(this.wizard);
				this.wizard.destroy();
				this._renderWizard(allPages, values);
			});

			// chain tasks with some time in between to allow a smooth standby animation
			this.standby(true);
			var self = this;
			tools.defer(_setLocale, 200).then(function() {
				return tools.defer(_cleanup, 200);
			}).then(function() {
				return tools.defer(lang.hitch(self, 'standby', false), 200);
			});
		},

		_displayNetworkPageWarning: function(networkDisabledBy) {
			var version = tools.status('ucsVersion').split('-')[0];
			var link = '<a href="' + _('http://docs.univention.de/computers-%s.html#uvmm', version) + '">"' + _('Setup for UCS Virtual Machine Manager') + '"</a>';
			var uvmmWarning = _('Changing network settings is disabled due to specific UVMM settings. See %s for further information.', link);
			var warning = {
				xen: uvmmWarning,
				kvm: uvmmWarning
			}[networkDisabledBy] || _('Changing network settings is disabled. It can be re enabled by unsetting the UCR variable "umc/modules/setup/network/disabled/by".');

			this.addWarning(warning);
		},

		ready: function() {
			return all(array.map(array.filter(this._pages, function(ipage) {
				return !!ipage._form;
			}), function(ipage) { return ipage._form.ready(); }));
		},

		updateAllValues: function(name, old, values) {
			var vals = lang.clone(this._orgValues);
			lang.mixin(vals, this.getValues());
			array.forEach(this._pages, function(ipage) {
				ipage.setValues(vals);
			}, this);
		},

		setValues: function(values) {
			// update all pages with the given values
			this._orgValues = lang.clone(values); //FIXME: wrong place
			array.forEach(this._pages, function(ipage) {
				ipage.setValues(this._orgValues);
			}, this);
		},

		getValues: function() {
			var values = {};
			array.forEach(this._pages, function(ipage) {
				lang.mixin(values, ipage.getValues());
			}, this);
			return values;
		},

		load: function() {
			// get settings from server
			this.standby(true);
			return this.umcpCommand('setup/load').then(lang.hitch(this, function(data) {
				// update setup pages with loaded values
				this.setValues(data.result);
				this.standby(false);
			}), lang.hitch(this, function() {
				this.standby(false);
			}));
		},

		isLoading: function() {
			return Boolean(this.get('standingBy'));
		},

		_getNewIpAddress: function(interfaces, primary_interface) {
			interfaces = interfaces || {};
			var newIpAddress = null;

			var currentIP = window.location.host;
			currentIP = currentIP.replace('[', '').replace(']', '');

			var prim = interfaces[primary_interface];
			var primIp4 = prim && prim.ip4[0] && prim.ip4[0][0];
			var primIp6 = prim && prim.ip6[0] && prim.ip6[0][0];

			tools.forIn(this._orgValues.interfaces, function(ikey, iface) {
				// 1. check if value is equal to the current IP
				// 2. check if a new value was set or use IP from new primary interface
				var oldIp4 = iface.ip4[0] && iface.ip4[0][0];
				var oldIp6 = iface.ip6[0] && iface.ip6[0][0];
				var newIp4 = interfaces[ikey] && interfaces[ikey].ip4[0] && interfaces[ikey].ip4[0][0];
				var newIp6 = interfaces[ikey] && interfaces[ikey].ip6[0] && interfaces[ikey].ip6[0][0];
				if (oldIp4 === currentIP) {
					newIpAddress = newIp4 || primIp4 || newIp6 || primIp6;
				} else if (oldIp6 === currentIP) {
					newIpAddress = newIp6 || primIp6 || newIp4 || primIp4;
				}
			});
			if (newIpAddress == currentIP) {
				newIpAddress = null;
			}
			if (newIpAddress && !(/[.]/).test(newIpAddress)) {
				// ipv6
				newIpAddress = '[' + newIpAddress + ']';
			}
			return newIpAddress;
		},

		_redirectBrowser: function(interfaces, primary_interface) {
			// redirect to new UMC address and set username to Administrator
			this._progressBar.reset();
			this._progressBar.setInfo(_('Restarting server components...'), _('This may take a few seconds...'), Number.POSITIVE_INFINITY);
			this.standby(true, this._progressBar);

			var username = 'Administrator';
			var target = window.location.href.replace(new RegExp( "/univention-management-console.*", "g" ), '/univention-management-console/?username=' + username);

			// Consider IP changes, replace old ip in url by new ip
			var newIp = this._getNewIpAddress(interfaces, primary_interface || 'eth0');
			if (newIp) {
				var oldIp = window.location.host;
				target = target.replace(oldIp, newIp);
			}

			// give the restart/services function 10 seconds time to restart the services
			setTimeout(function () {
				window.location.replace(target);
			}, 12000);
		},

		save: function() {
			topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'save');

			// get all entries that have changed and collect a summary of all changes
			var values = {};
			var nchanges = 0;
			var inverseKey2Page = {};  // saves which key belongs to which page
			var summaries = [];
			var umc_url = null;

			array.forEach(this._pages, function(ipage) {
				var pageVals = ipage.getValues();
				var summary = ipage.getSummary();
				summaries = summaries.concat(summary);

				// get altered values from page
				tools.forIn(pageVals, function(ikey, ival) {
					inverseKey2Page[ikey] = ipage;
					var orgVal = this._orgValues[ikey];
					orgVal = (undefined === orgVal || null === orgVal) ? '' : orgVal;
					var newVal = (undefined === ival || null) === ival ? '' : ival;
					// some variables (notably locale)
					// were sent as [{id:id, label:label}, ...]
					// but will be returned as [id, ...]
					if (orgVal instanceof Array) {
						var tmpOrgVal = array.filter(orgVal, function(iOrgVal) {
							return (iOrgVal && iOrgVal.id !== undefined && iOrgVal.label !== undefined);
						});
						if (tmpOrgVal.length) {
							orgVal = tmpOrgVal;
						}
					}
					if (!tools.isEqual(orgVal, newVal)) {
						values[ikey] = newVal;
						++nchanges;

						if (ikey === 'interfaces' && umc_url === null) {
							var newIp = this._getNewIpAddress(ival, pageVals['interfaces/primary'] || 'eth0');
							if (newIp) {
								umc_url = 'https://' + newIp + '/umc/';
							}
						}
					}
				}, this);
			}, this);

			// only submit data to server if there are changes and the system is joined
			if (!nchanges) {
				dialog.alert(_('No changes have been made.'));
				return;
			}

			// helper function
			var _matchesSummary = function(key, summary) {
				var matched = false;
				// iterate over all assigned variables
				array.forEach(summary.variables, function(ikey) {
					// key is a regular expression or a string
					if (typeof ikey == "string" && key == ikey ||
							ikey.test && ikey.test(key)) {
						matched = true;
						return false;
					}
				});
				return matched;
			};

			// function to locally validate the pages
			var _localValidation = function() {
				var allValid = true;
				var validationMessage = '<p>' + _('The following entries could not be validated:') + '</p><ul style="max-height:200px; overflow:auto;">';
				array.forEach(this._pages, function(ipage) {
					if (!ipage._form) {
						return true;
					}
					tools.forIn(ipage._form._widgets, lang.hitch(this, function(ikey, iwidget) {
						if (iwidget.isValid && false === iwidget.isValid()) {
							if (allValid) {
								// jump to the first invalid widget
								this.selectPage(ipage);
							}
							allValid = false;
							validationMessage += '<li>' + ipage.get('title') + '/' + iwidget.get('label') + '</li>';
						}
					}));
				}, this);
				validationMessage += '</ul>';

				if (!allValid) {
					_alert(validationMessage);
					throw new Error('Validation failed!');
				}
			};

			// function to confirm changes
			var _confirmChanges = function(values, summaries) {
				// first see which message needs to be displayed for the confirmation message
				tools.forIn(values, function(ikey) {
					array.forEach(summaries, function(idesc) {
						if (_matchesSummary(ikey, idesc)) {
							idesc.showConfirm = true;
						}
					}, this);
				}, this);

				// construct message for confirmation
				var confirmMessage = '<p>' + _('The following changes will be applied to the system:') + '</p><ul style="max-height:200px; overflow:auto;">';
				array.forEach(summaries, function(idesc) {
					if (idesc.showConfirm) {
						confirmMessage += '<li>' + idesc.description + ': ' + idesc.values + '</li>';
					}
				});
				confirmMessage += '</ul><p>' + _('Please confirm to apply these changes to the system. This may take some time.') + '</p>';

				return dialog.confirm(confirmMessage, [{
					name: 'cancel',
					'default': true,
					label: _('Cancel')
				}, {
					name: 'apply',
					label: _('Apply changes')
				}]).then(lang.hitch(this, function(response) {
					if ('apply' != response) {
						// throw new error to indicate that action has been canceled
						throw new CancelDialogException();
					}
				}));
			};

			// function for server side validation of user changes
			var _remoteValidation = function(values, summaries) {
				this.standby(true);
				return this.umcpCommand('setup/validate', { values: values }).then(lang.hitch(this, function(data) {
					var allValid = true;
					array.forEach(data.result, function(ivalidation) {
						if (!ivalidation.valid) {
							if (allValid) {
								// focus the first invalid page
								array.forEach(this._pages, function(ipage) {
									if (ipage._form && ipage._form.getWidget(ivalidation.key)) {
										this.selectPage(ipage);
									}
								}, this);
							}
							allValid = false;
						}
						if (ivalidation.message) {
							// find the correct description to be displayed
							array.forEach(summaries, function(idesc) {
								if (_matchesSummary(ivalidation.key, idesc)) {
									idesc.validationMessages = idesc.validationMessages || [];
									idesc.validationMessages.push(ivalidation.message);
								}
							}, this);
						}
					}, this);

					if (allValid) {
						// everythin fine, continue
						return;
					}

					// something could not be validated... construct message for validation
					var validationMessage = '<p>' + _('The following entries could not be validated:') + '</p><ul style="max-height:200px; overflow:auto;">';
					array.forEach(summaries, function(idesc) {
						array.forEach(idesc.validationMessages || [], function(imsg) {
							validationMessage += '<li>' + idesc.description + ': ' + imsg + '</li>';
						});
					});
					validationMessage += '</ul>';
					_alert(validationMessage);
					throw new Error('Validation failed!');
				}));
			};

			// function to save data
			var _save = function(values, umc_url) {
				var deferred = new Deferred();

				// send save command to server
				this._progressBar.reset(_('Initialize the configuration process ...'));
				this.standby(false, this._progressBar);
				this.standby(true, this._progressBar);
				this.umcpCommand('setup/save', {
					values: values
				}, false);

				// poll whether script has finished
				tools.defer(lang.hitch(this, function() {
					this._progressBar.auto(
						'setup/finished',
						{},
						lang.hitch(deferred, 'resolve'),
						lang.replace( _( 'The connection to the server could not be established after {time} seconds. This problem can occur due to a change of the IP address. In this case, please login to Univention Management Console again at the {linkStart}new address{linkEnd}.' ), {
							time: '{time}',
							linkStart : umc_url ? '<a href="' + umc_url + '">' : '',
							linkEnd : umc_url ? '</a>' : ''
						} ),
						_('Configuration finished'),
						true
					);
				}), 500);

				return deferred.then(lang.hitch(this, function() {
					this.standby(false);
				}));
			};

			// ask user whether UMC server components shall be restarted or not
			var _restart = function() {
				libServer.askRestart(_('The changes have been applied successfully.'));
				this.load(); // sets 'standby(false)'
			};

			// notify user that saving was successful
			var _success = function() {
				this.addNotification(_('The changes have been applied successfully.'));
				this.load(); // sets 'standby(false)'
			};

			// tell user that saving was not successful (has to confirm)
			var _failure = function(errorHtml) {
				var msg = _('Not all changes could be applied successfully:') + errorHtml;
				var choices = [{
					name: 'apply',
					'default': true,
					label: _('Ok')
				}];
				return dialog.confirm(msg, choices).then(lang.hitch(this, function() {
					this.load(); // sets 'standby(false)'
				}));
			};

			// show success/error message and eventually restart UMC server components
			var _checkForErrorsDuringSave = function(values) {
				var errors = this._progressBar.getErrors().errors;
				if (errors.length) {
					// errors have occurred
					var errorHtml = '<ul style="overflow: auto; max-height: 400px;">';
					array.forEach(errors, function(error) {
						errorHtml += '<li>' + error + '</li>';
					});
					errorHtml += '</ul>';
					return _failure(errorHtml);
				} else {
					// see whether a UMC server, UMC web server, and apache restart is necessary:
					// -> installation/removal of software components
					// -> update of SSL certificate
					var umcRestartNeeded = 'components' in values;
					tools.forIn(values, function(name) {
						if ((/^ssl\/.*$/).test(name)) {
							umcRestartNeeded = true;
						}
					});

					// everything went well :)
					if (umcRestartNeeded) {
						return _restart();
					}
					else {
						return _success();
					}
				}
			};

			// chain all methods together
			var deferred = new Deferred();
			deferred.resolve();
			deferred = deferred.then(lang.hitch(this, _localValidation, values));
			deferred = deferred.then(lang.hitch(this, _confirmChanges, values, summaries));
			deferred = deferred.then(lang.hitch(this, _remoteValidation, values, summaries));
			deferred = deferred.then(lang.hitch(this, _save, values, umc_url));
			deferred = deferred.then(lang.hitch(this, _checkForErrorsDuringSave, values));
			deferred.then(
				lang.hitch(this, 'standby', false),
				lang.hitch(this, 'standby', false)
			);
		},

		selectPage: function(page) {
			var tabcontainer = this.getChildren()[0];
			return tabcontainer.selectChild(page);
		}
	});
});
