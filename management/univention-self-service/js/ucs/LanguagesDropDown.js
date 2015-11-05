/*
 * Copyright 2015 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/array",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/io-query", 
	"dijit/MenuItem",
	"dijit/DropDownMenu",
	"dijit/form/DropDownButton",
	"./text!/univention-self-service/languages.json",
	"./i18n!."
], function(array, dom, domConstruct, ioQuery, MenuItem, DropDownMenu, DropDownButton, _availableLocales, _) {

	return {
		_availableLocales: _availableLocales,

		_getAvailableLocales: function() {
			if ('availableLocales' in window) {
				return availableLocales;
			}
			return this._availableLocales;
		},

		_hasLanguagesDropDown: function() {
			return dom.byId('dropDownButton');
		},

		createLanguagesDropDown: function() {
			//if (!this._hasLanguagesDropDown()) {
			//	return;
			//}
			var _languagesMenu = new DropDownMenu({ style: "display: none;"});
			array.forEach(this._getAvailableLocales(), function(ilocale) {
				var newMenuItem = new MenuItem ({
					label: ilocale.label,
					id: ilocale.id,
					onClick: function() {
						if (ilocale.href) {
							// full href link is given... go to this URL
							window.location.href = ilocale.href;
							return;
						}

						// adjust query string parameter and reload page
						var queryObj = {};
						var queryString = window.location.search;
						if (queryString.length) {
							// cut off the '?' character
							queryObj = ioQuery.queryToObject(queryString.substring(1));
						}
						queryKey = ilocale.queryKey || 'lang';
						queryObj[queryKey] = ilocale.id;
						queryString = ioQuery.objectToQuery(queryObj);
						window.location.search = '?' + queryString;
					}
				});
				_languagesMenu.addChild(newMenuItem);
			});
			var _toggleButton = new DropDownButton({
				label: _("Language"),
				name: "languages",
				dropDown: _languagesMenu,
				id: "languagesDropDown"
			});
			domConstruct.place(_toggleButton.domNode, 'dropDownButton');
		},

		start: function() {
			this.createLanguagesDropDown();		
		}
	};
});
