//
// Univention App Appliance
//   Tool for rendering a CSS background value into an image file
//
// Copyright 2016-2019 Univention GmbH
//
// https://www.univention.de/
//
// All rights reserved.
//
// The source code of this program is made available
// under the terms of the GNU Affero General Public License version 3
// (GNU AGPL V3) as published by the Free Software Foundation.
//
// Binary versions of this program provided by Univention to you as
// well as other copyrighted, protected or trademarked materials like
// Logos, graphics, fonts, specific documentations and configurations,
// cryptographic keys etc. are subject to a license agreement between
// you and Univention and not subject to the GNU AGPL V3.
//
// In the case you use this program under the terms of the GNU AGPL V3,
// the program is provided in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public
// License with the Debian GNU/Linux or Univention distribution in file
// /usr/share/common-licenses/AGPL-3; if not, see
// <https://www.gnu.org/licenses/>.

var system = require('system');
if (system.args.length <= 2) {
	console.log('usage: render-css-background [<width>x<height>] <cssBackgroundValue> <outImage>');
	phantom.exit();
}

// read in arguments
var resolution = '800x600';
var i = 1;
if (system.args.length >= 4) {
	// resolution is given for the image
	resolution = system.args[i++];
}
var cssBackground = system.args[i++];
var outImage = system.args[i++];

// pares image resolution argument
var matchResolutionArg = resolution.match(/^(\d+)x(\d+)$/);
if (!matchResolutionArg) {
	console.log('ERROR: incorrect format for the image width/height.');
	phantom.exit();
}
var width = parseInt(matchResolutionArg[1], 10);
var height = parseInt(matchResolutionArg[2], 10);

// render HTML page with specified css background
var page = require('webpage').create();
page.viewportSize = {
	width: width,
	height: height
};
page.content = '<html><body style="background:' + cssBackground + '; width: 100%; height: 100%;"></body></html>';
page.onLoadFinished = function(resp) {
	page.render(outImage);
	phantom.exit();
};
