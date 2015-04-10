var _callback = dojoConfig.callback;
dojoConfig.callback = function() {
	try {
		_callback();
	} catch(err) {};
	require(["welcome/welcome", "dojo/domReady!"], function(welcome) {
		welcome.start();
	});
}
