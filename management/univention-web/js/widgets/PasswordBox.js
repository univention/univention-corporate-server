/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-attr",
	"dojo/dom-class",
	"dojo/on",
	"umc/widgets/ToggleButton",
	"umc/widgets/TextBox",
	"umc/widgets/_FormWidgetMixin",
	"put-selector/put"
], function(declare, lang, domAttr, domClass, on, ToggleButton, TextBox, _FormWidgetMixin, put) {
	return declare("umc.widgets.PasswordBox", [ TextBox, _FormWidgetMixin ], {
		type: 'password',
		_setTypeAttr: { node: 'focusNode', type: 'attribute' },

		autocomplete: 'new-password',

		/**
		 * If true a button is shown that toggles whether the password is
		 * shown in cleartext or not.
		 */
		showRevealToggle: false,

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcPasswordBox');

			if (this.showRevealToggle) {
				var revealToggle = new ToggleButton({
					iconClass: 'eye',
					checkedIconClass: 'eye-off',
					'class': 'ucsIconButton umcPasswordBox__toggleButton',
					tabindex: '-1'
				});
				revealToggle.placeAt(this, 'first');
				on(revealToggle, 'change', lang.hitch(this, function(checked) {
					this.set('type', checked ? 'text' : 'password');
				}));
			}

			// HACK / WORKAROUND to prevent autocompletion
			//
			// autocomplete="off" is ignored by some
			// browsers due to https://www.w3.org/TR/html-design-principles/#priority-of-constituencies.
			// and autofill being and desired feature for users.
			// The workaround used in TextBox.js to set a random autocomplete value does not work
			// for type="password" (type="password" always prompts autocomplete)
			//
			// Catch the focus and then pass through to the actual input.
			// Likely that this workaround will be fixed in later chrome versions
			this.focusCatchNode = put('input.dijitInputInner[type="password"][tabIndex="-1"][autocomplete="new-password"][style="position: absolute; top: 0; left: 0; opacity: 0;"]');
			on(this.focusCatchNode, 'focus', lang.hitch(this, 'focus'));
			put(this.focusNode, '-', this.focusCatchNode);

			// firefox adds the autofill dropdown to the input before the password input.
			// add a hidden input to catch that
			put(this.focusCatchNode, '- input.dijitDisplayNone[type="text"]');
		},

		_setDisabledAttr: function(disabled) {
			this.inherited(arguments);
			domAttr.set(this.focusCatchNode, 'disabled', disabled);
		}
	});
});
