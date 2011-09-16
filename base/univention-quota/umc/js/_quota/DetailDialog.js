/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._quota.DetailDialog");

dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.TextBox");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.ContainerWidget");

dojo.declare("umc.modules._quota.DetailDialog", [ dijit.Dialog, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.quota',
	_form: null,

	//TODO
	// force max-width
	//style: 'max-width: 300px;',

	buildRendering: function() {
		this.inherited(arguments);
		this.renderForm();

		var titlePane = new umc.widgets.ExpandingTitlePane({
			title: this._('Add quota setting for a user on partition')
		});
		this.addChild(titlePane);
		titlePane.addChild(this._form);
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
			type: 'TextBox',
			name: 'sizeLimitSoft',
			label: this._('Data size soft limit')
		}, {
			type: 'TextBox',
			name: 'sizeLimitHard',
			label: this._('Data size hard limit')
		}, {
			type: 'TextBox',
			name: 'fileLimitSoft',
			label: this._('Files soft limit')
		}, {
			type: 'TextBox',
			name: 'fileLimitHard',
			label: this._('Files hard limit')
		}];

		var buttons = [{
			name: 'set',
			label: this._('Set'),
			callback: dojo.hitch(this, 'onClose')
		}, {
			name: 'cancel',
			label: this._('Cancel'),
			callback: dojo.hitch(this, 'onClose')
		}];

		var layout = [['user', 'partitionDevice'], ['sizeLimitSoft', 'sizeLimitHard'], ['fileLimitSoft', 'fileLimitHard'], ['set', 'cancel']];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});

		var container = new umc.widgets.ContainerWidget({});
		container.addChild(this._form);
		this.set('content', container);
		this.show();
	},

	onClose: function(options) {
		// event stub
	}
});



