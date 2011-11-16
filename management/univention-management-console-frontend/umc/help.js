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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.help");

dojo.require("dojo.cookie");
dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("dojo.cache");

dojo.mixin(umc.help, new umc.i18n.Mixin({
	// use the framework wide translation file
	i18nClass: 'umc.app'
} ), {

	show: function() {
		var introduction = this._( 'Univention Management Console (UMC) is a modularly designed, web-based application to administrate local computers. The application allows the user to control services, check system utilisation, and check or adjust system parameters.  The web-based interface of UMC is described in detail the in current manual of Univention Corporate Server (UCS). Besides the manual, the homepage of Univention provides additional documentation for Univention Corporate Server. These documents assist in different topics like installation or administration.' );

		var lang = dojo.locale.slice( 0, 2 ).toLowerCase();
		var keys = {
			introduction : introduction,
			manual : this._( 'Current manual (PDF)' ),
			add_doc : this._( 'Additional documentation for UCS' ),
			sdb : this._( 'Univention support data base (SDB)' ),
			wiki : this._( 'Univention wiki site' ),
			forum : this._( 'Univention forum' ),
			support : this._( 'Univention support' ),
			supportURL : lang == 'de' ? 'http://www.univention.de/univention/kontakt/kontaktformular/' : 'http://www.univention.de/en/about-univention/contact/',
			titleDoc : this._( 'Manual and documentation' ),
			titleSup : this._( 'Supplementary information' ),
			titleAss : this._( 'Support and assistance' )
		};
		umc.dialog.templateDialog( "umc", "help.html", keys, this._( 'Help' ), this._( 'Close' ) );
	}
} );
