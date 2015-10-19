var _callback = dojoConfig.callback;
dojoConfig.callback = function() {
	try {
		_callback();
	} catch(err) {};
	require(["setpassword/setpassword", "dojo/domReady!"], function(setpassword) {
		setpassword.start();
	});
}
