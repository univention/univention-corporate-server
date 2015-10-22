/*
 * Copyright 2013-2015 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"put-selector/put",
	"dojo/dom-class",
	"umc/tools",
	"umc/widgets/GalleryPane",
	"dojo/query",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, put, domClass, tools, GalleryPane, query, domGeometry, domStyle, _) {
	return declare("umc.modules.appcenter.AppCenterGallery", [ GalleryPane ], {
		region: 'main',

		baseClass: 'umcGalleryPane umcAppCenterGallery',

		bootstrapClasses: "",

		getIconClass: function(item, suffix) {
			suffix = suffix || '';
			return tools.getIconClass('apps-' + item.id + suffix, 'scalable', 'umcAppCenter');
		},

		renderRow: function(item) {
			var appWrapperDiv = put(lang.replace('div.umcGalleryWrapperItem.{bootstrapClasses}[moduleID={moduleID}]', {
				moduleID: item.id,
				bootstrapClasses: this.bootstrapClasses
			}));
			var innerWrapper = put(appWrapperDiv, 'div.appInnerWrapper.umcGalleryItem');

			put(innerWrapper, 'div.border');

			var iconClass = this.getIconClass(item);
			if (iconClass) {
				put(innerWrapper, 'div.appIcon.umcGalleryIcon.' + iconClass);
			}

			var text = put(innerWrapper, 'div.appContent');
			put(text, 'div.umcGalleryName', this.getItemName(item));
			put(text, 'div.umcGalleryVendor', item.vendor || item.maintainer || '');

			var hover = put(innerWrapper, 'div.appHover');
			if (item.description) {
				put(hover, 'div', item.description);
			}

			innerWrapper.onmouseover = function() {
				domClass.toggle(innerWrapper, 'hover');
			};
			innerWrapper.onmouseout = function() {
				domClass.toggle(innerWrapper, 'hover');
			};

			return appWrapperDiv;
		},

		_resizeItemNames: function() {
			query('.umcGalleryName', this.contentNode).forEach(lang.hitch(this, function(inode) {
				var fontSize = 1.4;
				while (domGeometry.position(inode).h > 40) {
					domStyle.set(inode, 'font-size', fontSize + 'em');
					fontSize *= 0.95;
				}
			}));
		},

		getStatusIconClass: function(item) {
			var iconClass = '';
			if (item.endoflife) {
				iconClass = 'umcErrorIcon';
			} else if (item.is_installed && item.candidate_version) {
				iconClass = 'umcUpdateIcon';
			}
			if (item.installations) {
				tools.forIn(item.installations, function(server, info) {
					if (info.version && ((item.candidate_version || item.version) != info.version)) {
						iconClass = 'umcUpdateIcon';
						return false;
					}
				});
			}
			return iconClass;
		}
	});
});
