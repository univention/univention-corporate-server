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
/*global define console*/

define([
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/cache",
	"dojo/json",
	"dojox/string/sprintf",
	"umc/dialog",
	"umc/i18n!umc/app"
], function(lang, dojo, cache, json, sprintf, dialog, _) {
	return function() {
		var path = sprintf('help/%s.json', dojo.locale.slice( 0, 2 ).toLowerCase());
		var keys = {};
		try {
			keys = json.parse(cache('umc', path));
		} catch(e) {
			try {
				keys = json.parse(cache('umc', 'help/en.json'));
			} catch(e2) {
				console.error("HelpPage: help/en.json is missing or malformed");
			}
		}

		dialog.templateDialog( "umc", "help/template.html", keys, _( 'Help' ), _( 'Close' ) );
	};
});
