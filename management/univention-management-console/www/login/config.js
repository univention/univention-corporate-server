/* global getQuery*/
var umcConfig = {
	deps: [
		"dojo/query",
		"login/dialog",
		"umc/tools",
		"umc/json!/univention/meta.json",
		"umc/i18n!login/main",
		"dojo/NodeList-html"
	],
	callback: function(query, dialog, tools, metaData, _) {
		query('h1').html(_('Login at %(domainname)s', metaData));
		tools.status('username', getQuery('username') || tools.getCookies().username);
		tools.status('password', getQuery('password'));
		dialog.renderLoginDialog();
	}
};
