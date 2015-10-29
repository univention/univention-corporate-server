// get locale from query string
locale = getQuery('lang');
if (locale) {
	locale = locale.replace('_', '-');
}

// load the javascript module that is specified in the hash
selfService = document.location.hash.substr(1)

var dojoConfig = {
	isDebug: false,
	locale: locale,
	async: true,
	callback: function() {
		require(["ucs/" + selfService, "dojo/domReady!"], function(app) {
			app.start();
		});
	}
};
