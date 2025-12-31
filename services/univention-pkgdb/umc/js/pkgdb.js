/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/modules/pkgdb/Page",
	"umc/widgets/TabbedModule",
	"umc/widgets/StandbyMixin",
	"umc/i18n!umc/modules/pkgdb"
], function(declare, lang, Page, TabbedModule, StandbyMixin, _) {
	return declare("umc.modules.pkgdb", [ TabbedModule, StandbyMixin ], {

		pageClass: 'umcPKGDBPage',

		buildRendering: function() {
			this.inherited(arguments);

			// trigger a reload of initial values on every module opening, even if the module process already exists
			this.umcpCommand('pkgdb/reinit');

			var syspage = new Page({
				title: _("Search UCS systems"),
				pageKey: 'systems',
				standbyDuring: lang.hitch(this, this.standbyDuring)
			});
			this.addTab(syspage);

			var packpage = new Page({
				title: _("Search software packages"),
				pageKey: 'packages',
				standbyDuring: lang.hitch(this, this.standbyDuring)
			});
			this.addTab(packpage);
		}
	});
});
