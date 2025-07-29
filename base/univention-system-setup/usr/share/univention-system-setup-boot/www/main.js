/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
