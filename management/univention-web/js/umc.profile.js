/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

var profile = (function() {
	return {
		resourceTags: {
			copyOnly: function(filename, mid) {
				// copy all .html, .css, and .json files
				return (/\.(html|json|png|svg|gif)$/).test(filename) ||
					// ignore the profile file
					mid == 'umc/umc.profile.js' ||
					// ignore all provided hooks
					(/^umc\/hooks\/.*/).test(mid) ||
					// ignore login package
					(/^login\/.*/).test(mid);
			},

			amd: function(filename, mid) {
				return mid != 'umc/umc.profile.js' && (/\.js$/).test(filename);
			}
		}
	};
}());

