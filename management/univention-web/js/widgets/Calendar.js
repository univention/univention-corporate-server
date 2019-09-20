/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dijit/Tooltip",
	"dijit/Calendar",
	"umc/widgets/NumberSpinner",
	"put-selector/put",
	"umc/i18n!"
], function(declare, lang, array, on, Tooltip, Calendar, NumberSpinner, put, _) {
	return declare("umc.widgets.Calendar", [ Calendar ], {
		// string that is shown as tooltip when '?' key is pressed
		tooltipString: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.tooltipString = this._getTooltipString();
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._yearInput = new NumberSpinner({
				// overwrite formatter; we do not want thousands separator (2000 instead of 2.000)
				_formatter: function(value) {
					return value;
				},
				intermediateChanges: true
			});
			put(this.currentYearLabelNode, '+', this._yearInput.domNode, '.currentYearInput');
			put(this.currentYearLabelNode, '!');

			var yearInputKeyDownHandler = on(this._yearInput, 'keyDown', lang.hitch(this, function(evt) {
				if (evt.key === 'Enter') {
					// focus the Calendar when Enter key is pressed in _yearInput to
					// activate the Calendar keyboard navigation
					this.focus();
				}

				var isLeftOrRightKey = (evt.key === 'ArrowLeft' || evt.key === 'Left' || evt.key === 'ArrowRight' || evt.key === 'Right');
				if (isLeftOrRightKey) {
					// we do not want the calendar to pick up the keyevents
					// for the right and left arrow key while typing in the input
					// so we can move the cursor left and right instead of focusing the
					// previous/next date cell
					evt.stopPropagation();
				}

				if (evt.key === 'Tab') {
					// prevent native tab behavior for _yearInput
					evt.preventDefault();
				}
			}));

			var calendarKeyDownHandler = on(this, 'keyDown', lang.hitch(this, function(evt) {
				if (evt.key === 'Tab') {
					// tabbing backwards while _yearInput is focused
					// focuses the date cells again
					if (evt.shiftKey && this._yearInput.focused) {
						evt.preventDefault();
						evt.stopPropagation();
						this._yearInput.focusNode.blur();
						this.focus();
					}

					// tabbing forward while the date cells are focused
					// focuses _yearInput
					if (!evt.shiftKey && !this._yearInput.focused) {
						evt.preventDefault();
						evt.stopPropagation();
						this._yearInput.focusNode.select();
					}
				}

				if (evt.key === '?') {
					this.showTooltip();
				}
			}));

			// update the current focus (which dates are being shown)
			// when the content of _yearInput changes
			var changeHandler = on(this._yearInput, 'change', lang.hitch(this, function(val) {
				// but do not update the focus if _yearInput is not
				// focused - when the navigational buttons in the
				// calendar widget are used to e.g. select the next year
				// the content of _yearInput is updated and this function
				// is called. Since the focus is already set we can ignore
				// this to prevent double calls of set('currentFocus')
				if (!this._yearInput.focused) {
					return;
				}

				if (!this._yearInput.isValid()) {
					return;
				}

				var date = new this.dateClassObj(this.get('currentFocus'));
				date.setFullYear(val || 0); // if the input is empty set the fullYear to 0 to prevent NaN display errors
				// use date.getTime() instead of date directly since copying a date object with a year of e.g. 99
				// in IE11, sets the year to 1999 instead. 
				this.set('currentFocus', date.getTime(), false);
				this._yearInput.focus();
			}));

			// watch the current focus (which dates are being shown) and update _yearInput accordingly
			this._yearInput.set('value', this.currentFocus.getFullYear());
			var watchHandler = this.watch('currentFocus', function() {
				this._yearInput.set('value', this.currentFocus.getFullYear());
			});

			// remove handlers on destroy
			this.own(
				calendarKeyDownHandler,
				yearInputKeyDownHandler,
				changeHandler,
				watchHandler
			);
		},

		_getTooltipString: function() {
			var keysAndActionPairs = [{
						key: '<kbd>&larr;</kbd> , <kbd>&uarr;</kbd> , <kbd>&darr;</kbd> , <kbd>&rarr;</kbd>',
						action: _('Move between date cells')
					}, {
						key: lang.replace('<kbd>{0} &darr;</kbd>', [_('Page')]),
						action: _('Move to same day in next month')
					}, {
						key: lang.replace('<kbd>{0} &uarr;</kbd>', [_('Page')]),
						action: _('Move to same day in previous month')
					}, {
						key: lang.replace('<kbd>Alt</kbd> + <kbd>{0} &darr;</kbd>', [_('Page')]),
						action: _('Move to same day in next year')
					}, {
						key: lang.replace('<kbd>Alt</kbd> + <kbd>{0} &uarr;</kbd>', [_('Page')]),
						action: _('Move to same day in previous year')
					}, {
						key: lang.replace('<kbd>{0}</kbd>', [_('Home')]),
						action: _('Move to first day in month')
					}, {
						key: lang.replace('<kbd>{0}</kbd>', [_('End')]),
						action: _('Move to last day in month')
					}, {
						key: lang.replace('<kbd>{0}</kbd> , <kbd>{1}</kbd>', [_('Space'), _('Enter')]),
						action: _('Select the date')
					}];

			// create beginning of table with header
			var tableDomString = '' +
					'<table class="calendarHotKeysTable">' +
						'<thead>' +
							'<tr>' +
								'<th>{keyHeader}</th>' +
								'<th>{actionHeader}</th>' +
							'</tr>' +
						'</thead>' +
						'<tbody>';
			tableDomString = lang.replace(tableDomString, {
				keyHeader: _('Key'),
				actionHeader: _('Action')
			});

			// fill in key and action pairs
			array.forEach(keysAndActionPairs, function(pair) {
				var string = '' +
						'<tr>' +
							'<td>{key}</td>' +
							'<td>{action}</td>' +
						'</tr>';
				tableDomString += lang.replace(string, {
					key: pair.key,
					action: pair.action
				});
			});

			// close table
			tableDomString += '</tbody></table>';

			return tableDomString;
		},

		showTooltip: function() {
			Tooltip.show(this.tooltipString, this.domNode);
		},

		hideTooltip: function() {
			Tooltip.hide(this.domNode);
		}
	});
});

