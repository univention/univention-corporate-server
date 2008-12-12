dependencies = {
	layers: [
		{
			name: "../dijit/dijit.js",
			dependencies: [
				"dijit.dijit"
			]
		},
		{
			name: "../dijit/dijit-all.js",
			layerDependencies: [
				"../dijit/dijit.js"
			],
			dependencies: [
				"dijit.dijit-all"
			]
		},
		{
			name: "../dojox/off/offline.js",
			layerDependencies: [
			],
			dependencies: [
				"dojox.off.offline"
			]
		},
		{
			name: "../unijit/unijit.js", // copyrightFile: "../unijit/Copyright",
			layerDependencies: [
			],
			dependencies: [
				"unijit.form.DateWidget" // "dojo.cldr.nls.gregorian"
			]
		}
	],

	prefixes: [
		[ "dijit", "../dijit" ],
		[ "dojox", "../dojox" ],
		[ "unijit", "../../unijit" ]
	]
}
