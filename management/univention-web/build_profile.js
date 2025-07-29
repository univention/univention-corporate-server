/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
// Dojo build documentation:
//   http://dojotoolkit.org/reference-guide/build/index.html
//   http://dojotoolkit.org/reference-guide/build/buildScript.html
//   http://dojotoolkit.org/documentation/tutorials/1.6/build/

var profile = (function() {
	return {
		stripConsole : "normal",
		basePath : "./tmp",
		releaseDir : "../build",
		action : "release",

		packages: [
			"dojo",
			"dijit",
			"dojox",
			"umc",
			"dgrid",
			"dstore",
			"put-selector",
			"xstyle",
			"dompurify"
		],

		layerOptimize : "closure",
		optimize : "closure",
		cssOptimize: false, //"comments.keepLines",
		copyTests: false,

		layers: {
			"dojo/dojo": {
				include: [ "dojo/dojo", "umc/_all", "dgrid" ],
				exclude: [ "login/main" ],
				customBase: true,
				boot: true
			},
			"login/main": {
				include: [ "login/main" ],
				discard: true
			}
		}
	};
})();
