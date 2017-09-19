/*
 * Copyright 2016-2017 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojox/html/entities",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/i18n!umc/modules/logview",
	"xstyle/css!../logview.css"
], function(declare, entities, StandbyMixin, Text, _) {

var TAB = '&#9;';

	return declare("umc.modules.logview.FiletextWidget", [Text, StandbyMixin], {

		placeholder: '',
		_searchResultSeparator: '-'.repeat(10),

		buildRendering: function() {
			this.inherited(arguments);

			this.set('content', this.placeholder);
		},

		setText: function(text, pattern) {
			text = entities.encode(text);
			var lines = text.split('\n');
			text = '';
			for (var i = 0; i < lines.length; i++) {
				var line = lines[i];
				var lineNumber = i + 1;
				if (pattern) {
					// format line numbers returned by grep on server
					lineNumber = parseInt(line);
					if (isNaN(lineNumber)) {
						// handle result block separator '--'
						lineNumber = line;
						line = this._searchResultSeparator;
					} else {
						// split line number plus marker character [:-] from the rest of the line
						while (!isNaN(line.charAt(0))) {
							line = line.substring(1);
						}
						lineNumber += line.charAt(0);
						line = line.substring(1);
						var highlight = '<span class="umc-logview highlight">' + entities.encode(pattern) + '</span>';
						line = line.replace(new RegExp(pattern, 'gi'), highlight);
					}
				}
				lineNumber = '<span class="umc-logview number">' + lineNumber + TAB + '</span>';
				var styleClass = 'line';
				if (i % 2 === 1) {
					styleClass = 'zebra-line';
				}
				text += '<span class="umc-logview ' + styleClass + '">' + lineNumber + line + '</span>';
			}
			text = '<span class="umc-logview text">' + text + '</span>';
			this.set('content', text);
			this.standby(false);
		}
	});
});
