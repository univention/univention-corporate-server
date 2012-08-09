/*
 * Copyright 2011-2012 Univention GmbH
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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.help");

dojo.require("/*REQUIRE:"dojo/cookie"*/ cookie");
dojo.require("umc.i18n");
dojo.require("dialog");
dojo.require("dojo.cache");

/*REQUIRE:"dojo/_base/lang"*/ lang.mixin(umc.help, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
} ), {

	show: function() {
		var introduction = _( 'Univention Management Console (UMC) is the central web-application for comfortable domain and computer administration in Univention Corporate Server (UCS). UMC allows to manage users, groups or computers, to control services, and to check or adjust system settings. The web-based interface of UMC is described in detail in the current manual of Univention Corporate Server (UCS). You can find the manual and further important information at the given links below. ' );

		var lang = dojo.locale.slice( 0, 2 ).toLowerCase();
		var keys = {
			introduction : introduction,
			manual : _( 'Current manual (PDF)' ),
			manualURL : _( 'http://www.univention.de/fileadmin/download/documentation_english/ucs-3.0-manual_en.pdf' ),
			add_doc : _( 'Additional documentation for UCS' ),
			addDocURL : _( 'http://www.univention.de/en/download/documentation/documentation/' ),
			sdb : _( 'Univention support data base (SDB)' ),
			wiki : _( 'Univention Wiki' ),
			forum : _( 'Univention forum' ),
			support : _( 'Univention support' ),
			supportURL : lang == 'de' ? 'http://www.univention.de/univention/kontakt/kontaktformular/' : 'http://www.univention.de/en/about-univention/contact/',
			titleDoc : _( 'Manual and documentation' ),
			titleSup : _( 'Supplementary information' ),
			titleAss : _( 'Support and assistance' )
		};
		dialog.templateDialog( "umc", "help.html", keys, _( 'Help' ), _( 'Close' ) );
	}
} );
