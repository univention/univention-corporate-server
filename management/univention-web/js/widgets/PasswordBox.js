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
	"dojo/dom-class",
	"dojo/on",
	"dijit/form/ToggleButton",
	"umc/widgets/TextBox",
	"umc/widgets/_FormWidgetMixin",
	"put-selector/put"
], function(declare, lang, domClass, on, ToggleButton, TextBox, _FormWidgetMixin, put) {
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
					iconClass: 'umcEyeIcon',
					'class': 'umcPasswordBox__revealToggle umcFlatButton umcIconButton--aligned-to-textfield',
					tabindex: '-1'
				});
				revealToggle.placeAt(this, 'first');
				on(revealToggle, 'change', lang.hitch(this, function(checked) {
					revealToggle.set('iconClass', checked ? 'umcEyeCrossedOutIcon' : 'umcEyeIcon');
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
			this.focusCatchNode = put('input.dijitInputInner[type="password"][tabIndex="-1"][style="position: absolute; opacity: 0;"]');
			on(this.focusCatchNode, 'focus', lang.hitch(this, 'focus'));
			put(this.focusNode, '-', this.focusCatchNode);
		}
	});
});
