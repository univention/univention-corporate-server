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

dojo.provide("umc.modules.setup");

dojo.require("dijit.TitlePane");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.TabContainer");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TitlePane");

dojo.declare("umc.modules._setup.CancelDialogException", null, {
	// empty class that indicates that the user canceled a dialog
});

dojo.declare("umc.modules.setup", [ umc.widgets.Module, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.setup',

	// pages: String[]
	//		List of all setup-pages that are visible.
	pages: [ 'LanguagePage', 'BasisPage', 'NetworkPage', 'CertificatePage', 'SoftwarePage' ],

	// 100% opacity during rendering the module
	//standbyOpacity: 1,

	_pages: null,

	_orgValues: null,

	_currentPage: -1,

	buildRendering: function() {
		this.inherited(arguments);

		// query the system role
		this.standby(true);
		umc.tools.ucr('server/role').then(dojo.hitch(this, function(ucr) {
			this.renderPages(ucr['server/role']);
			this.standby(false);
			this.standbyOpacity = 0.75;  // set back the opacity to 75%
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	renderPages: function(role) {
		this.standby(true);
		if (this.moduleFlavor == 'wizard') {
			// wizard mode

			// create all pages dynamically
			this._pages = [];
			dojo.forEach(this.pages, function(iclass, i) {
				// load page class
				var ipath = 'umc.modules._setup.' + iclass;
				dojo['require'](ipath);

				// check whether 'role' is set and the page should be visible or not
				var Class = new dojo.getObject(ipath);
				if (Class.prototype.role && dojo.indexOf(Class.prototype.role, role) < 0) {
					return true;
				}

				// get the buttons we need
				var buttons = [];
				if (i < this.pages.length - 1) {
					buttons.push({
						name: 'submit',
						label: this._('Next'),
						callback: dojo.hitch(this, function() {
							this.selectChild(this._pages[i + 1]);
						})
					});
				}
				if (i > 0) {
					buttons.push({
						name: 'restore',
						label: this._('Back'),
						callback: dojo.hitch(this, function() {
							this.selectChild(this._pages[i - 1]);
						})
					});
				}
				if (i == this.pages.length - 1) {
					buttons.push({
						name: 'submit',
						label: this._('Finish'),
						callback: dojo.hitch(this, function() {
							this.save();
						})
					});
				}

				// make a new page
				var ipage = new Class({
					umcpCommand: dojo.hitch(this, 'umcpCommand'),
					footerButtons: buttons,
					onSave: dojo.hitch(this, function() {
						if (i < this.pages.length - 1) {
							this.selectChild(this._pages[i + 1]);
						}
						else {
							this.save();
						}
					})
				});
				this.addChild(ipage);
				this._pages.push(ipage);
			}, this);
		}
		else {
			// normal mode... we need a TabContainer
			var tabContainer = new umc.widgets.TabContainer({
				nested: true
			});

			// each page has the same buttons for saving/resetting
			var buttons = [{
				name: 'submit',
				label: this._('Save'),
				callback: dojo.hitch(this, function() {
					this.save();
				})
			}, {
				name: 'restore',
				label: this._('Reset'),
				callback: dojo.hitch(this, function() {
					this.load();
				})
			}];

			// create all pages dynamically
			this._pages = [];
			dojo.forEach(this.pages, function(iclass) {
				var ipath = 'umc.modules._setup.' + iclass;
				dojo['require'](ipath);

				// check whether 'role' is set and the page should be visible or not
				var Class = new dojo.getObject(ipath);
				if (Class.prototype.role && dojo.indexOf(Class.prototype.role, role) < 0) {
					return true;
				}

				// create new page
				var ipage = new Class({
					umcpCommand: dojo.hitch(this, 'umcpCommand'),
					footerButtons: buttons,
					onSave: dojo.hitch(this, function() {
						this.save();
					})
				});
				tabContainer.addChild(ipage);
				this._pages.push(ipage);
			}, this);

			this.addChild(tabContainer);
		}

		this.startup();
		this.load();
	},

	setValues: function(values) {
		// update all pages with the given values
		this._orgValues = dojo.clone(values);
		dojo.forEach(this._pages, function(ipage) {
			ipage.setValues(this._orgValues);
		}, this);
	},

	getValues: function() {
		var values = {};
		dojo.forEach(this._pages, function(ipage) {
			dojo.mixin(values, ipage.getValues());
		}, this);
		return values;
	},

	load: function() {
		// get settings from server
		this.standby(true);
		return this.umcpCommand('setup/load').then(dojo.hitch(this, function(data) {
			// update setup pages with loaded values
			this.setValues(data.result);
			this.standby(false);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	save: function() {
		// helper function 
		var matchesSummary = function(key, summary) {
			var matched = false;
			// iterate over all assigned variables
			dojo.forEach(summary.variables, function(ikey) {
				// key is a regular expression or a string
				if (dojo.isString(ikey) && key == ikey ||
						ikey.test && ikey.test(key)) {
					matched = true;
					return false;
				}
			});
			return matched;
		};

		// confirm dialog to continue with boot process
		var _shutDownBrowser = dojo.hitch(this, function(msg, hasCancel) {
			var choices = [{
				name: 'apply',
				'default': true,
				label: this._('Continue')
			}];
			if (hasCancel) {
				// show continue and cancel buttons
				choices = [{
					name: 'cancel',
					'default': true,
					label: this._('Cancel')
				}, {
					name: 'apply',
					label: this._('Continue')
				}];
			}

			return umc.dialog.confirm(msg, choices).then(dojo.hitch(this, function(response) {
				if (response == 'cancel') {
					// do not continue
					return;
				}

				// otherwise send the UMCP command to shut down the web browser
				return this.umcpCommand('setup/browser/shutdown').then(dojo.hitch(this, function() {
					this.standby(false);
				}), dojo.hitch(this, function() {
					this.standby(false);
				}));
			}));
		});

		// get all entries that have changed and collect a summary of all changes
		var values = {};
		var nchanges = 0;
		var inverseKey2Page = {};  // saves which key belongs to which page
		var summaries = [];
		dojo.forEach(this._pages, function(ipage) {
			var pageVals = ipage.getValues();
			var summary = ipage.getSummary();
			summaries = summaries.concat(summary);

			// get altered values from page
			umc.tools.forIn(pageVals, function(ikey, ival) {
				inverseKey2Page[ikey] = ipage;
				var orgVal = this._orgValues[ikey];
				orgVal = undefined === orgVal || null === orgVal ? '' : orgVal;
				var newVal = undefined === ival || null === ival ? '' : ival;
				if (dojo.toJson(orgVal) != dojo.toJson(newVal)) {
					values[ikey] = newVal;
					++nchanges;
				}
			}, this);
		}, this);

		// initiate some local check variables
		var joined = this._orgValues['joined'];
		var role = this._orgValues['server/role'];
		var applianceMode = umc.tools.status('username') == '__systemsetup__';

		if (!nchanges && applianceMode && !(joined || role == 'basesystem')) {
			// no changes have been made we can shut down the web browser directly
			_shutDownBrowser(this._('No changes have been made. Please confirm to continue with the boot process.'), true);
			return
		}

		// only submit data to server if there are changes and the system is joined
		if (!nchanges && (joined || role == 'basesystem')) {
			umc.dialog.alert(this._('No changes have been made.'));
			return;
		}

		// check whether all page widgets are valid
		var allValid = true;
		var validationMessage = '<p>' + this._('The following entries could not be validated:') + '</p><ul style="max-height:200px; overflow:auto;">';
		dojo.forEach(this._pages, function(ipage) {
			umc.tools.forIn(ipage._form._widgets, function(ikey, iwidget) {
				if (iwidget.isValid && false === iwidget.isValid()) {
					allValid = false;
					validationMessage += '<li>' + ipage.get('title') + '/' + iwidget.get('label') + '</li>';
				}
			});
		});
		if (!allValid) {
			this.standby(false);
			umc.dialog.alert(validationMessage);
			return;
		}

		// validate the changes
		this.standby(true);
		this.umcpCommand('setup/validate', { values: values }).then(dojo.hitch(this, function(data) {
			var allValid = true;
			dojo.forEach(data.result, function(ivalidation) {
				allValid = allValid && ivalidation.valid;
				if (!ivalidation.valid) {
					// find the correct description to be displayed
					dojo.forEach(summaries, function(idesc) {
						if (matchesSummary(ivalidation.key, idesc)) {
							idesc.validationMessages = idesc.validationMessages || [];
							idesc.validationMessages.push(ivalidation.message);
						}
					});

				}
			});

			// construct message for validation
			dojo.forEach(summaries, function(idesc) {
				//console.log('#', dojo.toJson(idesc));
				dojo.forEach(idesc.validationMessages || [], function(imsg) {
					validationMessage += '<li>' + idesc.description + ': ' + imsg + '</li>';
				});
			});

			if (!allValid) {
				// something could not be validated
				this.standby(false);
				umc.dialog.alert(validationMessage);
				return;
			}

			// function to confirm changes
			var _confirmChanges = dojo.hitch(this, function() {
				// first see which message needs to be displayed for the confirmation message
				umc.tools.forIn(values, function(ikey) {
					dojo.forEach(summaries, function(idesc) {
						if (matchesSummary(ikey, idesc)) {
							idesc.showConfirm = true;
						}
					});
				});

				// construct message for confirmation
				var confirmMessage = '<p>' + this._('The following changes will be applied to the system:') + '</p><ul style="max-height:200px; overflow:auto;">';
				dojo.forEach(summaries, function(idesc) {
					if (idesc.showConfirm) {
						confirmMessage += '<li>' + idesc.description + ': ' + idesc.values + '</li>';
					}
				});
				confirmMessage += '</ul><p>' + this._('Please confirm to apply these changes to the system. This may take some time.') + '</p>';

				return umc.dialog.confirm(confirmMessage, [{
					name: 'cancel',
					'default': true,
					label: this._('Cancel')
				}, {
					name: 'apply',
					label: this._('Apply changes')
				}]).then(dojo.hitch(this, function(response) {
					if ('apply' != response) {
						// throw new error to indicate that action has been canceled
						throw new umc.widgets._setup.CancelDialogException();
					}
				}));
			});

			// function to ask the user for DC account data
			var _password = dojo.hitch(this, function() {
				var msg = '<p>' + this._('The specified settings will be applied to the system and the system will be joined into the domain. Please enter username and password of a domain administrator account.') + '</p>'; 
				var deferred = new dojo.Deferred();
				var dialog = null;
				var form = new umc.widgets.Form({
					widgets: [{
						name: 'text',
						type: 'Text',
						content: msg
					}, {
						name: 'username',
						type: 'TextBox',
						label: this._('Username')
					}, {
						name: 'password',
						type: 'PasswordBox',
						label: this._('Password')
					}],
					buttons: [{
						name: 'submit',
						label: this._('Join'),
						callback: function() {
							deferred.resolve({
								username: form.getWidget('username').get('value'),
								password: form.getWidget('password').get('value')
							});
							dialog.hide();
							dialog.destroyRecursive();
							form.destroyRecursive();
						}
					}, {
						name: 'cancel',
						label: this._('Cancel'),
						callback: dojo.hitch(this, function() {
							deferred.reject();
							this.standby(false);
							dialog.hide();
							dialog.destroyRecursive();
							form.destroyRecursive();
						})
					}],
					layout: [ 'text', 'username', 'password' ]
				});
				dialog = new dijit.Dialog({
					title: this._('Account data'),
					content: form,
					style: 'max-width: 400px;'
				});
				this.connect(dialog, 'onHide', function() {
					if (deferred.fired < 0) {
						// user clicked the close button
						this.standby(false);
						deferred.reject();
					}
				});
				dialog.show();
				return deferred;
			});

			// confirmation message for the master
			var _confirmMaster = dojo.hitch(this, function() {
				var msg = '<p>' + this._('The specified settings will be applied to the system. This may take some time. Please confirm to proceed.') + '</p>';
				return umc.dialog.confirm(msg, [{
					name: 'cancel',
					'default': true,
					label: this._('Cancel')
				}, {
					name: 'apply',
					label: this._('Apply changes')
				}]).then(dojo.hitch(this, function(response) {
					if ('apply' != response) {
						// throw new error to indicate that action has been canceled
						throw new umc.widgets._setup.CancelDialogException();
					}
				}));
			});

			// function to save data
			var _save = dojo.hitch(this, function(username, password) {
				// send save command to server
				this.standby(true);
				return this.umcpCommand('setup/save', { 
					values: values,
					username: username || null,
					password: password || null
				}).then(dojo.hitch(this, function() {
					// poll whether script has finished
					return this.umcpCommand('setup/finished', {}, undefined, undefined, {
						// long polling options
						messageInterval: 30,
						message: this._('The connection to the server could not be established after {time} seconds. This problem can occur due to a change of the IP address. In this case, please login to Univention Management Console again at the new address.')
					});
				}));
			});

			// notify user that saving was successfull
			var _success = dojo.hitch(this, function() {
				umc.dialog.notify(this._('The changes have been applied successfully.'));
				this.load(); // sets 'standby(false)'
			});

			// show the correct dialogs
			var deferred = null;
			if (joined || role == 'basesystem') {
				// normal setup scenario, confirm changes and then save
				deferred = _confirmChanges().then(function() {
					return _save();
				});
			}
			else if (role != 'domaincontroller_master') {
				// unjoined system scenario and not master
				// we need a proper DC administrator account
				deferred = _password().then(function(opt) {
					return _save(opt.username, opt.password);
				});
			}
			else {
				// unjoined master
				deferred = _confirmMaster().then(function() {
					return _save();
				});
			}

			// in appliance mode, notify that the boot process will continue
			if (applianceMode) {
				deferred = deferred.then(function() {
					return _shutDownBrowser(this._('Please confirm to continue with the boot process.'));
				});
			}
			else {
				deferred = deferred.then(function() {
					return _success();
				});
			}

			// error case, turn off standby animation
			deferred.then(function() {}, dojo.hitch(this, function() {
				this.standby(false);
			}));
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	}

});

