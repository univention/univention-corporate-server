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

dojo.declare("umc.modules.setup", [ umc.widgets.Module, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.setup',

	// pages: String[]
	//		List of all setup-pages that are visible.
	pages: [ 'LanguagePage', 'BasisPage', 'NetworkPage', 'CertificatePage', 'SoftwarePage' ],

	_pages: null,

	_orgValues: null,

	_currentPage: -1,

	buildRendering: function() {
		this.inherited(arguments);

		this.standby(true);

		if (this.moduleFlavor == 'wizard') {
			// wizard mode

			// create all pages dynamically
			this._pages = [];
			dojo.forEach(this.pages, function(iclass, i) {
				// load page class
				var ipath = 'umc.modules._setup.' + iclass;
				dojo['require'](ipath);

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
				var ipage = new dojo.getObject(ipath)({
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
			this.addChild(tabContainer);

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
				var ipage = new dojo.getObject(ipath)({
					umcpCommand: dojo.hitch(this, 'umcpCommand'),
					footerButtons: buttons,
					onSave: dojo.hitch(this, function() {
						this.save();
					})
				});
				tabContainer.addChild(ipage);
				this._pages.push(ipage);
			}, this);
			tabContainer.startup();
		}

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
		this.umcpCommand('setup/load').then(dojo.hitch(this, function(data) {
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

		// only submit data to server if there are changes
		if (!nchanges) {
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

			// first see which message needs to be displayed for the confirmation message
			umc.tools.forIn(values, function(ikey) {
				dojo.forEach(summaries, function(idesc) {
					if (matchesSummary(ikey, idesc)) {
						idesc.showConfirm = true;
					}
				});
			});

			// construct message for confirmation
			var confirmMessage = '<p>' + this._('Changes to system setting may have a severe effect on your system.');
			if (this._orgValues['server/role'] != 'domaincontroller_master') {
				confirmMessage += ' ' + this._('Note that some changes may require a new join into the UCS domain.');
			}
			confirmMessage += '</p><p>' + this._('The following changes will be applied to the system:') + '</p><ul style="max-height:200px; overflow:auto;">';
			
			// collect all summaries to be displayed
			dojo.forEach(summaries, function(idesc) {
				if (idesc.showConfirm) {
					confirmMessage += '<li>' + idesc.description + ': ' + idesc.values + '</li>';
				}
			});
			confirmMessage += '</ul><p>' + this._('Please confirm to apply these changes to the system.') + '</p>';

			umc.dialog.confirm(confirmMessage, [{
				'default': true,
				label: this._('Cancel'),
				callback: dojo.hitch(this, function() {
					this.standby(false);
				})
			}, {
				label: this._('Apply changes'),
				callback: dojo.hitch(this, function() {
					this.standby(true);
					this.umcpCommand('setup/save', { values: values }).then(dojo.hitch(this, function() {
						this.load();
					}), dojo.hitch(this, function() {
						this.standby(false);
					}));
				})
			}]);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	}
});

