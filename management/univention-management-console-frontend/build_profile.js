/*
 * Copyright 2011-2014 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
// Dojo build documentation:
//   http://dojotoolkit.org/reference-guide/build/index.html
//   http://dojotoolkit.org/reference-guide/build/buildScript.html
//   http://dojotoolkit.org/documentation/tutorials/1.6/build/

var profile = (function() {
	return {
		//stripConsole : "all",
		basePath : ".",
		releaseDir : "build",
		releaseName : "js",
		action : "release",

		packages:[{
			name: "dojo",
			location: "tmp/dojo"
		}, {
			name: "dijit",
			location: "tmp/dijit"
		}, {
			name: "dojox",
			location: "tmp/dojox"
		}, {
			name: "umc",
			location: "tmp/umc"
		}, {
			name: "dgrid",
			location: "tmp/dgrid"
		}, {
			name: "put-selector",
			location: "tmp/put-selector"
		}, {
			name: "xstyle",
			location: "tmp/xstyle"
		}],

		optimize : "shrinksafe.keepLines",
		//localeList : "de-de,en-us",
		cssOptimize: "comments.keepLines",
		copyTests: false,

		layers: {
			"dojo/dojo": {
				include: [ "dojo/dojo", "umc/app", "umc/widgets", "dgrid" ],
				customBase: true,
				boot: true
			}
		}
	};
})();
