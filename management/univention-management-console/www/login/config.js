/* global getQuery*/
var umcConfig = {
	autoLogin: false,
	deps: [
		"dojo/query",
		"login",
		"login/dialog",
		"umc/tools",
		"umc/i18n!login",
		"dojo/NodeList-html"
	],
	callback: function(query, login, dialog, tools, _) {
		query('h1').html(_('Login at %(domainname)s', tools.status()));
		tools.status('username', getQuery('username') || tools.status('username'));
		tools.status('password', getQuery('password'));
		login.renderLoginDialog();
		dialog.renderLoginDialog();
	}
};
