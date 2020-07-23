/* global getQuery*/
var umcConfig = {
	autoLogin: false,
	deps: [
		"dojo/query",
		"login",
		"login/dialog",
		"umc/tools",
		"umc/i18n/tools",
		"umc/json!/univention/login/meta.json",
		"umc/i18n!login",
		"dojo/NodeList-html"
	],
	callback: function(query, login, dialog, tools, i18nTools, meta, _) {
		var _getText = function(name, fallback) {
			var loginTexts = meta.login_texts || {};
			var locale = i18nTools.defaultLang().substring(0, 2);

			var text = loginTexts[name + '/' + locale];
			text = text || loginTexts[name];
			text = text || fallback;
			text = text || '';
			return text;
		};

		query('h1').html(_getText('title', _('Login at %(domainname)s', tools.status())));
		tools.status('username', getQuery('username') || tools.status('username'));
		tools.status('password', getQuery('password'));
		login.renderLoginDialog();
		dialog.renderLoginDialog();
	}
};
