function getQuery(/*String*/ param, /*mixed*/ defaultVal) {
	// parse the URI query string
	var query = window.location.search.substring(1);
	var vars = query.split('&');
	for (var i = 0; i < vars.length; i++) {
		// parse the tuple
		var tuple = vars[i].split('=');
		// check whether we found the particular parameter we are interested in
		if (2 == tuple.length && param == tuple[0]) {
			return tuple[1];
		}
	}
}

locale = getQuery('lang');
if (locale) {
	locale = locale.replace('_', '-');
}

var dojoConfig = {
	isDebug: false,
	locale: locale,
	async: true,
	callback: function() {
		require(["ucs/app", "dojo/domReady!"], function(app) {
			app.start();
		});
	}
};
