/**
SPDX-FileCopyrightText: 2019-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
**/

var profile = {
	resourceTags: {
		miniExclude: function(filename, mid) {
			if(mid === "dompurify/purify") { return true; }
			return false;
		},

		amd: function(filename, mid) {
			if(mid === "dompurify/purify") { return true; } // marks UMD as AMD
			return /\.js$/.test(filename);
		}
	}
};
