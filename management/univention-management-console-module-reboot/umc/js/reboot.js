/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.reboot");

dojo.require("umc.app");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");

dojo.declare("umc.modules.reboot", [ umc.widgets.Module, umc.i18n.Mixin ], {

    _page: null,
    _form: null,

	i18nClass: 'umc.modules.reboot',

	buildRendering: function() {
		this.inherited(arguments);

        this._page = new umc.widgets.Page({
            title: this._("Reboot"),
            helptext: this._("System reboot or shutdown")
        });
        this.addChild(this._page);

		var widgets = [{
			type: 'ComboBox',
			name: 'action',
			value: 'reboot',
			label: this._('Action'),
			staticValues: [
				{id: 'reboot', label: this._('Reboot')},
				{id: 'halt', label: this._('Stop')}
			]
		}, {
			type: 'TextBox',
			name: 'message',
			label: this._('Reason for this reboot/shutdown')
		}];

		var buttons = [{
			name: 'submit',
			label: this._('Execute'),
			callback: dojo.hitch(this, function() {
                var vals = this._form.gatherFormValues();
                this.umcpCommand('reboot/reboot', vals).then(dojo.hitch(this, function(data) {
                    umc.app.alert(data.result.message);
                }));
			})
		}];

		var layout = [['action'], ['message']];

		this._form = new umc.widgets.Form({
			style: 'width: 100%',
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			cols: 1
		});

        this._page.addChild(this._form);

        this._page.startup();
    }
});
