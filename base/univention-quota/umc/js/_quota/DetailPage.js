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

	_setFormData: function() {
		this._form.getWidget('partitionDevice').setValue(data.partitionDevice);
		this._form.getWidget('partitionDevice').set('disabled', true);
		if (data.userData) {
			this._form.getWidget('user').setValue(data.userData[0].user);
			this._form.getWidget('user').set('disabled', true);
			this._form.getWidget('sizeLimitSoft').setValue(data.userData[0].sizeLimitSoft);
			this._form.getWidget('sizeLimitHard').setValue(data.userData[0].sizeLimitHard);
			this._form.getWidget('fileLimitSoft').setValue(data.userData[0].fileLimitSoft);
			this._form.getWidget('fileLimitHard').setValue(data.userData[0].fileLimitHard);
		}
		else {
			this._form.getWidget('user').setValue('');
			this._form.getWidget('user').set('disabled', false);
			this._form.getWidget('sizeLimitSoft').setValue('0');
			this._form.getWidget('sizeLimitHard').setValue('0');
			this._form.getWidget('fileLimitSoft').setValue('0');
			this._form.getWidget('fileLimitHard').setValue('0');
		}
	},

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
			label: this._('User')
		}, {
			type: 'TextBox',
			name: 'partitionDevice',
			label: this._('Partition')
		}, {
			type: 'NumberSpinner',
			name: 'sizeLimitSoft',
			label: this._('Data size soft limit'),
			value: 0,
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}, {
			type: 'NumberSpinner',
			name: 'sizeLimitHard',
			label: this._('Data size hard limit'),
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}, {
			type: 'NumberSpinner',
			name: 'fileLimitSoft',
			label: this._('Files soft limit'),
			smallDelta: 10,
			largeDelta: 100,
			constraints: {
				min: 0
			}
		}, {
			type: 'NumberSpinner',
			name: 'fileLimitHard',
			label: this._('Files hard limit'),
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

		var layout = [['user', 'partitionDevice'], ['sizeLimitSoft', 'sizeLimitHard'], ['fileLimitSoft', 'fileLimitHard'], ['set', 'cancel']];

		this._form = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});
	},

	onClosePage: function() {
		return true;
	}
});