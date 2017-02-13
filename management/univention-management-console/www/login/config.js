/* global dojoConfig,require*/
dojoConfig.callback = function() {
	require(["login/dialog", "dojo/domReady!"], function(dialog) {
		dialog.renderLoginDialog();
	});
};
