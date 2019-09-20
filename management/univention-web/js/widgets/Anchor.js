/*
 * Copyright 2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, lang, domClass, entities, _WidgetBase, _TemplatedMixin) {
	return declare("umc.widgets.Anchor", [_WidgetBase, _TemplatedMixin], {
		// summary:
		//		Simple widget that displays a link.

		templateString: '<a href="${href}" title="${title}" dojoAttachPoint="contentNode">${content}</a>',

		labelPosition: 'top',

		// content: String
		//		String which contains the text (or HTML code) to be rendered.
		content: '',

		title: '',
		href: '#',

		// the widget's class name as CSS class
		baseClass: 'umcText',

		postCreate: function() {
			this.inherited(arguments);

			if (typeof this.callback === "function") {
				this.on('click', lang.hitch(this, 'callback'));
			}
		},

		_setContentAttr: function(content) {
			this.contentNode.innerHTML = entities.encode(content);
			this._set('content', content);
		},

		_setVisibleAttr: function(visible) {
			this._set('visible', visible);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !visible);
		},

		isValid: function() {
			// text is always valid
			return true;
		}
	});
});
