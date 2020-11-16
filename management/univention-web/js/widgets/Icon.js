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
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, domClass, _WidgetBase, _TemplatedMixin) {
	return declare("umc.widgets.Icon", [_WidgetBase, _TemplatedMixin], {
		_SVG_SPRITE_PATH: '/univention/js/dijit/themes/umc/images/feather-sprite.svg',

		templateString: '' +
			'<svg class="featherIcon dijitDisplayNone" xmlns="http://www.w3.org/2000/svg">' +
				'<use ' +
					'data-dojo-attach-point="useNode" ' +
					'xlink:href="${_SVG_SPRITE_PATH}" ' +
				'/>' +
			'</svg>',

		iconName: '',
		_setIconNameAttr: function(iconName) {
			/* can't use dojo/dom-class here since it does not work for svg elements */
			this.domNode.classList.remove(`icon-${this.iconName}`);
			if (iconName) {
				this.useNode.setAttribute('xlink:href', `${this._SVG_SPRITE_PATH}#${iconName}`);
				this.domNode.classList.add(`icon-${iconName}`);
				this.domNode.classList.remove('dijitDisplayNone');
			} else {
				this.domNode.classList.add('dijitDisplayNone');
			}
			this._set('iconName', iconName);
		},

		_setClassAttr: function(classes) {
			for (const _class of this.get('class').split(' ').filter(_ => _)) {
				this.domNode.classList.remove(_class);
			}
			for (const _class of classes.split(' ').filter(_ => _)) {
				this.domNode.classList.add(_class);
			}
		}
	});
});
