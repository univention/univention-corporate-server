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
	"dojo/_base/declare",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, domClass, _WidgetBase, _TemplatedMixin) {
	return declare('Tile', [_WidgetBase, _TemplatedMixin], {
		templateString: '' +
			'<div class="previewTile umcAppGallery col-xs-4" data-dojo-attach-point="domNode">' +
				'<div class="umcGalleryWrapperItem" data-dojo-attach-point="wrapperNode">' +
					'<div class="cornerPiece boxShadow bl">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadow tr">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadowCover bl"></div>' +
					'<div class="appIcon umcGalleryIcon" data-dojo-attach-point="iconNode">' +
						'<img data-dojo-attach-point="imgNode"/>' +
					'</div>' +
					'<div class="appInnerWrapper umcGalleryItem">' +
						'<div class="contentWrapper">' +
							'<div class="appContent">' +
								'<div class="umcGalleryName" data-dojo-attach-point="displayNameWrapperNode">' +
									'<div class="umcGalleryNameContent" data-dojo-attach-point="displayNameNode"></div>' +
								'</div>' +
								'<div class="umcGallerySubName" data-dojo-attach-point="linkNode"></div>' +
							'</div>' +
							'<div class="appHover">' +
								'<div data-dojo-attach-point="descriptionNode"></div>' +
							'</div>' +
						'</div>' +
					'</div>' +
				'</div>' +
			'</div>',

		currentPageClass: null,
		_setCurrentPageClassAttr: function(page) {
			domClass.toggle(this.wrapperNode, 'hover', page === 'description');
			domClass.replace(this.domNode, page, this.currentPageClass);
			this._set('currentPageClass', page);
		},

		icon: null,
		_setIconAttr: function(iconUri) {
			this.imgNode.src = iconUri;
			domClass.toggle(this.iconNode, 'iconLoaded', iconUri);
			this._set('icon', iconUri);
		},

		displayName: null,
		_setDisplayNameAttr: function(displayName) {
			this.set('displayNameClass', displayName ? 'hasName': null);
			this.displayNameNode.innerHTML = displayName;
			this._set('displayName', displayName);
		},
		displayNameClass: null,
		_setDisplayNameClassAttr: { node: 'displayNameWrapperNode', type: 'class' },

		link: null,
		_setLinkAttr: function(link) {
			this.set('linkClass', link ? 'hasLink' : null);
			this.linkNode.innerHTML = link;
			this._set('link', link);
		},
		linkClass: null,
		_setLinkClassAttr: { node: 'linkNode', type: 'class' },

		description: null,
		_setDescriptionAttr: function(description) {
			this.set('descriptionClass', description ? 'hasDescription' : null)	;
			this.descriptionNode.innerHTML = description;
			this._set('description', description);
		},
		descriptionClass: null,
		_setDescriptionClassAttr: { node: 'descriptionNode', type: 'class' }
	});
});
