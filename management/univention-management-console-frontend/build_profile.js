// Dojo build documentation: 
//   http://dojotoolkit.org/reference-guide/build/index.html
//   http://dojotoolkit.org/reference-guide/build/buildScript.html
//   http://dojotoolkit.org/documentation/tutorials/1.6/build/

dependencies = {
	//stripConsole : 'all',
	action : 'clean,release',
	optimize : 'shrinksafe.keepLines',
	releaseName : '',
	localeList : 'de-de,en-us',
	cssOptimize: 'comments.keepLines',
	copyTests: false,
	prefixes: [
		["umc", "%CURDIR%/umc"], 
		["dojo", "/usr/share/univention-dojo/dojo"], 
		["dijit", "/usr/share/univention-dojo/dijit"],
		["dojox", "/usr/share/univention-dojo/dojox"]
	], 
	layers: [{
		resourceName:"umc.build",
		name:"../umc/build.js",
		dependencies:[
			"umc.app",
			"umc.widgets"
		],
		//layerDependencies:[]
	}]
}
