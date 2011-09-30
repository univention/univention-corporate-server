/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.DetailPage");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.NumberSpinner");

dojo.declare("umc.modules._quota.DetailPage", [ umc.widgets.Page, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.quota',
	_form: null,

	buildRendering: function() {
		this.inherited(arguments);
		this.renderForm();

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Quota settings')
		});
		this.addChild(titlePane);
		titlePane.addChild(this._form);
	},

	postCreate: function() {
		this.inherited(arguments);
		this.startup();
	},

	renderForm: function() {
		var widgets = [{
			type: 'TextBox',
			name: 'user',
			value: this._('User')
		}, {
			type: 'TextBox',
			name: 'partitionDevice',
			value: this._('Partition')
		}, {
			type: 'Text',
			name: 'sizeLimitSoftText',
			content: this._('Data size soft limit')
		}, {
			type: 'NumberSpinner',
			name: 'sizeLimitSoftSpinner',
			value: 0,
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}, {
			type: 'Text',
			name: 'sizeLimitHardText',
			content: this._('Data size hard limit')
		}, {
			type: 'NumberSpinner',
			name: 'sizeLimitHardSpinner',
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}, {
			type: 'Text',
			name: 'fileLimitSoftText',
			content: this._('Files soft limit')
		}, {
			type: 'NumberSpinner',
			name: 'fileLimitSoftSpinner',
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}, {
			type: 'Text',
			name: 'fileLimitHardText',
			content: this._('Files hard limit')
		}, {
			type: 'NumberSpinner',
			name: 'fileLimitHardSpinner',
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}];

		var buttons = [{
			name: 'set',
			label: this._('Set'),
			callback: dojo.hitch(this, 'onClosePage')
		}, {
			name: 'cancel',
			label: this._('Cancel'),
			callback: dojo.hitch(this, 'onClosePage')
		}];

		var layout = [['user', 'partitionDevice'], ['sizeLimitSoftText', 'sizeLimitHardText'], ['sizeLimitSoftSpinner', 'sizeLimitHardSpinner'], ['fileLimitSoftText', 'fileLimitHardText'], ['fileLimitSoftSpinner', 'fileLimitHardSpinner'], ['set', 'cancel']];

		this._form = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});
	},

	onClosePage: function() {
		return true;
	},

	init: function(data) {
		console.log(data);
		this._form.getWidget('partitionDevice').setValue(data.partitionDevice);
		this._form.getWidget('partitionDevice').set('disabled', true);
		if (data.userData) {
			this._form.getWidget('user').setValue(data.userData[0].user);
			this._form.getWidget('user').set('disabled', true);
			this._form.getWidget('sizeLimitSoftSpinner').setValue(data.userData[0].sizeLimitSoft);
			this._form.getWidget('sizeLimitHardSpinner').setValue(data.userData[0].sizeLimitHard);
			this._form.getWidget('fileLimitSoftSpinner').setValue(data.userData[0].fileLimitSoft);
			this._form.getWidget('fileLimitHardSpinner').setValue(data.userData[0].fileLimitHard);
		}
		else {
			this._form.getWidget('user').setValue('');
			this._form.getWidget('user').set('disabled', false);
			this._form.getWidget('sizeLimitSoftSpinner').setValue('0');
			this._form.getWidget('sizeLimitHardSpinner').setValue('0');
			this._form.getWidget('fileLimitSoftSpinner').setValue('0');
			this._form.getWidget('fileLimitHardSpinner').setValue('0');
		}
	}
});