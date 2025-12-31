/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
