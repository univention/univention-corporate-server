/*
 * Copyright 2018-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/lang",
	"dojox/html/styles"
], function(lang, styles) {
	return {
		RenderMode: {
			NORMAL: 'normal',
			EDIT: 'edit',
			DND: 'dnd'
		},

		_insertedIconStyles: {},
		_createWithTimeStamp: {},

		getIconClass: function(logoUrl) {
			if (!logoUrl) {
				return '';
			}

			var name = logoUrl.replace(/\.\w*$/, '').replace(/.*\//, '').replace(/[^a-zA-Z0-9]/g, '__');
			var iconClass = lang.replace('umcPortal-{0}', [name]);

			// insert a css style for the logo if none exists yet
			if (!this._insertedIconStyles[iconClass]) {
				var timeStamp = '';
				if (this._createWithTimeStamp[iconClass]) {
					delete this._createWithTimeStamp[iconClass];
					timeStamp = lang.replace('?{0}', [Date.now()]); // circumvent a cached logo being used for the css style
				}
				var selector = lang.replace('.{0}', [iconClass]);
				var declaration = lang.replace('background-image: url("{0}{1}") !important;', [logoUrl, timeStamp]); 
				styles.insertCssRule(selector, declaration);
				this._insertedIconStyles[iconClass] = {
					selector: selector,
					declaration: declaration
				};
			}

			return iconClass;
		},

		requestNewIconClass: function(logoUrl) {
			var iconClass = this.getIconClass(logoUrl);
			var insertedStyle = this._insertedIconStyles[iconClass];
			if (insertedStyle) {
				styles.removeCssRule(insertedStyle.selector, insertedStyle.declaration);
				delete this._insertedIconStyles[iconClass];
				this._createWithTimeStamp[iconClass] = true;
			}
		}
	};
});
