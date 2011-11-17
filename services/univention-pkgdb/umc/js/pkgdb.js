/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.pkgdb");

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.TabbedModule");

dojo.require("umc.modules._pkgdb.Page");


dojo.declare("umc.modules.pkgdb", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {
	
	i18nClass:		'umc.modules.pkgdb',
	
	buildRendering: function() {
		this.inherited(arguments);
			
		var syspage = new umc.modules._pkgdb.Page({
			title:			this._("Systems"),
			headerText:		this._("Search systems"),
			helpText:		this._("Search for systems with specific software properties"),
			pageKey:		'systems'
		});
		this.addChild(syspage);

		var packpage = new umc.modules._pkgdb.Page({
			title:			this._("Packages"),
			headerText:		this._("Search packages"),
			helpText:		this._("Search for packages with specific software properties"),
			pageKey:		'packages'
		});
		this.addChild(packpage);
		
		var propage = new umc.modules._pkgdb.Page({
			title:			this._("Problems"),
			headerText:		this._("Identify problems"),
			helpText:		this._("Find problems related to software package installation"),
			pageKey:		'problems'
		});
		this.addChild(propage);
		
	}
	
});
