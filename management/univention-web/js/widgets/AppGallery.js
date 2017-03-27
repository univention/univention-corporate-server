/*
 * Copyright 2017 Univention GmbH
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
/*global define, require, navigator*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/event",
	"dojo/_base/kernel",
	"dojo/on",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/query",
	"dojo/mouse",
	"dijit/Tooltip",
	"dojox/html/entities",
	"./GalleryPane",
	"../tools"
], function(declare, lang, dojoEvent, kernel, on, domClass, domConstruct, domGeometry, domStyle, query, mouse, Tooltip, entities, GalleryPane, tools) {
	return declare("umc.widgets.AppGallery", [ GalleryPane ], {
		region: 'main',

		bootstrapClasses: '',

		baseClass: 'umcAppGallery',

		iconClassPrefix: 'umcAppGallery',

		getIconClass: function(iconName) {
			var iconClass = tools.getIconClass(iconName, 'scalable', this.iconClassPrefix);
			if (iconClass) {
				//IE specific
				//on IE some svgs are not shown. this fixes the problem
				if (navigator.userAgent.indexOf('Trident/') !== -1) {
					var iconUrl = this.getIconUrl(item.logo_name);
					domConstruct.create('img', {
						src: iconUrl
					});
				}
			}

			return iconClass;
		},

		getIconUrl: function(iconName) {
			return lang.replace('{url}/umc/icons/scalable/{icon}', {
				url: require.toUrl('dijit/themes'),
				icon: iconName || ''
			});
		},

		renderRow: function(item) {
			var renderInfo = this.getRenderInfo(item);
			return this.getDomForRenderRow(renderInfo);
		},

		getRenderInfo: function(item) {
			var iconClass = item.logo_name ? this.getIconClass(item.logo_name) : '';
			return {
				itemId: item.id,
				iconClass: iconClass,
				itemName: this.getItemName(item),
				itemSubName: this.getMore(item),
				itemHoverContent: this.getItemDescription(item),
				itemStatusIcon: this.getStatusIconClass(item),
				itemStatusTooltipMessage: this.getItemStatusTooltipMessage(item)
			};
		},

		getDomForRenderRow: function(item) {
			var domString = '' +
				'<div class="umcGalleryWrapperItem" moduleID={itemId}>' +
					'<div class="cornerPiece boxShadow bl">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadow tr">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadowCover bl"></div>' +
					'<div class="appIcon umcGalleryIcon {iconClass}"></div>' +
					'<div class="appInnerWrapper umcGalleryItem">' +
						'<div class="contentWrapper">' +
							'<div class="appContent">' +
								'<div class="umcGalleryName">' +
									'<div class="umcGalleryNameContent">{itemName}</div>' +
								'</div>' +
								'<div class="umcGallerySubName">{itemSubName}</div>' +
							'</div>' +
							'<div class="appHover">' +
								'<div>{itemHoverContent}</div>' +
							'</div>' +
						'</div>' +
					'</div>' +
					'<div class="appStatusIcon {itemStatusIcon}"></div>' +
					'<div class="appStatusIcon appStatusHoverIcon {itemStatusIcon}"></div>' +
				'</div>';

			var item2 = {};
			tools.forIn(item, function(key, value) {
				item2[key] = entities.encode(value);
			});
			var domNode = domConstruct.toDom(lang.replace(domString, item2));

			on(domNode, mouse.enter, function() {
				domClass.add(this, 'hover');
			});

			on(domNode, mouse.leave, function() {
				// secondTouch is used in AppCenterMetaCategory
				domClass.remove(this, 'hover secondTouch');
			});

			var statusIcon = query('.appStatusHoverIcon', domNode)[0];
			on(statusIcon, 'click', function(evt) {
				Tooltip.show(entities.encode(item.itemStatusTooltipMessage), statusIcon);
				if (evt) {
					dojoEvent.stop(evt);
				}
				on.once(kernel.body(), 'click', function(evt) {
					Tooltip.hide(statusIcon);
					dojoEvent.stop(evt);
				});
			});

			return domNode;
		},

		_resizeItemNames: function() {
			var defaultValues = this._getDefaultValuesForResize('.umcGalleryName');
			var defaultHeight = defaultValues.height;
			query('.umcGalleryNameContent', this.contentNode).forEach(lang.hitch(this, function(inode) {
				var fontSize = parseInt(defaultValues.fontSize, 10) || 16;
				while (domGeometry.position(inode).h > defaultHeight) {
					fontSize--;
					domStyle.set(inode, 'font-size', fontSize + 'px');
				}
			}));
		},

		_getItemFontSize: function(node, cssClass) {
			var queriedNode = query(cssClass, node)[0];
			return domStyle.get(queriedNode, 'font-size');
		},

		_getDefaultValuesForResize: function(cssClass) {
			// render empty gallery item
			var node = this.renderRow({
				name: '*',
				description: '*'
			});
			domClass.add(node, 'dijitOffScreen');
			domConstruct.place(node, this.contentNode);
			var height = this._getItemHeight(node, cssClass);
			var fontSize = this._getItemFontSize(node, cssClass);
			domConstruct.destroy(node);
			return {
				height: height,
				fontSize: fontSize
			};

		},

		getMore: function(item) {
			return item.vendor || item.maintainer || '';
		},

		getStatusIconClass: function(item) {
			return 'noStatus';
		},

		getItemStatusTooltipMessage: function(item) {
			return '';
		}
	});
});
