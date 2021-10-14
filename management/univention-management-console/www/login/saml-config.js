/*global availableLocales*/
var umcConfig = {
	autoLogin: false,
	deps: [
		"login/dialog",
		"dojo/_base/array",
		"dojo/dom-class",
		"umc/tools",
		"umc/i18n/tools"
	],
	callback: function(dialog, array, domClass, tools, i18nTools) {
		tools.status('umcMenu/hideLogin', true);
		tools.status('single_sign_on_links', null);
		tools.status('umc/login/disable-default-login', false);
		dialog.renderLoginDialog();
		domClass.remove(document.body, 'umcLoginLoading');
		i18nTools.availableLanguages = availableLocales;
		i18nTools.setLanguage = function(locale) {
			var localelink = array.filter(availableLocales, function(lang) { return lang.id === locale; })[0].href;
			window.location = localelink;
		};
	}
};
