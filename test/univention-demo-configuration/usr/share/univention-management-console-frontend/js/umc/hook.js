define(["dojo/dom", "dojo/dom-attr", "umc/dialog/LoginDialog", "dojo/_base/lang"], function (dom,  attr, LoginDialog, lang) {
	var _fillLoginForm = function () {
		var node = dom.byId("umcLoginPassword");
		attr.set(node, 'value', 'univention');
		node = dom.byId('umcLoginUsername');
		attr.set(node, 'value', 'Administrator');
	}

	lang.extend(LoginDialog, {
		_resetFormOld: lang.clone(LoginDialog.prototype._resetForm),
		_resetForm: function() {
			this._resetFormOld();
			_fillLoginForm();
		}
	});
});
