/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"umc/widgets/Button"
], function(declare, Button) {
	return declare("umc.widgets.SubmitButton", Button, {
		type: 'submit',

		// defaultButton: Boolean
		//		The submit button will always be rendered as the default button
		defaultButton: true,

		uninitialize: function() {
			// Sometimes after a form is destroyed, there would be tracebacks as a submit
			// event handler would try to access this.node (see dijit/form/_ButtonMixin:_onClick).
			// Therefore, set type to 'button' to avoid these problems
			this.type = 'button';

			this.inherited(arguments);
		}
	});
});
