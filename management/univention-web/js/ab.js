/*
 * Copyright 2019 Univention GmbH
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
	"umc/tools"
], function(tools) {
	return {
		load: function(path, require, load, headers) {
			var wantsAlternative = false;
			if (tools.status("abtesting") === true) {
				wantsAlternative = true;
			}
			var paths = path.split(/\s*,\s*/);
			var original = paths[0];
			var alternative = paths[1];
			if (alternative === undefined) {
				var handler = require.on('error', function(err) {
					if (err.message === 'scriptError' && err.info[0] === require.toUrl(original)) {
						load(null);
						handler.remove();
					}
				});
				require([original], function(mod) {
					load(mod);
					handler.remove();
				});
			} else {
				var firstTry = original;
				if (wantsAlternative) {
					firstTry = alternative;
				}
				var handler = require.on('error', function(err) {
					if (err.message === 'scriptError' && err.info[0] === require.toUrl(firstTry)) {
						if (wantsAlternative) {
							require([original], function(mod) {
								load(mod);
							});
						}
						handler.remove();
					}
				});
				require([firstTry], function(mod) {
					load(mod);
					handler.remove();
				});
			}
		}
	};
});

