/* global umcConfig,require*/
umcConfig.callback = function() {
	require(["login/dialog"], function(dialog) {
		dialog.renderLoginDialog();
	});
};
