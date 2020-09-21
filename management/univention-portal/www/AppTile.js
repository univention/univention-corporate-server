/*
 * Copyright 2020 Univention GmbH
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
	"dojo/dom-style",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, domClass, domStyle, _WidgetBase, _TemplatedMixin) {
	return declare('AppTile', [_WidgetBase, _TemplatedMixin], {
		templateString: `
			<div class="tile app">
				<div
					class="tile__box"
					data-dojo-attach-point="backgroundNode"
				>
					<img 
						class="tile__logo"
						src=""
						data-dojo-attach-point="logoNode"
					>
				</div>
				<span class="tile__name" data-dojo-attach-point="displayNameNode"></span>
			</div>
		`,

		currentPageClass: null,
		_setCurrentPageClassAttr: function(page) {
			// domClass.toggle(this.wrapperNode, 'hover', page === 'description');
			// domClass.replace(this.domNode, page, this.currentPageClass);
			this._set('currentPageClass', page);
		},

		icon: null,
		_setIconAttr: function(icon) {
			this.logoNode.src = icon;
			// domClass.toggle(this.iconNode, 'iconLoaded', iconUri);
			this._set('icon', icon);
		},

		displayName: null,
		_setDisplayNameAttr: function(displayName) {
			// this.set('displayNameClass', displayName ? 'hasName': null);
			this.displayNameNode.innerHTML = displayName;
			this._set('displayName', displayName);
		},
		displayNameClass: null,
		// _setDisplayNameClassAttr: { node: 'displayNameWrapperNode', type: 'class' },

		backgroundColor: '',
		_setBackgroundColorAttr: function(backgroundColor) {
			domStyle.set(this.backgroundNode, 'background', backgroundColor);
			this._set('backgroundColor', backgroundColor);
		},
	});
});

