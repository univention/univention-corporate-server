/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.setup");

dojo.require("dijit.TitlePane");
dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.TitlePane");

dojo.declare("umc.modules.setup", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.setup',

	// pages: String[]
	//		List of all setup-pages that are visible.
	pages: [ 'LanguagePage', 'ServerPage', 'NetworkPage', 'CertificatePage', 'SoftwarePage' ],

	wizard: false,

	_pages: null,

	_orgValues: null,

	buildRendering: function() {
		this.inherited(arguments);

		this.standby(true);

		// each page has the same buttons for saving/resetting
		var buttons = [{
			name: 'submit',
			label: this._('Save'),
			callback: dojo.hitch(this, function() {
				this.save(this.getValues());
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
				footerButtons: buttons,
				onSave: dojo.hitch(this, function() {
					this.save(this.getValues());
				})
			});
			this.addChild(ipage);
			this._pages.push(ipage);
		}, this);

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
		umc.tools.umcpCommand('setup/load').then(dojo.hitch(this, function(data) {
			// update setup pages with loaded values
			this.setValues(data.result);
			this.standby(false);
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	save: function(_values) {
		// only save the true changes
		var values = {};
		var nchanges = 0;
		umc.tools.forIn(_values, function(ikey, ival) {
			if (dojo.toJson(this._orgValues[ikey]) != dojo.toJson(ival)) {
				values[ikey] = ival;
				++nchanges;
			}
		}, this);

		// only submit data to server if there are changes
		if (!nchanges) {
			umc.dialog.alert(this._('No changes have been made.'));
		}
		else {
			this.standby(true);
			umc.tools.umcpCommand('setup/save', { values: values }).then(dojo.hitch(this, function() {
				this.load();
			}), dojo.hitch(this, function() {
				this.standby(false);
			}));
		}
	}
});
