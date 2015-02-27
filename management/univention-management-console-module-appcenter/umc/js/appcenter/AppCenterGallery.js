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
	"put-selector/put",
	"dojo/dom-class",
	"umc/tools",
	"umc/widgets/GalleryPane"
], function(declare, array, put, domClass, tools, GalleryPane) {
	return declare("umc.modules.appcenter.AppCenterGallery", [ GalleryPane ], {
		region: 'main',

		baseClass: 'umcGalleryPane umcAppCenterGallery',

		style: 'height: 100%; width: 100%;',

		bootstrapClasses: "col-xs-12.col-sm-6.col-md-6.col-lg-6",

		getIconClass: function(item) {
			if (array.indexOf(item.unlocalised_categories, 'UCS components') >= 0) {
				// do not display icon of UCS components
				return tools.getIconClass('appcenter-ucs-component', 50, 'umcAppCenter');
			}
			return tools.getIconClass(item.icon, 50, 'umcAppCenter');
		},

		renderRow: function(item) {
			var div;
			if (item.isSeparator) {
				div = put('div.umcGalleryCategoryHeader.col-xs-12[style=display: block]', item.name);
			} else {
				div = this.inherited(arguments);
				domClass.add(div.firstElementChild, 'umcGalleryCategory-software');
			}
			return div;
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
