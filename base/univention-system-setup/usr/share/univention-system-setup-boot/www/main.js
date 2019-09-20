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

/*global define*/
define([
	"dojo/_base/declare",
	"dojo/dom",
	"dojox/html/entities",
	"umc/tools",
	"umc/i18n!initialsetup"
], function(declare, dom, entities, tools, _) {
	return {
		start: function() {
			this.initLabels();
		},

		initLabels: function() {
			var title = _("Welcome to UCS initial configuration");
			window.document.title = title;

			var heading = entities.encode(title);
			dom.byId('heading').innerHTML = heading;

			var contentP1 = "<p>" + _("Before starting the setup wizard, an initial password for the <i>root</i> user must be set.") + "</p>";
			var contentP2 = "<p>" +
				_("Connect to this server instance as <i>root</i> via ssh and your selected private ssh key. ") +
				_("Set a password with <i>passwd</i>, e.g., by issuing the following command:") +
				"<pre>" +
					_("ssh -ti &lt;path/to/privatekey&gt; root@%(serveraddress)s passwd", {
						serveraddress: tools.status('serveraddress')
					}) +
				"</pre></p>";
			var contentP3 = "<p>" + _("If a password for <i>root</i> has been set, <a href='/univention/setup/?username=root'>start the setup wizard</a>.") + "</p>";
			var content = contentP1 + contentP2 + contentP3;
			dom.byId('content').innerHTML = content;
		}
	};
});
