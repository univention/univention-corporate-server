/** TODO: Univention header **/
dojo.provide("umc.modules._luga.PasswordInputBox");
dojo.require("umc.widgets.PasswordInputBox");

dojo.declare("umc.modules._luga.PasswordInputBox", [umc.widgets.PasswordInputBox], {
	setDisabledAttr: function(newVal) {
		this._firstWidget.set('disabled', newVal);
		this._secondWidget.set('disabled', newVal);
	}
});
