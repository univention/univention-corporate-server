/*
 * SPDX-FileCopyrightText: 2017-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/widgets/TextBoxMaxLengthChecker",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, TextBoxMaxLengthChecker, _) {
	return declare(TextBoxMaxLengthChecker, {
		maxLength: 20,
		warningMessage: null,
		warningMessageTemplate: null,

		constructor: function() {
			this.inherited(arguments);

			this.warningMessageTemplate = _('<b>Warning:</b> The user name is longer than {length} characters which makes a login on Windows clients impossible. Please consider shortening the user name.');

			this.warningMessage = lang.replace(this.warningMessageTemplate, {
				'length': this.maxLength
			});
		}
	});
});
