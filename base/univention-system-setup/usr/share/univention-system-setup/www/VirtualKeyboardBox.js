/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
		keyboard: null,

		_renderKeyboard: function() {
			var siblingNode = query('.umcTextBox__validationIcon', this.domNode)[0];
			var iconNode = put("span.umcKeyboardIcon", {
				title: _('Virtual keyboard')
			});
			touch.press(iconNode, lang.hitch(this, function() {
				popup.open({
					parent: this,
					popup: this.keyboard,
					around: iconNode,
					orient: ["below-centered"]
				});
			}));
			put(siblingNode, '-', iconNode);

			var charNodes = put('div.umcKeyboardRow', {
				innerHTML: _("Please click on the required character.")
			});
			var keyContainer = put(charNodes, 'div.umcKeyContainer');
			array.forEach(this.chars, lang.hitch(this, function(ichar, idx) {
				var key = new Button({
					label: ichar,
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


