/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define,console */

define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, domClass, _WidgetBase, _TemplatedMixin) {
	return declare("umc.widgets.Text", [_WidgetBase, _TemplatedMixin], {
		// summary:
		//		Simple widget that displays a given label, e.g., some text to
		//		be rendered in a form. Can also render HTML code.

		templateString: '<div dojoAttachPoint="contentNode">${content}</div>',

		labelPosition: 'top',

		// content: String
		//		String which contains the text (or HTML code) to be rendered.
		content: '',

		_tmpContent: null,

		// the widget's class name as CSS class
		baseClass: 'umcText',

		postMixInProperties: function() {
			this.inherited(arguments);
			// We need to temporary unset 'content'. See bug #28810 or #25635
			this._tmpContent = this.content;
			this.content = '';
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.set('content', this._tmpContent);
		},

		_setContentAttr: function(content) {
			this.contentNode.innerHTML = content;
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
