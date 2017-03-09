var umcConfig = {
	deps: [
		"login/dialog",
		"dojo/dom-class"
	],
	callback: function(dialog, domClass) {
		dialog.renderLoginDialog();
		domClass.remove(document.body, 'umcLoginLoading');
	}
};
