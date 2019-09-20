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
/*global define,require,window,setTimeout*/

define([
	"dojo/_base/kernel",
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/promise/all",
	"dojo/topic",
	"dojo/Deferred",
	"dojox/html/styles",
	"dojox/html/entities",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Module",
	"umc/widgets/ProgressBar",
	"umc/modules/lib/server",
	"umc/i18n!umc/modules/setup",
// Pages:
	"./setup/LanguagePage",
	"./setup/NetworkPage",
	"./setup/CertificatePage"
], function(dojo, declare, lang, array, all, topic, Deferred, styles, entities,
	tools, dialog, Module, ProgressBar, libServer, _) {

	var CancelDialogException = declare("umc.modules.setup.CancelDialogException", null, {
		// empty class that indicates that the user canceled a dialog
	});

	var _alert = function(msg) {
		dialog.alert(msg, _('Validation error'));
	};

	return declare("umc.modules.setup", [ Module ], {

		// this module can only be opened once
		unique: true,

		// 100% opacity during rendering the module
		//standbyOpacity: 1,

		_pages: null,

		_orgValues: null,

		_progressBar: null,

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
				'system/setup/boot/fields/blacklist',
				'system/setup/boot/minimal_memory',
				'system/setup/boot/installer',
				'docker/container/uuid',
				'umc/modules/setup/network/disabled/by',
				'umc/web/appliance/*'
			]);

			all({
				ucr: deferred_ucr,
				values: this.umcpCommand('setup/load')
			}).then(lang.hitch(this, function(data) {
				this._progressBar = new ProgressBar();
				this.own(this._progressBar);
				this.standby(true);

				var values = data.values.result;

				// save current values
				this._orgValues = lang.clone(values);

				this._renderTabs(values, data.ucr);

				this.startup();
				this.standby(false);
				this.standbyOpacity = 0.75;  // set back the opacity to 75%
			}));
		},

		_renderTabs: function(values, ucr) {

			// disable network page, See Bug #33006
			var networkDisabledBy = ucr['umc/modules/setup/network/disabled/by'];
			if (networkDisabledBy && this.moduleFlavor == 'network') {
				this._displayNetworkPageWarning(networkDisabledBy);
				this.closeModule();
				return;
			}

			// each page has the same buttons for saving/resetting
			var buttons = [/* {
				name: 'close',
				label: _( 'Close' ),
				iconClass: 'umcCloseIconWhite',
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
			}, */{
				name: 'submit',
				iconClass: 'umcSaveIconWhite',
				label: _( 'Apply changes' ),
				callback: lang.hitch(this, function() {
					this.save();
				})
			}];

			var iclass = {
				languages: 'LanguagePage',
				network: 'NetworkPage',
				certificate: 'CertificatePage'
			}[this.moduleFlavor];

			var ipath = 'umc/modules/setup/' + iclass;
			var Class = require(ipath);
			var ipage = new Class({
				umcpCommand: lang.hitch(this, 'umcpCommand'),
				headerButtons: buttons,
				moduleFlavor: this.moduleFlavor,
				wizard_mode: false,
				onSave: lang.hitch(this, function() {
					this.save();
				}),
				addPage: lang.hitch(this, 'addChild'),
				removePage: lang.hitch(this, 'removeChild'),
				addNotification: lang.hitch(this, 'addNotification'),
				addWarning: lang.hitch(this, 'addWarning'),
				isLoading: lang.hitch(this, 'isLoading')
			});
			ipage.on('selectPage', lang.hitch(this, function(page) {
				this.selectChild(page || ipage);
			}));
			this._page = ipage;
			this.addChild(ipage);
			ipage.on('valuesChanged', lang.hitch(this, function() {
				this.ready().then(lang.hitch(this, 'updateAllValues'));
			}));
			ipage.setValues(values);
		},

		_displayNetworkPageWarning: function(networkDisabledBy) {
			var version = tools.status('ucsVersion').split('-')[0];
			var link = '<a href="' + _('https://docs.software-univention.de/manual-%s.html#computers:networkcomplex:uvmm', version) + '">"' + _('Setup for UCS Virtual Machine Manager') + '"</a>';
			var uvmmWarning = _('Changing network settings is disabled due to specific UVMM settings. See %s for further information.', link);
			var warning = {
				xen: uvmmWarning,
				kvm: uvmmWarning
			}[networkDisabledBy] || _('Changing network settings is disabled. It can be re enabled by unsetting the UCR variable "umc/modules/setup/network/disabled/by".');

			this.addWarning(warning);
		},

		ready: function() {
			return this._page._form.ready();
		},

		updateAllValues: function(name, old, values) {
			var vals = lang.clone(this._orgValues);
			lang.mixin(vals, this.getValues());
			this._page.setValues(vals);
		},

		setValues: function(values) {
			// update all pages with the given values
			this._orgValues = lang.clone(values); //FIXME: wrong place
			if (this._page) {
				this._page.setValues(this._orgValues);
			}
		},

		getValues: function() {
			return this._page.getValues();
		},

		load: function() {
			// get settings from server
			return this.standbyDuring(this.umcpCommand('setup/load')).then(lang.hitch(this, function(data) {
				// update setup pages with loaded values
				this.setValues(data.result);
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

		save: function() {
			topic.publish('/umc/actions', this.moduleID, this.moduleFlavor, 'save');

			// get all entries that have changed and collect a summary of all changes
			var values = {};
			var nchanges = 0;
			var inverseKey2Page = {};  // saves which key belongs to which page
			var summaries = [];
			var umc_url = null;

			var pageVals = this._page.getValues();
			var summary = this._page.getSummary();
			summaries = summaries.concat(summary);

			// get altered values from page
			tools.forIn(pageVals, function(ikey, ival) {
				inverseKey2Page[ikey] = this._page;
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
			var _localValidation = lang.hitch(this, function() {
				var allValid = true;
				var validationMessage = '<p>' + _('The following entries could not be validated:') + '</p><ul style="max-height:200px; overflow:auto;">';
				tools.forIn(this._page._form._widgets, lang.hitch(this, function(ikey, iwidget) {
					if (iwidget.isValid && false === iwidget.isValid()) {
						allValid = false;
						validationMessage += '<li>' + this._page.get('title') + '/' + iwidget.get('label') + '</li>';
					}
				}));
				validationMessage += '</ul>';

				if (!allValid) {
					_alert(validationMessage);
					throw new Error('Validation failed!');
				}
			});

			// function to confirm changes
			var _confirmChanges = lang.hitch(this, function(values, summaries) {
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
						var values = idesc.values;
						if (!idesc.valuesAllowHTML) {
							values = entities.encode(values);
						}
						confirmMessage += '<li>' + entities.encode(idesc.description) + ': ' + values + '</li>';
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
			});

			// function for server side validation of user changes
			var _remoteValidation = lang.hitch(this, function(values, summaries) {
				this.standby(true);
				return this.umcpCommand('setup/validate', { values: values }).then(lang.hitch(this, function(data) {
					var allValid = true;
					array.forEach(data.result, function(ivalidation) {
						if (!ivalidation.valid) {
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
						// everything fine, continue
						return;
					}

					// something could not be validated... construct message for validation
					var validationMessage = '<p>' + _('The following entries could not be validated:') + '</p><ul style="max-height:200px; overflow:auto;">';
					array.forEach(summaries, function(idesc) {
						array.forEach(idesc.validationMessages || [], function(imsg) {
							validationMessage += '<li>' + entities.encode(idesc.description) + ': ' + entities.encode(imsg) + '</li>';
						});
					});
					validationMessage += '</ul>';
					_alert(validationMessage);
					throw new Error('Validation failed!');
				}));
			});

			// function to save data
			var _save = lang.hitch(this, function(values, umc_url) {
				// send save command to server
				return this.standbyDuring(this.umcpCommand('setup/save', {
					values: values
				})).then(lang.hitch(this, function() {
					// make sure the server process cannot die
					this.umcpCommand('setup/ping', {keep_alive: true}, false);

					var deferred = new Deferred();
					// poll whether script has finished
					this._progressBar.reset(_('Initialize the configuration process ...'));
					this.standby(false, this._progressBar);
					this.standbyDuring(deferred, this._progressBar);
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
					return deferred;
				}));
			});

			// ask user whether UMC server components shall be restarted or not
			var _restart = lang.hitch(this, function() {
				libServer.askRestart(_('The changes have been applied successfully.'));
				this.load(); // sets 'standby(false)'
			});

			// notify user that saving was successful
			var _success = lang.hitch(this, function() {
				this.addNotification(_('The changes have been applied successfully.'));
				this.load(); // sets 'standby(false)'
			});

			// tell user that saving was not successful (has to confirm)
			var _failure = lang.hitch(this, function(errorHtml) {
				var msg = _('Not all changes could be applied successfully:') + errorHtml;
				var choices = [{
					name: 'apply',
					'default': true,
					label: _('Ok')
				}];
				return dialog.confirm(msg, choices).then(lang.hitch(this, function() {
					this.load(); // sets 'standby(false)'
				}));
			});

			// show success/error message and eventually restart UMC server components
			var _checkForErrorsDuringSave = lang.hitch(this, function(values) {
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
			});

			// chain all methods together
			var deferred = new Deferred();
			deferred.resolve();
			deferred = deferred.then(lang.partial(_localValidation, values));
			deferred = deferred.then(lang.partial(_confirmChanges, values, summaries));
			deferred = deferred.then(lang.partial(_remoteValidation, values, summaries));
			deferred = deferred.then(lang.partial(_save, values, umc_url));
			deferred = deferred.then(lang.partial(_checkForErrorsDuringSave, values));
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
