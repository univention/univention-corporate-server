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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/touch",
	"dojo/dom-class",
	"put-selector/put",
	"dijit/TooltipDialog",
	"dijit/popup",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/TextBox",
	"umc/i18n!setup"
], function(declare, lang, array, query, touch, domClass, put, TooltipDialog, popup, Container, Button, TextBox, _) {
	return declare("umc.modules.setup.VirtualKeyboardBox", [ TextBox ], {

		chars: null,
		iconNode: null,
		keyboard: null,

		_renderKeyboard: function() {
			var siblingNode = query('.dijitValidationContainer', this.domNode)[0];
			this.iconNode = put("span.umcKeyboardIcon", {
				title: _('Virtual keyboard')
			});
			touch.press(this.iconNode, lang.hitch(this, function() {
				popup.open({
					parent: this,
					popup: this.keyboard,
					around: this.iconNode,
					orient: ["below-centered"]
				});
			}));
			put(siblingNode, '-', this.iconNode);

			var charNodes = put('div.umcKeyboardRow', {
				innerHTML: _("Please click on the required character.")
			});
			var keyContainer = put(charNodes, 'div.umcKeyContainer');
			array.forEach(this.chars, lang.hitch(this, function(ichar, idx) {
				var key = new Button({
					label: ichar,
					'class' : 'umcKeyboardKey',
					onClick: lang.hitch(this, function() {
						var oldVal = this.get('value');
						var newVal = oldVal + ichar;
						this.set('value', newVal);
					})
				});
				put(keyContainer, key.domNode);
			}));
			this.keyboard = new TooltipDialog({
				content: charNodes
			});
			var _focusHandler = lang.hitch(this, function(name, oldVal, newVal) {
				var isKeyboardVisible = this.keyboard.domNode.offsetParent;
				if (!newVal && isKeyboardVisible) {
					popup.close(this.keyboard);
				}
			});
			this.keyboard.watch('focused', _focusHandler);
			this.watch('focused', _focusHandler);
		},

		buildRendering: function() {
			this.inherited(arguments);
			if (this.chars) {
				this._renderKeyboard();
			}
		}
	});
});


