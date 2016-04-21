/*
 * Copyright 2013-2016 Univention GmbH
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
	"dojo/_base/kernel",
	"dojo/_base/event",
	"dojox/html/entities",
	"put-selector/put",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/on",
	"umc/tools",
	"umc/widgets/GalleryPane",
	"dijit/Tooltip",
	"dojo/query",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, lang, kernel, dojoEvent, entities, put, domClass, domConstruct, on, tools, GalleryPane, Tooltip, query, domGeometry, domStyle, _) {
	return declare("umc.modules.appcenter.AppCenterGallery", [ GalleryPane ], {
		region: 'main',

		baseClass: 'umcGalleryPane umcAppCenterGallery',

		bootstrapClasses: "",

		getIconClass: function(iconName) {
			return tools.getIconClass(iconName, 'scalable', 'umcAppCenter');
		},

		getIconUrl: function(iconName) {
			return lang.replace('{url}/umc/icons/scalable/{icon}', {
				url: require.toUrl('dijit/themes'),
				icon: iconName || ''
			});
		},

		renderRow: function(item) {
			var appWrapperDiv = put(lang.replace('div.umcGalleryWrapperItem.{bootstrapClasses}[moduleID={moduleID}]', {
				moduleID: item.id,
				bootstrapClasses: this.bootstrapClasses
			}));
			var innerWrapper = put(appWrapperDiv, lang.replace('div[id={0}].appInnerWrapper.umcGalleryItem', [item.id]));

			put(innerWrapper, 'div.border');

			var iconClass = this.getIconClass(item.logo_name);
			if (iconClass) {
				put(innerWrapper, 'div.appIcon.umcGalleryIcon.' + iconClass);

				//IE specific
				//on IE some svgs are not shown. this fixes the problem
				if (navigator.userAgent.indexOf('Trident/') !== -1) {
					var iconUrl = this.getIconUrl(item.logo_name);
					domConstruct.create('img', {
						src: iconUrl
					});
				}
			}

			var text = put(innerWrapper, 'div.appContent');
			put(text, 'div.umcGalleryName', this.getItemName(item));
			put(text, 'div.umcGalleryVendor', this.getMore(item));

			var hover = put(innerWrapper, 'div.appHover');
			var description = this.getItemDescription(item);
			if (description) {
				put(hover, 'div', description);
			}

			innerWrapper.onmouseover = function() {
				domClass.toggle(innerWrapper, 'hover');
			};
			innerWrapper.onmouseout = function() {
				domClass.toggle(innerWrapper, 'hover secondTouch');
			};

			var statusIconClass = this.getStatusIconClass(item);
			if (statusIconClass) {
				put(appWrapperDiv, lang.replace('div.appStatusIcon{0}', [statusIconClass]));

				var statusIcon = put(lang.replace('div.appStatusIcon.appStatusHoverIcon{0}', [statusIconClass]));

				var tooltipMessage;
				if (statusIconClass.indexOf("EndOfLife") !== -1) {
					if (item.is_installed) {
						tooltipMessage = _('This application will not get any further updates. We suggest to uninstall %(app)s and search for an alternative application.', {app: entities.encode(item.name)});
					} else {
						tooltipMessage = _("This application will not get any further updates.");
					}
				} else if (statusIconClass.indexOf('Update') !== -1) {
					tooltipMessage = _("Update available");
				}
				on(statusIcon, 'click', function(evt) {
					Tooltip.show(tooltipMessage, statusIcon);
					if (evt) {
						dojoEvent.stop(evt);
					}
					on.once(kernel.body(), 'click', function(evt) {
						Tooltip.hide(statusIcon);
						dojoEvent.stop(evt);
					});
				});
				put(appWrapperDiv, statusIcon);
			}

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

		getMore: function(item) {
			return item.vendor || item.maintainer || '';
		},

		getStatusIconClass: function(item) {
			var iconClass = '';
			if (item.end_of_life) {
				iconClass = '.appEndOfLifeIcon';
			} else if (item.update_available) {
				iconClass = '.appUpdateIcon';
			}
			if (item.installations) {
				tools.forIn(item.installations, function(server, info) {
					if (info.update_available) {
						iconClass = '.appUpdateIcon';
						return false;
					}
				});
			}
			return iconClass;
		}
	});
});
