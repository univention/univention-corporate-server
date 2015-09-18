var _callback = dojoConfig.callback;
dojoConfig.callback = function() {
	try {
		_callback();
	} catch(err) {};
	require(["passwordreset/passwordreset", "dojo/domReady!"], function(passwordreset) {
		passwordreset.start();
	});
}
