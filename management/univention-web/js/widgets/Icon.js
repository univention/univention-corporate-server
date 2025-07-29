/*
 * SPDX-FileCopyrightText: 2020-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
