/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.reboot");

dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("dijit.TitlePane");

dojo.declare("umc.modules.reboot", [ umc.widgets.Module, umc.i18n.Mixin ], {

    _page: null,
    _form: null,

	i18nClass: 'umc.modules.reboot',

	buildRendering: function() {
		this.inherited(arguments);

        this._page = new umc.widgets.Page({
            helpText: this._("This module can be used to restart or shut down the system remotely. The optionally given message will be displayed on the console and written to the syslog."),
            headerText: this._("Reboot/shutdown the system")
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
                	umc.dialog.alert(data.result.message);
                }));
			})
		}];

		var layout = [['action'], ['message']];

		this._form = new umc.widgets.Form({
			widgets: widgets,
			buttons: buttons,
			layout: layout,
			cols: 1
		});

        this._page.addChild(new dijit.TitlePane({
			title: this._('Actions'),
			content: this._form
		}));

        this._page.startup();
    }
});
