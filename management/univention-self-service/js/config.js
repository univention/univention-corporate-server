/**
* Search the value of the QueryString for an given key.
* @param: {string} key - Key for the searched value.
* @param: {mixed} defaultVal - default value if no value is found.
* */
function getQuery(key, defaultVal) {
	var queryString = window.location.search.substring(1);
	var items = queryString.split('&');
	for (var i = 0; i < items.length; i++) {
		var tuple = items[i].split('=');
		if (2 == tuple.length && key == tuple[0]) {
			return tuple[1];
		}
	}
	return defaultVal;
}


/**
 * Get the current language from the queryString
 * */
function getLocale() {
	var locale = getQuery('lang', 'en-US');
	locale = locale.replace('_', '-');
	return locale;
}


var dojoConfig = {
	isDebug: false,
	locale: getLocale(),
	async: true,
	callback: function() {
		require([
			"ucs/PasswordService",
			"ucs/LanguagesDropDown",
			"dojo/domReady!"
		], function(PasswordService, LanguagesDropDown) {
			PasswordService.start();
			LanguagesDropDown.start();
		});
	}
};
