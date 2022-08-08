/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2022 Univention GmbH
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
	var SVG_SPRITE_PATH = '/univention/js/dijit/themes/umc/images/feather-sprite.svg';
	function getIconNameAndHref(iconNameOrObject) {
		var svgSpritePath = SVG_SPRITE_PATH;
		var iconName = iconNameOrObject;
		if (!!iconNameOrObject && typeof iconNameOrObject !== 'string') {
			svgSpritePath = iconNameOrObject.spritePath || svgSpritePath;
			iconName = iconNameOrObject.iconName;
		}
		return {
			iconName: iconName,
			svgSpritePath: svgSpritePath
		};
	}
	var Icon = declare("umc.widgets.Icon", [_WidgetBase, _TemplatedMixin], {
		_SVG_SPRITE_PATH: SVG_SPRITE_PATH,

		templateString: '' +
			'<svg class="featherIcon dijitDisplayNone" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' +
				'<use ' +
					'data-dojo-attach-point="useNode" ' +
					'xlink:href="${_SVG_SPRITE_PATH}" ' +
				'/>' +
			'</svg>',

		iconName: '',
		_setIconNameAttr: function(iconName) {
			var {iconName, svgSpritePath} = getIconNameAndHref(iconName);
			/* can't use dojo/dom-class here since it does not work for svg elements */
			this.domNode.classList.remove(`icon-${this.iconName}`);
			if (iconName) {
				this.useNode.setAttribute('xlink:href', `${svgSpritePath}#${iconName}`);
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

	Icon.asHTMLString = function(iconName, claz) {
		var {iconName, svgSpritePath} = getIconNameAndHref(iconName);
		return `<svg class="featherIcon icon-${iconName} ${claz || ''}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="${svgSpritePath}#${iconName}"/></svg>`;
	};

	Icon.createNode = function(iconName, claz) {
		// performant rendering of a stateless Icon node
		var {iconName, svgSpritePath} = getIconNameAndHref(iconName);
		var svgNode = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
		var className = 'featherIcon';
		if (iconName) {
			className += ` icon-${iconName}`;
			svgNode.setAttribute('data-iconName', iconName);
		}
		if (claz) {
			className += ` ${claz}`;
		}
		svgNode.className.baseVal = className;

		var useNode = document.createElementNS('http://www.w3.org/2000/svg', 'use');
		useNode.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', `${svgSpritePath}#${iconName || ''}`);

		svgNode.appendChild(useNode);
		return svgNode;
	};

	Icon.setIconOfNode = function(node, iconName) {
		var {iconName, svgSpritePath} = getIconNameAndHref(iconName);
		var lastIconName = node.getAttribute('data-iconName');
		if (lastIconName) {
			node.classList.remove(`icon-${lastIconName}`);
		}
		if (iconName) {
			node.setAttribute('data-iconName', iconName);
			node.classList.add(`icon-${iconName}`);
		} else {
			node.removeAttribute('data-iconName');
		}
		node.firstChild.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', `${svgSpritePath}#${iconName || ''}`);
	};

	return Icon;
});
