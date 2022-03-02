/*
 * Copyright 2021-2022 Univention GmbH
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

/**
 * @module umc/widgets/HeaderButtonCloseOverlay
 */
define([
	"dojo/dom",
	"dojo/dom-class",
	"dojo/on",
	"put-selector/put"
], function(dom, domClass, on, put) {
	const toggleButtons = {};
	return {
		createOverlay: function(sibling) {
			let overlay = dom.byId('headerButtonsCloseOverlay');
			if (!overlay) {
				overlay = put(document.body, 'div#headerButtonsCloseOverlay');
			}
			put(overlay, '+', sibling);
		},

		subscribe: function(toggleButton, name, exception) {
			toggleButtons[name] = toggleButton;
			const bodyClickHandler = on.pausable(dojo.body(), 'click', () => {
				this.state(name, false);
			});
			bodyClickHandler.pause();
			toggleButton.watch('checked', (attr, oldVal, newVal) => {
				if (newVal) {
					bodyClickHandler.resume();
				} else {
					bodyClickHandler.pause();
				}
				this.state(name, newVal);
			});
			on(toggleButton, 'click', evt => {
				// prevent bodyClickHandler from getting the click event when
				// the toggle button is clicked directly
				evt.stopImmediatePropagation();
			});
			if (exception) {
				on(exception, 'click', evt => {
					evt.stopImmediatePropagation();
				});
			}
		},

		state: function(name, checked) {
			const toggleButton = toggleButtons[name];
			if (toggleButton.get('checked') !== checked) {
				toggleButton.set('checked', checked);
			}
			if (checked) {
				for (const _toggleButton of Object.values(toggleButtons)) {
					if (toggleButton !== _toggleButton) {
						_toggleButton.set('checked', false);
					}
				}
			}
			domClass.toggle(document.body, `ucsOverlay--${name}`, checked);
		}
	};
});
