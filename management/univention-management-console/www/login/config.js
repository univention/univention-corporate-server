/* global getQuery*/
var umcConfig = {
	autoLogin: false,
	deps: [
		"dojo/query",
		"login",
		"login/dialog",
		"umc/tools",
		"umc/json!/univention/meta.json",
		"umc/i18n!login",
		"dojo/NodeList-html"
	],
	callback: function(query, login, dialog, tools, metaData, _) {
		query('h1').html(_('Login at %(domainname)s', metaData));
		tools.status('username', getQuery('username') || tools.getCookies().username);
		tools.status('password', getQuery('password'));
		login.renderLoginDialog();
		dialog.renderLoginDialog();
	}
};
