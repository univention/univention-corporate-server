/*
 * SPDX-FileCopyrightText: 2013-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"umc/tools",
], function(tools) {
	return {
		traceback: function(traceback, feedbackLink) {
			return tools.sendTraceback(traceback, feedbackLink);
		}
	};
});
