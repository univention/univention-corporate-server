/* global umcConfig,require,getQuery*/
umcConfig.callback = function() {
	require(["login/dialog", "umc/tools"], function(dialog, tools) {
		tools.status('username', getQuery('username') || tools.getCookies().username);
		tools.status('password', getQuery('password'));
		dialog.renderLoginDialog();
	});
};
